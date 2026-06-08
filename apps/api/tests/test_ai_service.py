"""AIService: provider-agnostic facade behavior, with the LangChain model faked.

No network: a narrow FakeChatModel mimics the only surface AIService touches —
``with_structured_output(schema).ainvoke(...)`` and ``ainvoke(...).content``.
"""

from types import SimpleNamespace

import pytest

from models.base import DepartmentType, RequestPriority
from schemas.ai import ExtractedItem, IntentResult
from services import AIService, AIServiceError


class _Runnable:
    def __init__(self, value, raises=False):
        self._value = value
        self._raises = raises

    async def ainvoke(self, messages):
        if self._raises:
            raise RuntimeError("model boom")
        return self._value


class FakeChatModel:
    """Implements just the slice of BaseChatModel that AIService calls."""

    def __init__(self, *, structured=None, chat_content="", raises=False):
        self._structured = structured
        self._chat_content = chat_content
        self._raises = raises

    def with_structured_output(self, schema):
        return _Runnable(self._structured, self._raises)

    async def ainvoke(self, messages):
        if self._raises:
            raise RuntimeError("model boom")
        return SimpleNamespace(content=self._chat_content)


HOTEL_CTX = {"hotel_name": "Grand Hotel", "departments": ["housekeeping", "fb"]}


async def test_classify_intent_passthrough():
    canned = IntentResult(
        department=DepartmentType.housekeeping,
        priority=RequestPriority.high,
        ai_title="Extra towels x2",
        items=[ExtractedItem(item="towel", qty=2)],
        sentiment=0.1,
    )
    svc = AIService(FakeChatModel(structured=canned))
    result = await svc.classify_intent("I need 2 extra towels please", HOTEL_CTX)
    assert result.department is DepartmentType.housekeeping
    assert result.items[0].item == "towel" and result.items[0].qty == 2


async def test_classify_intent_falls_back_on_model_error():
    svc = AIService(FakeChatModel(raises=True))
    result = await svc.classify_intent("The shower is broken", HOTEL_CTX)
    assert result.department is DepartmentType.concierge  # safe default
    assert result.priority is RequestPriority.medium
    assert "shower" in result.ai_title


async def test_analyze_sentiment_clamps_high():
    svc = AIService(FakeChatModel(structured=SimpleNamespace(score=1.7)))
    assert await svc.analyze_sentiment("amazing stay!") == 1.0


async def test_analyze_sentiment_clamps_low():
    svc = AIService(FakeChatModel(structured=SimpleNamespace(score=-3.0)))
    assert await svc.analyze_sentiment("worst ever") == -1.0


async def test_analyze_sentiment_neutral_on_error():
    svc = AIService(FakeChatModel(raises=True))
    assert await svc.analyze_sentiment("anything") == 0.0


async def test_extract_items_passthrough():
    from services.ai_service import _ItemList

    items = _ItemList(items=[ExtractedItem(item="pillow", qty=3)])
    svc = AIService(FakeChatModel(structured=items))
    result = await svc.extract_items("can I get 3 pillows")
    assert [(i.item, i.qty) for i in result] == [("pillow", 3)]


async def test_chat_response_returns_text():
    svc = AIService(FakeChatModel(chat_content="Of course, sending towels now."))
    reply = await svc.chat_response([{"role": "guest", "content": "towels?"}], HOTEL_CTX)
    assert reply == "Of course, sending towels now."


async def test_chat_response_raises_on_model_error():
    svc = AIService(FakeChatModel(raises=True))
    with pytest.raises(AIServiceError):
        await svc.chat_response([{"role": "guest", "content": "hi"}])
