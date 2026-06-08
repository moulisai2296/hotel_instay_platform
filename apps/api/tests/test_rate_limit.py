"""Rate limiting: the global per-IP default returns a 429 envelope once exceeded.

conftest sets RATE_LIMIT_DEFAULT="3/minute" and resets the limiter before each
test, so the 4th request within the window is the first to be blocked.
"""

from conftest import auth, make_token


async def test_under_limit_passes(client):
    for _ in range(3):
        resp = await client.get("/test/limited")
        assert resp.status_code == 200


async def test_over_limit_returns_429_envelope(client):
    last = None
    for _ in range(4):
        last = await client.get("/test/limited")
    assert last.status_code == 429
    body = last.json()
    assert body["code"] == "RATE_LIMITED"
    assert body["error"] == "Too many requests"
    assert "Retry-After" in last.headers


async def test_limit_applies_to_authenticated_routes_too(client):
    # The global default guards protected routes as well (keyed by IP here).
    token = make_token()
    last = None
    for _ in range(4):
        last = await client.get("/test/whoami", headers=auth(token))
    assert last.status_code == 429
    assert last.json()["code"] == "RATE_LIMITED"
