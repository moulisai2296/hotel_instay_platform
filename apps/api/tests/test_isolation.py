"""Hotel-isolation guard: cross-tenant access must be impossible at the app layer."""

import uuid

from conftest import HOTEL_A, HOTEL_B, auth, make_token


async def test_no_token_is_unauthenticated(client):
    resp = await client.get("/test/whoami")
    assert resp.status_code == 401
    assert resp.json()["code"] == "NOT_AUTHENTICATED"


async def test_garbage_token_is_invalid(client):
    resp = await client.get("/test/whoami", headers=auth("not-a-real-jwt"))
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_TOKEN"


async def test_refresh_token_rejected_as_access(client):
    token = make_token(token_type="refresh")
    resp = await client.get("/test/whoami", headers=auth(token))
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_TOKEN"


async def test_expired_token_rejected(client):
    token = make_token(expired=True)
    resp = await client.get("/test/whoami", headers=auth(token))
    assert resp.status_code == 401


async def test_same_hotel_allowed(client):
    token = make_token(app_role="staff", hotel_id=HOTEL_A)
    resp = await client.get(f"/test/hotels/{HOTEL_A}/resource", headers=auth(token))
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


async def test_cross_hotel_forbidden(client):
    token = make_token(app_role="staff", hotel_id=HOTEL_A)
    resp = await client.get(f"/test/hotels/{HOTEL_B}/resource", headers=auth(token))
    assert resp.status_code == 403
    assert resp.json()["code"] == "HOTEL_MISMATCH"


async def test_super_admin_crosses_hotels(client):
    # Platform super-admin: app_role=admin, hotel_id=NULL — may reach any hotel.
    token = make_token(app_role="admin", hotel_id=None)
    for hotel in (HOTEL_A, HOTEL_B, uuid.uuid4()):
        resp = await client.get(f"/test/hotels/{hotel}/resource", headers=auth(token))
        assert resp.status_code == 200
