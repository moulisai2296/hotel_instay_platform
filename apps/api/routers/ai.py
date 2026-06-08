"""AI utility endpoints. Currently: voice-note transcription (Deepgram STT).

Storage of the audio (voice_url) is deferred — this returns the transcript text,
which the client then submits to /requests/create with input_mode="voice".
"""

from fastapi import APIRouter, Depends, File, UploadFile

from middleware import RequestContext, require_guest
from schemas import TranscribeResponse
from services import VoiceService, get_voice_service

router = APIRouter(prefix="/ai", tags=["ai"])


def get_voice() -> VoiceService:
    """Provider for the voice service — overridden in tests with a fake."""
    return get_voice_service()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    audio: UploadFile = File(...),
    ctx: RequestContext = Depends(require_guest),
    voice: VoiceService = Depends(get_voice),
) -> TranscribeResponse:
    """Transcribe an uploaded voice note to text."""
    data = await audio.read()
    text = await voice.transcribe(data, mimetype=audio.content_type or "audio/wav")
    return TranscribeResponse(text=text)
