# InStayOS — API Reference

Hand-written reference for the frontend. Covers the **REST API** (FastAPI, all
mutations + logic-heavy reads) and the **direct-from-Supabase reads** (simple
"my rows" lists + realtime) that don't go through REST. Reflects the backend as
implemented through Step 6.

- **Base URL:** `NEXT_PUBLIC_API_BASE_URL` (local: `http://localhost:8000`)
- **All requests/responses are JSON** unless noted (transcribe is multipart).
- **CORS:** credentials allowed for the configured origins (`CORS_ORIGINS`).

---

## 1. Auth model

Two JWT kinds, both **HS256**, both `type="access"`, both carry `app_role` +
`hotel_id`. Send as `Authorization: Bearer <token>` (staff may also use the
HTTP-only cookie set on login).

| Caller | How they get a token | `app_role` |
|---|---|---|
| Staff / Dept manager / Hotel manager / Admin | `POST /auth/login` (email+password) | `staff` / `dept_manager` / `hotel_manager` / `admin` |
| Guest | `POST /guest/verify-pin` (hotel slug + room + PIN) | `guest` |

**JWT claims (read by the frontend / RLS):**
```
sub            user id (staff) or guest_session id (guest)
role           "authenticated"          (required by Supabase RLS)
app_role       staff|dept_manager|hotel_manager|admin|guest
hotel_id       uuid
department_id  uuid | null              (staff/dept_manager)
session_id     uuid                     (guests only)
room_id        uuid                     (guests only)
guest_name     string                   (guests only)
exp            staff: ~15 min · guest: checkout_date 23:59 (hotel tz)
```

---

## 2. Conventions

**Error envelope** — every error is:
```json
{ "error": "human message", "code": "MACHINE_CODE" }
```
Validation errors add `"details"`. Codes the UI should handle:

| Code | HTTP | Meaning |
|---|---|---|
| `NOT_AUTHENTICATED` | 401 | No/blank token |
| `INVALID_TOKEN` | 401 | Malformed/expired/not an access token |
| `INVALID_CREDENTIALS` | 401 | Wrong room/PIN (uniform — never says which) |
| `GUEST_ONLY` | 403 | Guest-only route hit by a non-guest |
| `HOTEL_MISMATCH` | 403 | Cross-hotel access attempt |
| `MODE_DISABLED` | 403 | Guest access mode not enabled for this deployment |
| `NO_DEPARTMENT` | 422 | Hotel has no active department to route to |
| `VALIDATION_ERROR` | 422 | Body failed schema validation (+`details`) |
| `RATE_LIMITED` | 429 | Too many requests (`Retry-After` header) |

**Rate limits:** global default `100/min` per IP; `POST /guest/verify-pin` is
`5/min` (brute-force defense).

---

## 3. Staff / Manager / Admin auth (fast-authkit)

### POST `/auth/login`
```json
// request
{ "email": "manager@hotel.com", "password": "•••••••" }
// 200 — also sets HTTP-only cookies authkit_access / authkit_refresh
{ "access_token": "eyJ…", "refresh_token": "eyJ…", "token_type": "bearer" }
```
`401` Incorrect email or password · `403` account deactivated.

### POST `/auth/refresh`
Rotates tokens. Refresh token from the `authkit_refresh` cookie or
`Authorization: Bearer <refresh>`. Returns the same shape as login. `401` if the
session was revoked.

### POST `/auth/logout` · POST `/auth/logout-all`
Revoke the current (or all) refresh sessions and clear cookies. `logout-all`
requires a valid access token.

### GET `/auth/me`  *(auth required)*
```json
{
  "id": "uuid", "email": "…", "is_active": true, "is_verified": true,
  "role": "hotel_manager",
  "display_name": "Asha R.", "hotel_id": "uuid",
  "department_id": null, "avatar_url": null, "last_seen_at": "2026-06-08T…Z"
}
```

### POST `/auth/forgot-password` `{ "email" }` · POST `/auth/reset-password` `{ "token", "new_password" }`
Email-driven reset (no-op response on unknown email to avoid enumeration).

> `POST /auth/register` exists but is **disabled** (`403`) — staff are provisioned
> via the admin panel, not self-registration.

---

## 4. Guest auth (custom PIN flow — mobile-first)

### POST `/guest/verify-pin`   *(rate limit 5/min)*
The web app is served per-hotel (`/h/{hotel-slug}`), so the client knows the slug;
the guest types room number + 6-digit PIN.
```json
// request
{ "hotel_slug": "grand-hotel", "room_number": "412", "pin": "481920" }
// 200
{
  "access_token": "eyJ…",
  "token_type": "bearer",
  "expires_at": "2026-06-11T18:29:59Z",
  "guest": {
    "session_id": "uuid", "guest_name": "Sam Lee",
    "room_number": "412", "hotel_id": "uuid", "checkout_date": "2026-06-11"
  }
}
```
`401 INVALID_CREDENTIALS` for any failure (unknown hotel/room, wrong PIN, checked
out — uniform). `422 VALIDATION_ERROR` if `pin` isn't 6 digits.
Store the token in memory/`sessionStorage` only — **never** `localStorage`.

### GET `/guest/me`   *(guest token required)*
```json
{ "session_id": "uuid", "hotel_id": "uuid", "room_id": "uuid", "app_role": "guest" }
```
`403 GUEST_ONLY` if a non-guest token is used.

---

## 5. Guest chat + requests

### POST `/requests/create`   *(guest token required)*
The guest "chat turn" endpoint. The message is classified and **gated** before any
write (see `kind`). Always returns a reply; only an actionable request creates a
`requests` row.
```json
// request  (hotel_id/room_id/session_id come from the JWT — never send them)
{ "raw_input": "I need 2 extra towels", "input_mode": "text", "voice_url": null }
```
`input_mode`: `text` | `voice` | `chip`. For a voice note, transcribe first
(§6) and send the text with `input_mode: "voice"`.

```jsonc
// 201 Created  — kind == "service_request"
{
  "kind": "service_request",
  "guest_reply": "Of course — your towels are on the way!",
  "request": {
    "id": "uuid", "status": "pending", "priority": "high",
    "department_id": "uuid", "ai_title": "Extra towels x2",
    "items": [{ "item": "towel", "qty": 2 }],
    "sentiment": 0.2, "created_at": "2026-06-08T…Z"
  }
}
```
```jsonc
// 200 OK — kind == "needs_info"  (a required detail is missing; NO request)
{ "kind": "needs_info", "guest_reply": "How many pillows would you like?", "request": null }

// 200 OK — kind == "unsupported"  (off-topic; deterministic scope message; NO request)
{ "kind": "unsupported",
  "guest_reply": "I'm your in-stay assistant, so I can only help with hotel services…",
  "request": null }
```
`422 NO_DEPARTMENT` if the hotel has no active department. The follow-up to a
`needs_info` question (e.g. just `"2"`) is sent as a normal create call; the
backend resolves it using recent chat history.

### POST `/ai/transcribe`   *(guest token required, multipart)*
```
Content-Type: multipart/form-data
audio=<file>        # the recorded voice note
```
```json
// 200
{ "text": "I need two extra towels" }
```
Returns text only (no storage yet). The client then submits it via
`/requests/create` with `input_mode: "voice"`.

---

## 6. Direct-from-Supabase reads (NOT REST)

Per the architecture decision (DESIGN_NOTES #8), **simple "rows that belong to me"
reads + realtime go straight from Next.js via the Supabase client + RLS** — there
are no REST endpoints for these. Authenticate the Supabase client with the **same
JWT** (so RLS sees `session_id`/`hotel_id`):

```ts
const supabase = createClient(URL, ANON_KEY, {
  accessToken: async () => token,   // guest or staff JWT
})
```
Frontend uses the **anon** key only — never the service-role key.

**Guest chat history** — render as bubbles:
```ts
supabase.from('guest_interactions')
  .select('role, content, input_mode, created_at')
  .order('created_at')          // RLS scopes to the guest's own session
```
**Request tracker** (guest) / **kanban** (staff):
```ts
supabase.from('requests').select('*')           // RLS: own session / own hotel+dept
supabase.from('request_events').select('*')     // status timeline (append-only)
```
**Realtime** (live kanban + tracker + alert bell) — subscribe to:
`requests`, `request_events`, `notifications`, `tablets`. Example:
```ts
supabase.channel('requests')
  .on('postgres_changes',
      { event: '*', schema: 'public', table: 'requests',
        filter: `department_id=eq.${departmentId}` },
      handle)
  .subscribe()
```

> Rule of thumb: **writes + AI/aggregation → REST (this doc).** "My rows" lists +
> live updates → Supabase client + RLS.

---

## 7. Enum reference (for the UI)

```
app_role        : staff | dept_manager | hotel_manager | admin | guest
department_type : housekeeping | fb | maintenance | concierge | spa | front_desk
request_status  : pending | assigned | in_progress | completed | escalated | cancelled
request_priority: low | medium | high | urgent
input_mode      : text | voice | chip
intent kind     : service_request | needs_info | unsupported
```

---

## 8. Meta

### GET `/health`
```json
{ "status": "ok" }
```

> Interactive Swagger/OpenAPI is also available at `/docs` (FastAPI) for the REST
> endpoints, but this file is the source of truth — it also documents the
> direct-Supabase reads and the auth/JWT contract that OpenAPI can't express.
