"""Guest chat turn: classify -> route+persist / clarify / decline.

DB- and model-free: a fake repo records what would be persisted and a fake
AIService returns a canned IntentResult, so we assert routing, the guardrails, and
isolation without a database.
"""

from conftest import (
    DEPT_A,
    DEPT_DEFAULT,
    HOTEL_A,
    ROOM_A,
    SESSION_A,
    auth,
    guest_token,
    make_intent,
    make_token,
)
from models.base import DepartmentType
from schemas.ai import IntentKind

CREATE = "/requests/create"
BODY = {"raw_input": "I need 2 extra towels in room 412", "input_mode": "text"}


async def test_service_request_classifies_and_persists(client, set_request_service):
    repo = set_request_service(make_intent())
    resp = await client.post(CREATE, json=BODY, headers=auth(guest_token()))
    assert resp.status_code == 201  # a request was created
    data = resp.json()
    assert data["kind"] == "service_request"
    assert data["guest_reply"] == "Of course — towels are on the way!"
    assert data["request"]["priority"] == "high"
    assert data["request"]["ai_title"] == "Extra towels x2"
    assert data["request"]["items"] == [{"item": "towel", "qty": 2}]
    assert data["request"]["department_id"] == str(DEPT_A)

    saved = repo.persisted
    assert saved.event.event_type == "created" and saved.event.to_status == "pending"
    assert [i.role for i in saved.interactions] == ["guest", "assistant"]


async def test_unsupported_message_is_declined_no_request(client, set_request_service):
    # Off-topic (coding/general) -> kind=unsupported -> canned scope message, no request.
    repo = set_request_service(make_intent(kind=IntentKind.unsupported, guest_reply="<ignored>"))
    resp = await client.post(
        CREATE, json={**BODY, "raw_input": "write me a python quicksort"}, headers=auth(guest_token())
    )
    assert resp.status_code == 200  # nothing created
    data = resp.json()
    assert data["kind"] == "unsupported"
    assert data["request"] is None
    # Deterministic scope message (not the model's text), built from active departments.
    assert "in-stay assistant" in data["guest_reply"]
    assert "<ignored>" not in data["guest_reply"]
    # Still logged to the transcript, but no request/event persisted.
    assert repo.persisted.request is None
    assert [i.role for i in repo.persisted.interactions] == ["guest", "assistant"]


async def test_needs_info_asks_clarifying_question_no_request(client, set_request_service):
    repo = set_request_service(
        make_intent(kind=IntentKind.needs_info, guest_reply="How many pillows would you like?")
    )
    resp = await client.post(
        CREATE, json={**BODY, "raw_input": "I need extra pillows"}, headers=auth(guest_token())
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["kind"] == "needs_info"
    assert data["request"] is None
    assert data["guest_reply"] == "How many pillows would you like?"
    assert repo.persisted.request is None


async def test_voice_message_goes_through_the_same_guardrail(client, set_request_service):
    # A transcribed voice note hits /requests/create with input_mode="voice" and is
    # gated identically: off-topic speech is declined, no request created.
    repo = set_request_service(make_intent(kind=IntentKind.unsupported))
    resp = await client.post(
        CREATE,
        json={"raw_input": "what is the capital of France", "input_mode": "voice"},
        headers=auth(guest_token()),
    )
    assert resp.status_code == 200
    assert resp.json()["kind"] == "unsupported"
    assert resp.json()["request"] is None
    assert repo.persisted.request is None


async def test_voice_service_request_records_voice_input_mode(client, set_request_service):
    from models.base import InputMode

    repo = set_request_service(make_intent())
    resp = await client.post(
        CREATE,
        json={"raw_input": "I need 2 towels", "input_mode": "voice"},
        headers=auth(guest_token()),
    )
    assert resp.status_code == 201
    assert repo.persisted.request.input_mode == InputMode.voice


async def test_scope_taken_from_jwt_not_body(client, set_request_service):
    repo = set_request_service(make_intent())
    resp = await client.post(
        CREATE,
        json={**BODY, "hotel_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth(guest_token()),
    )
    assert resp.status_code == 201
    req = repo.persisted.request
    assert req.hotel_id == HOTEL_A
    assert req.room_id == ROOM_A
    assert req.guest_session_id == SESSION_A


async def test_department_fallback_when_inactive(client, set_request_service):
    repo = set_request_service(make_intent(department=DepartmentType.spa), dept_id=None)
    resp = await client.post(CREATE, json=BODY, headers=auth(guest_token()))
    assert resp.status_code == 201
    assert resp.json()["request"]["department_id"] == str(DEPT_DEFAULT)


async def test_422_when_hotel_has_no_department(client, set_request_service):
    set_request_service(make_intent(), dept_id=None, default_dept_id=None)
    resp = await client.post(CREATE, json=BODY, headers=auth(guest_token()))
    assert resp.status_code == 422
    assert resp.json()["code"] == "NO_DEPARTMENT"


async def test_requires_guest(client, set_request_service):
    set_request_service(make_intent())
    staff = make_token(app_role="staff", hotel_id=HOTEL_A)
    resp = await client.post(CREATE, json=BODY, headers=auth(staff))
    assert resp.status_code == 403
    assert resp.json()["code"] == "GUEST_ONLY"


async def test_unauthenticated(client):
    resp = await client.post(CREATE, json=BODY)
    assert resp.status_code == 401
