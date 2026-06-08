"""POST /ai/transcribe: multipart audio -> Deepgram STT (faked) -> text."""

from conftest import HOTEL_A, auth, guest_token, make_token

TRANSCRIBE = "/ai/transcribe"


async def test_transcribe_returns_text(client, set_voice_service):
    set_voice_service("I need extra towels")
    resp = await client.post(
        TRANSCRIBE,
        files={"audio": ("note.wav", b"\x00\x01fake-wav", "audio/wav")},
        headers=auth(guest_token()),
    )
    assert resp.status_code == 200
    assert resp.json() == {"text": "I need extra towels"}


async def test_transcribe_requires_guest(client, set_voice_service):
    set_voice_service("x")
    staff = make_token(app_role="staff", hotel_id=HOTEL_A)
    resp = await client.post(
        TRANSCRIBE,
        files={"audio": ("note.wav", b"audio", "audio/wav")},
        headers=auth(staff),
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "GUEST_ONLY"
