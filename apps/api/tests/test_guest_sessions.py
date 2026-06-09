"""Manual guest check-in endpoint (POST /guest-sessions).

DB-free: GuestSessionService is replaced with a fake, so these assert routing,
the require_manager guard, validation, and that the PIN is returned once.
"""

import uuid
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

import routers.sessions as _sessions_router
from tests.conftest import auth, guest_token, make_token


class _FakeSessionService:
    def __init__(self):
        self.calls: list = []

    async def create_session(self, ctx, *, room_number, guest_name, checkout_date, **kw):
        self.calls.append((room_number, guest_name, checkout_date, kw))
        session = SimpleNamespace(
            id=uuid.uuid4(),
            guest_name=guest_name,
            checkin_date=kw.get("checkin_date") or date.today(),
            checkout_date=checkout_date,
        )
        return session, kw.get("pin") or "424242"


@pytest.fixture
def set_session_service(app):
    def _install() -> _FakeSessionService:
        fake = _FakeSessionService()
        app.dependency_overrides[_sessions_router.get_guest_session_service] = lambda: fake
        return fake

    yield _install
    app.dependency_overrides.pop(_sessions_router.get_guest_session_service, None)


def _body(**over):
    base = {
        "room_number": "205",
        "guest_name": "Jane Doe",
        "checkout_date": (date.today() + timedelta(days=2)).isoformat(),
    }
    base.update(over)
    return base


async def test_manager_can_check_in(client, set_session_service):
    fake = set_session_service()
    res = await client.post(
        "/guest-sessions", json=_body(), headers=auth(make_token(app_role="hotel_manager"))
    )
    assert res.status_code == 201
    body = res.json()
    assert body["pin"] == "424242"  # returned once
    assert body["guest_name"] == "Jane Doe"
    assert fake.calls


async def test_generated_pin_returned_when_omitted(client, set_session_service):
    set_session_service()
    res = await client.post(
        "/guest-sessions", json=_body(), headers=auth(make_token(app_role="admin"))
    )
    assert res.status_code == 201
    assert len(res.json()["pin"]) == 6


async def test_plain_staff_is_rejected(client, set_session_service):
    set_session_service()
    res = await client.post(
        "/guest-sessions", json=_body(), headers=auth(make_token(app_role="staff"))
    )
    assert res.status_code == 403
    assert res.json()["code"] == "MANAGER_ONLY"


async def test_guest_is_rejected(client, set_session_service):
    set_session_service()
    res = await client.post("/guest-sessions", json=_body(), headers=auth(guest_token()))
    assert res.status_code == 403


async def test_checkout_before_checkin_is_422(client, set_session_service):
    set_session_service()
    res = await client.post(
        "/guest-sessions",
        json=_body(
            checkin_date=date.today().isoformat(),
            checkout_date=(date.today() - timedelta(days=1)).isoformat(),
        ),
        headers=auth(make_token(app_role="hotel_manager")),
    )
    assert res.status_code == 422
