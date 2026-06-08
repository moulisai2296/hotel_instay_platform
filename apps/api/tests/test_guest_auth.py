"""Guest PIN auth: mobile verify-pin flow + the guest JWT it mints."""

from datetime import date, datetime, timezone

import jwt

from conftest import (
    GUEST_PIN,
    HOTEL_A,
    ROOM_A,
    SECRET,
    SESSION_A,
    auth,
    make_guest_session,
    make_resolved,
    make_token,
)
from services import compute_token_expiry, is_session_active

VERIFY_BODY = {"hotel_slug": "grand-hotel", "room_number": "101", "pin": GUEST_PIN}


# --- Pure helpers (no app/DB) ------------------------------------------------


def test_is_session_active_window():
    s = make_guest_session()
    today = date.today()
    assert is_session_active(s, today) is True
    assert is_session_active(make_guest_session(is_checked_out=True), today) is False


def test_token_expiry_is_checkout_end_of_day_utc():
    exp = compute_token_expiry(date(2026, 6, 10), "America/New_York")
    # 23:59:59 EDT on Jun 10 == 03:59:59 UTC on Jun 11.
    assert exp == datetime(2026, 6, 11, 3, 59, 59, tzinfo=timezone.utc)
    # Unknown timezone falls back to UTC without raising.
    assert compute_token_expiry(date(2026, 6, 10), "Not/AZone").tzinfo == timezone.utc


# --- verify-pin endpoint -----------------------------------------------------


async def test_valid_pin_issues_guest_token(client, set_guest_service):
    set_guest_service(make_resolved(make_guest_session()))
    resp = await client.post("/guest/verify-pin", json=VERIFY_BODY)
    assert resp.status_code == 200
    data = resp.json()
    assert data["guest"]["session_id"] == str(SESSION_A)
    assert data["guest"]["guest_name"] == "Test Guest"

    claims = jwt.decode(data["access_token"], SECRET, algorithms=["HS256"])
    assert claims["app_role"] == "guest"
    assert claims["role"] == "authenticated"
    assert claims["type"] == "access"
    assert claims["sub"] == str(SESSION_A)
    assert claims["session_id"] == str(SESSION_A)
    assert claims["hotel_id"] == str(HOTEL_A)
    assert claims["room_id"] == str(ROOM_A)
    assert claims["exp"] > datetime.now(timezone.utc).timestamp()


async def test_wrong_pin_is_uniform_401(client, set_guest_service):
    set_guest_service(make_resolved(make_guest_session()))
    resp = await client.post("/guest/verify-pin", json={**VERIFY_BODY, "pin": "000000"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_CREDENTIALS"


async def test_no_active_session_is_uniform_401(client, set_guest_service):
    # Unknown hotel/room, checked out, or out-of-window all surface as None.
    set_guest_service(make_resolved(None))
    resp = await client.post("/guest/verify-pin", json=VERIFY_BODY)
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_CREDENTIALS"


async def test_malformed_pin_rejected_by_validation(client, set_guest_service):
    set_guest_service(make_resolved(make_guest_session()))
    resp = await client.post("/guest/verify-pin", json={**VERIFY_BODY, "pin": "12ab"})
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"


async def test_verify_pin_is_rate_limited(client, set_guest_service):
    set_guest_service(make_resolved(None))  # PIN_VERIFY_LIMIT = 5/minute
    last = None
    for _ in range(6):
        last = await client.post("/guest/verify-pin", json=VERIFY_BODY)
    assert last.status_code == 429
    assert last.json()["code"] == "RATE_LIMITED"


# --- the minted token against the rest of the system -------------------------


async def test_guest_token_accepted_by_guest_me(client, set_guest_service):
    set_guest_service(make_resolved(make_guest_session()))
    token = (await client.post("/guest/verify-pin", json=VERIFY_BODY)).json()["access_token"]

    resp = await client.get("/guest/me", headers=auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["app_role"] == "guest"
    assert body["session_id"] == str(SESSION_A)
    assert body["room_id"] == str(ROOM_A)


async def test_staff_token_blocked_from_guest_me(client):
    token = make_token(app_role="staff", hotel_id=HOTEL_A)
    resp = await client.get("/guest/me", headers=auth(token))
    assert resp.status_code == 403
    assert resp.json()["code"] == "GUEST_ONLY"
