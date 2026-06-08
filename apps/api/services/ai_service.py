"""Provider-agnostic AI layer (LangChain).

CLAUDE.md / docs/ARCHITECTURE.md: routes must NEVER call an AI SDK directly — they
go through ``AIService``. We use LangChain's ``init_chat_model`` so the model and
provider are pure configuration: swap ``AI_MODEL`` / ``AI_MODEL_PROVIDER`` (e.g.
``claude-...`` + ``anthropic``) and every caller keeps working unchanged.

Structured methods use ``model.with_structured_output(Schema)`` so the model
returns typed Pydantic objects — no manual JSON parsing. The chat model is built
lazily and memoized (Design Note #1), so importing this module opens no network.
"""

import os
from functools import lru_cache
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from models.base import DepartmentType, RequestPriority
from schemas.ai import ExtractedItem, IntentResult

DEFAULT_MODEL = "gemini-2.5-flash"  # CLAUDE.md's gemini-1.5-pro is being retired
DEFAULT_PROVIDER = "google_genai"

_DEPARTMENTS = ", ".join(d.value for d in DepartmentType)

CLASSIFY_SYSTEM = (
    "You are the routing brain of a hotel guest-service app. Read the guest's "
    "message and classify it for staff dispatch. Choose the single best department "
    f"from: {_DEPARTMENTS}. Set priority (low|medium|high|urgent) by urgency and "
    "guest safety. Write a short ai_title (e.g. 'Extra towels x2'). Extract concrete "
    "items with quantities. Score sentiment from -1.0 (very upset) to 1.0 (delighted)."
)
SENTIMENT_SYSTEM = (
    "Score the sentiment of the guest message from -1.0 (very negative) to 1.0 "
    "(very positive). Return only the score."
)
EXTRACT_SYSTEM = (
    "Extract the concrete items the guest is requesting, with quantities. "
    "If none, return an empty list."
)
CHAT_SYSTEM = (
    "You are a warm, concise in-stay concierge for {hotel_name}. Help the guest, "
    "confirm requests clearly, and never invent services the hotel doesn't offer."
)


class AIServiceError(RuntimeError):
    """Raised when the model call fails and the caller must handle it (e.g. chat)."""


class _SentimentResult(BaseModel):
    # Intentionally unconstrained — a provider may overshoot the range; analyze_sentiment
    # clamps the value so an out-of-range score is preserved (clamped) not discarded.
    score: float


class _ItemList(BaseModel):
    items: list[ExtractedItem] = Field(default_factory=list)


def _clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _context_note(hotel_context: dict[str, Any] | None) -> str:
    """Fold the hotel context into a prompt hint (active departments, hotel name)."""
    if not hotel_context:
        return ""
    parts: list[str] = []
    if name := hotel_context.get("hotel_name"):
        parts.append(f"Hotel: {name}.")
    if depts := hotel_context.get("departments"):
        parts.append(f"Departments available here: {', '.join(depts)}.")
    return " ".join(parts)


class AIService:
    """Facade over a LangChain chat model. Construct with an injected model in tests."""

    def __init__(self, model: BaseChatModel):
        self._model = model

    async def classify_intent(
        self, text: str, hotel_context: dict[str, Any] | None = None
    ) -> IntentResult:
        """Route a guest message to a department + priority with items and sentiment.

        Degrades gracefully: on any model error, returns a safe default so the
        Step 6 request pipeline can still create the request.
        """
        try:
            structured = self._model.with_structured_output(IntentResult)
            messages = [
                SystemMessage(content=CLASSIFY_SYSTEM),
                HumanMessage(content=f"{_context_note(hotel_context)}\n\nGuest: {text}".strip()),
            ]
            return await structured.ainvoke(messages)
        except Exception:
            return self._fallback_intent(text)

    async def chat_response(
        self, messages: list[dict[str, str]], hotel_context: dict[str, Any] | None = None
    ) -> str:
        """Generate a guest-facing reply. Raises AIServiceError on failure."""
        hotel_name = (hotel_context or {}).get("hotel_name", "our hotel")
        lc_messages: list[Any] = [SystemMessage(content=CHAT_SYSTEM.format(hotel_name=hotel_name))]
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            lc_messages.append(
                SystemMessage(content=content)
                if role == "system"
                else HumanMessage(content=content)
                if role in ("user", "guest")
                else HumanMessage(content=content)
            )
        try:
            result = await self._model.ainvoke(lc_messages)
        except Exception as exc:  # noqa: BLE001
            raise AIServiceError("chat_response failed") from exc
        content = getattr(result, "content", result)
        return content if isinstance(content, str) else str(content)

    async def analyze_sentiment(self, text: str) -> float:
        """Return sentiment in [-1.0, 1.0]; 0.0 on failure (neutral)."""
        try:
            structured = self._model.with_structured_output(_SentimentResult)
            result = await structured.ainvoke(
                [SystemMessage(content=SENTIMENT_SYSTEM), HumanMessage(content=text)]
            )
            return _clamp(result.score)
        except Exception:
            return 0.0

    async def extract_items(self, text: str) -> list[ExtractedItem]:
        """Extract requested items + quantities; empty list on failure."""
        try:
            structured = self._model.with_structured_output(_ItemList)
            result = await structured.ainvoke(
                [SystemMessage(content=EXTRACT_SYSTEM), HumanMessage(content=text)]
            )
            return result.items
        except Exception:
            return []

    @staticmethod
    def _fallback_intent(text: str) -> IntentResult:
        """Conservative classification when the model is unavailable."""
        title = (text or "Guest request").strip()
        return IntentResult(
            department=DepartmentType.concierge,
            priority=RequestPriority.medium,
            ai_title=title[:80],
            items=[],
            sentiment=0.0,
            reason="AI unavailable — routed to concierge for manual triage.",
        )


def _api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def build_chat_model() -> BaseChatModel:
    """Build the configured LangChain chat model from env (called on first use)."""
    model = os.getenv("AI_MODEL", DEFAULT_MODEL)
    provider = os.getenv("AI_MODEL_PROVIDER", DEFAULT_PROVIDER)
    kwargs: dict[str, Any] = {"temperature": float(os.getenv("AI_TEMPERATURE", "0.2"))}
    # google_genai reads GOOGLE_API_KEY; pass our GEMINI_API_KEY explicitly so either
    # env var works. Other providers fall back to their own SDK env vars.
    if provider == "google_genai":
        key = _api_key()
        if not key:
            raise AIServiceError(
                "No Gemini API key. Set GEMINI_API_KEY (free key from "
                "https://aistudio.google.com). A Gemini Advanced subscription does "
                "not provide an API key."
            )
        kwargs["api_key"] = key
    return init_chat_model(model, model_provider=provider, **kwargs)


@lru_cache(maxsize=1)
def get_ai_service() -> AIService:
    """Process-wide AIService, built lazily on first use."""
    return AIService(build_chat_model())
