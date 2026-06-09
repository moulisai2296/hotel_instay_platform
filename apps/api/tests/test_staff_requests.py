"""Staff request status endpoint (PATCH /requests/{id}/status).

DB-free: the StaffRequestService is replaced with a fake via dependency override,
so these assert the routing, the require_staff guard, and the response mapping —
not the DB writes (those live in the service).
"""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import routers.requests as _requests_router
from models.base import RequestPriority, RequestStatus
from tests.conftest import DEPT_A, auth, guest_token, make_token


class _FakeStaffService:
    def __init__(self):
        self.calls: list = []

    async def update_status(self, ctx, request_id, new_status, note=None):
        self.calls.append((request_id, new_status, note))
        return SimpleNamespace(
            id=request_id,
            status=new_status,
            priority=RequestPriority.medium,
            department_id=DEPT_A,
            ai_title="Extra towels",
            ai_items=[{"item": "towel", "qty": 2}],
            sentiment_score=0.1,
            created_at=datetime.now(timezone.utc),
        )


@pytest.fixture
def set_staff_service(app):
    def _install() -> _FakeStaffService:
        fake = _FakeStaffService()
        app.dependency_overrides[_requests_router.get_staff_request_service] = lambda: fake
        return fake

    yield _install
    app.dependency_overrides.pop(_requests_router.get_staff_request_service, None)


async def test_staff_can_update_status(client, set_staff_service):
    fake = set_staff_service()
    rid = uuid.uuid4()
    res = await client.patch(
        f"/requests/{rid}/status",
        json={"status": "in_progress"},
        headers=auth(make_token(app_role="staff")),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "in_progress"
    assert body["id"] == str(rid)
    assert fake.calls and fake.calls[0][1] == RequestStatus.in_progress


async def test_guest_token_is_rejected(client, set_staff_service):
    set_staff_service()
    res = await client.patch(
        f"/requests/{uuid.uuid4()}/status",
        json={"status": "completed"},
        headers=auth(guest_token()),
    )
    assert res.status_code == 403
    assert res.json()["code"] == "STAFF_ONLY"


async def test_unauthenticated_is_rejected(client, set_staff_service):
    set_staff_service()
    res = await client.patch(
        f"/requests/{uuid.uuid4()}/status", json={"status": "completed"}
    )
    assert res.status_code == 401


async def test_invalid_status_is_422(client, set_staff_service):
    set_staff_service()
    res = await client.patch(
        f"/requests/{uuid.uuid4()}/status",
        json={"status": "teleported"},
        headers=auth(make_token(app_role="dept_manager")),
    )
    assert res.status_code == 422
