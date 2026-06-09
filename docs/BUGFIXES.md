# InStayOS — Bug Fix Log

A running log of bugs found during development and how they were resolved. Newest
first. Each entry: symptom → root cause → fix → files touched.

---

## BF-002 · `POST /requests/create` takes ~37s (feels like the app hangs)

- **Date:** 2026-06-09
- **Found during:** PR 2 (guest app) — live chat testing from the UI.
- **Symptom:** Sending a chat message (which calls `/requests/create`) appeared to
  "run forever" — ~37 seconds before any reply. Even an off-topic message like
  "tell me a joke" (one classify call, no DB-heavy work) took ~37s.
- **Root cause:** The **Gemini free-tier quota was exhausted** (`429
  RESOURCE_EXHAUSTED`) from repeated testing. `AIService.classify_intent` already
  degrades gracefully on AI failure (`_fallback_intent` → a safe concierge
  request), but the underlying `langchain-google-genai` client **retries a 429 six
  times with exponential backoff (~30s+)** before raising, so the graceful
  fallback only kicked in after the full retry budget.
- **Fix:** Cap retries and add a request timeout for the `google_genai` provider so
  a rate-limited turn degrades in seconds instead of ~37s. Env-overridable:
  `AI_MAX_RETRIES` (default `1`) and `AI_TIMEOUT` (default `20`s). Result:
  `/requests/create` returns in ~4s while rate-limited (still creates + tracks the
  request; reply is the generic fallback until quota frees up).
- **Files:** `apps/api/services/ai_service.py` (`build_chat_model`).
- **Note / follow-up:** This is a *resilience* fix, not a quota fix. While the free
  tier is exhausted, AI replies are generic (no smart routing/title/items) and the
  intent guardrails (needs_info / unsupported) won't show. For unthrottled AI
  testing, use a higher-quota / paid `GEMINI_API_KEY`. Thorough AI testing is
  deferred until the app is more complete.

---

## BF-001 · Backend hangs or 500s (`connection is closed`) on the first request after idle

- **Date:** 2026-06-09
- **Found during:** PR 2 (guest app) — integration testing after the backend sat
  idle between requests.
- **Symptom:** After a period of inactivity, the next DB-touching request either
  returned `500` with
  `asyncpg ... InterfaceError: connection is closed`, or hung indefinitely.
- **Root cause:** The app talks to Postgres through the **Supabase connection
  pooler**, which silently drops idle connections. The async SQLAlchemy engine was
  created without connection health checks, so SQLAlchemy handed out a dead
  connection. Depending on timing this surfaced as an immediate "connection is
  closed" error, or — on a half-open socket — a query that waited forever for a
  response that never came (the apparent "hang").
- **Fix:** Harden the engine (Postgres only) with:
  - `pool_pre_ping=True` — validate a connection before use, transparently
    reconnecting if it's dead.
  - `pool_recycle=1800` — proactively retire connections older than 30 min.
  - `connect_args`: `statement_cache_size=0` (pgbouncer-safe) and
    `command_timeout=30` (no single query can hang forever).
- **Files:** `apps/api/auth/setup.py` (`get_engine`).

---
