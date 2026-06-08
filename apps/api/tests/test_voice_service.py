"""VoiceService: Deepgram transcript extraction, with the SDK client faked."""

from types import SimpleNamespace

import pytest

from services import VoiceService, VoiceServiceError


def _response(transcript: str):
    alt = SimpleNamespace(transcript=transcript)
    channel = SimpleNamespace(alternatives=[alt])
    return SimpleNamespace(results=SimpleNamespace(channels=[channel]))


class _FakeMedia:
    def __init__(self, response=None, raises=False):
        self._response = response
        self._raises = raises
        self.calls: list[dict] = []

    async def transcribe_file(self, **kwargs):
        if self._raises:
            raise RuntimeError("network down")
        self.calls.append(kwargs)
        return self._response


class FakeDeepgram:
    """Mimics client.listen.v1.media.transcribe_file."""

    def __init__(self, response=None, raises=False):
        self.media = _FakeMedia(response, raises)
        self.listen = SimpleNamespace(v1=SimpleNamespace(media=self.media))


async def test_transcribe_returns_best_alternative():
    client = FakeDeepgram(_response("I need extra towels"))
    svc = VoiceService(client)
    assert await svc.transcribe(b"\x00\x01audio") == "I need extra towels"
    # audio bytes are forwarded as the request body
    assert client.media.calls[0]["request"] == b"\x00\x01audio"


async def test_transcribe_empty_when_no_channels():
    empty = SimpleNamespace(results=SimpleNamespace(channels=[]))
    svc = VoiceService(FakeDeepgram(empty))
    assert await svc.transcribe(b"audio") == ""


async def test_transcribe_raises_on_sdk_error():
    svc = VoiceService(FakeDeepgram(raises=True))
    with pytest.raises(VoiceServiceError):
        await svc.transcribe(b"audio")
