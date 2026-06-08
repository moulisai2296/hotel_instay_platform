"""Speech-to-text for guest voice notes (Deepgram).

Kept behind ``VoiceService`` so the transcription provider stays swappable, and so
the request pipeline (Step 6) depends on a stable ``transcribe`` interface rather
than the SDK. The voice flow is: audio bytes -> ``transcribe`` -> text -> the AI
processing layer (``AIService``).

The Deepgram client is built lazily and memoized (Design Note #1); importing this
module opens no network.
"""

import os
from functools import lru_cache

from deepgram import AsyncDeepgramClient

DEFAULT_STT_MODEL = "nova-2"


class VoiceServiceError(RuntimeError):
    """Raised when transcription fails."""


class VoiceService:
    """Wrapper over Deepgram prerecorded STT. Inject a fake client in tests."""

    def __init__(self, client: AsyncDeepgramClient, model: str = DEFAULT_STT_MODEL):
        self._client = client
        self._model = model

    async def transcribe(self, audio: bytes, mimetype: str = "audio/wav") -> str:
        """Transcribe audio bytes to text (best alternative); "" if no speech found."""
        try:
            response = await self._client.listen.v1.media.transcribe_file(
                request=audio,
                model=self._model,
                smart_format=True,
                punctuate=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise VoiceServiceError("Deepgram transcription failed") from exc
        return _extract_transcript(response)


def _extract_transcript(response: object) -> str:
    """Pull channels[0].alternatives[0].transcript out of a Deepgram response."""
    try:
        channels = response.results.channels  # type: ignore[attr-defined]
        if not channels:
            return ""
        alternatives = channels[0].alternatives or []
        if not alternatives:
            return ""
        return (alternatives[0].transcript or "").strip()
    except AttributeError as exc:
        raise VoiceServiceError("Unexpected Deepgram response shape") from exc


def build_deepgram_client() -> AsyncDeepgramClient:
    """Build the async Deepgram client from DEEPGRAM_API_KEY (called on first use)."""
    key = os.getenv("DEEPGRAM_API_KEY")
    if not key:
        raise VoiceServiceError("No DEEPGRAM_API_KEY configured.")
    return AsyncDeepgramClient(api_key=key)


@lru_cache(maxsize=1)
def get_voice_service() -> VoiceService:
    """Process-wide VoiceService, built lazily on first use."""
    return VoiceService(build_deepgram_client())
