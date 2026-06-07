# InStayOS — Design Notes & Learnings

A running journal of design concepts encountered while building InStayOS. Each
entry captures *why* a choice was made so the principle is reusable in future
projects — not just "what the code does."

Format for each entry:
- **Context** — where in this project it came up
- **Principle** — the one-line takeaway
- **Explanation / analogy** — the mental model
- **Advantages / Tradeoffs**
- **Rule of thumb** — the quick test to apply it elsewhere

---

## Index
1. [Lazy initialization of external resources](#1-lazy-initialization-of-external-resources)
2. [DB-first schema ownership (migrations as source of truth)](#2-db-first-schema-ownership-migrations-as-source-of-truth)
3. [Isolating a third-party framework behind your own seams (fast-authkit)](#3-isolating-a-third-party-framework-behind-your-own-seams-fast-authkit)

---

## 1. Lazy initialization of external resources

**Context:** `apps/api/auth/setup.py`. The fast-authkit-generated file created the
DB engine, session maker, and AuthKit instance at the *top level* of the module.
Importing anything from the `auth` package (or even just `models`, which imports
`auth`) therefore tried to build a database engine and load the async driver —
crashing with `No module named 'aiosqlite'` when all we wanted was to inspect the
schema.

**Principle:** *Import time should have no side effects. Defer the creation of
external resources (DB engines, network clients, connection pools, file handles,
SDK clients) until first use, and memoize so it happens exactly once.*

### The mechanic
Code at the top level of a module runs **the moment the module is imported** (once).
Code inside a `def` runs only when the function is **called**.

```python
# OLD — runs on `import` → importing opens a DB engine + loads the driver
engine = create_async_engine(DATABASE_URL, ...)
async_session = async_sessionmaker(engine, ...)
auth_kit = AuthKit(db_session_maker=async_session, ...)

# NEW — runs on first call; nothing happens at import
@lru_cache(maxsize=1)
def get_engine():
    return create_async_engine(os.getenv("AUTHKIT_DATABASE_URL", ...), ...)
```

### Analogy — a house and its appliances
Importing a module = walking into a house.

- **Eager (old):** the instant you open the front door, the oven, AC, water heater,
  and every light switch ON automatically — even if you only came to grab your keys.
  And if the gas line isn't connected yet (driver missing / URL unset), the oven
  *explodes the moment you step inside*. You can't even enter.
- **Lazy (new):** walking in does nothing. The oven heats only when you actually
  turn it on. Need just your keys? Walk in and out, zero appliances running.
- **`@lru_cache(maxsize=1)` = the appliance stays on once started.** Without it,
  every `get_engine()` call would install a *brand-new* water heater (a new
  connection pool — a leak). With it: built once, same instance returned forever.
  That's the singleton, created on demand. **Best of both: one shared engine, but
  only when first needed.**

### Advantages
1. **Imports are safe & free of side effects** — tests, scripts, Alembic, and tools
   can import modules without opening a DB. (This is exactly what fixed our crash.)
2. **Errors surface where you can handle them** — a bad URL/missing driver fails at
   the call site inside the running app (clear stack trace), not as a cryptic
   `ImportError` before the app starts.
3. **Configuration timing** — env vars / `.env` are read at *first use*, after config
   is loaded. You aren't forced to set every env var just to import a module.
4. **Pay only for what you use** — a CLI command or a test of pure logic never opens
   a DB pool.
5. **(Async-specific) right event loop** — asyncpg pools bind to the event loop they
   live in. Building lazily means the engine is created inside the live loop, avoiding
   "attached to a different event loop" bugs.
6. **Testability** — override the env or monkeypatch before first call; reset between
   tests with `get_engine.cache_clear()`.

### Tradeoffs
- Slight indirection: callers write `get_sessionmaker()()` instead of a global.
- **You must memoize** — a bare lazy function with no cache recreates the resource
  every call (connection-pool leak). `lru_cache` is what makes it correct.
- Cache lives for the process lifetime (good for singletons; use `cache_clear()` in tests).
- Cost moves from import time to first-call ("cold start"). If you want warm-up,
  call the getter once at startup deliberately.

### Rule of thumb
> If a line at module top-level touches the **network, disk, database, or clock**,
> it probably shouldn't be at top-level. Wrap it in a memoized function.

This is the seed of **dependency injection**: modules *declare how to build* a
resource rather than eagerly *being* one.

---

## 2. DB-first schema ownership (migrations as source of truth)

**Context:** Deciding how the database schema should be created/owned for the
FastAPI + Supabase stack (whether the app should auto-create tables on first run).

**Principle:** *In a Supabase/Postgres app, the SQL migrations are the single source
of truth for the schema. SQLAlchemy models are a typed mapping layer over the
existing tables — they never create or alter the schema in production.*

### The three options (and why "app creates tables" loses)
| Approach | How tables are made | Prod-safe? |
|---|---|---|
| `Base.metadata.create_all()` on startup | App creates tables from models on boot | ❌ dev/sandbox only |
| Code-first + Alembic | Models are truth → Alembic generates migrations → applied on deploy | ✅ |
| **DB-first + SQL migrations** | Hand-written SQL migrations → applied on deploy (`supabase db push`) | ✅ (chosen) |

The key reframe: the opposite of "models create tables" is **not** "create tables by
hand." The prod-safe options are *migrations* (versioned, reviewed, reversible).
`create_all` on startup is actually the *least* prod-safe — no version history, no
rollback, no review, and it races across multiple app instances. It also only ever
*creates missing* tables; it never `ALTER`s.

### Why DB-first specifically for this stack
- **RLS is central** — Supabase Row Level Security policies use `auth.jwt() ->>
  'app_role'`. RLS, custom Postgres enums, triggers/functions, and the realtime
  publication **cannot be expressed in SQLAlchemy models.** Even with code-first
  Alembic, you'd hand-write raw SQL for all of that inside migration files anyway —
  so autogenerate buys little.
- The whole Supabase ecosystem (CLI, `db push`, branching) assumes SQL migrations.

### Tradeoff & mitigation
- **Risk:** the Python model and the real DB columns can *drift* (change SQL, forget
  the model). Mitigate by generating models from the DB (`sqlacodegen`) or a CI
  "drift test" that reflects the live schema and asserts the models match.

### Rule of thumb
> Schema changes ship as a **reviewed migration in the deploy pipeline**, never as a
> side effect of the app booting. Models map the schema; migrations own it.

---

## 3. Isolating a third-party framework behind your own seams (fast-authkit)

**Context:** Integrating `fast-authkit` as the staff auth layer (`apps/api/auth/`).
Several of the library's assumptions didn't match InStayOS — DB-first schema, a
`staff_role` enum, a required `display_name` column, and the Supabase JWT contract.
Instead of forking the library or fighting it, each mismatch was resolved at a thin
seam we control.

**Principle:** *When adopting a third-party framework, don't let its assumptions leak
through your whole app — adapt it at a thin seam you own, and treat generated scaffold
code as a draft to review, not finished code.*

### Explanation / analogy
A framework is like a **pre-fab kitchen module** craned into your house. It's far
faster than building every cabinet yourself, but the plumbing connections rarely line
up perfectly with your walls. You don't demolish the house to fit the module (fork the
library), and you don't accept a leaking joint (use it blindly) — you fit **short
adapter pipes** at the connection points. Each workaround below is one adapter pipe.

### Adapters we used (the seams)
- **Lazy init wrapper** — `get_engine()/get_sessionmaker()/get_auth_kit()` instead of
  the scaffold's import-time engine creation (see entry #1).
- **`access_token_claims` callback** — injects the Supabase JWT contract
  (`role="authenticated"`, `app_role`, `hotel_id`, `department_id`) without forking
  authkit's token creation.
- **`enable_register=False`** — authkit's `/register` hardcodes `role="user"` and omits
  the required `display_name`, which violate our schema. Staff are provisioned via the
  admin panel instead.
- **Overrode `GET /auth/me`** — authkit's router uses its own `UserRead` and ignores the
  `CustomUser*` schema stubs, so we drop its route and serve our own with
  `CustomUserRead` (exposes `display_name`, `hotel_id`, …).
- **Fixed a scaffold bug** — `mapped_column` was imported from `sqlalchemy` instead of
  `sqlalchemy.orm`, which broke first import.

### Advantages
- **Upgrade-safe:** no fork to maintain; library upgrades stay possible.
- **Leverage the hard parts:** bcrypt, refresh-token rotation, DB-backed session
  revocation, anti-enumeration — all kept.
- **App-specific needs are localized** to a few obvious files, not smeared everywhere.

### Tradeoffs
- Some glue code to maintain.
- Seams must be **re-verified on each library upgrade** (the override could drift).
- Scaffolded/generated files need auditing — they are not guaranteed correct.

### Rule of thumb
> Never edit vendored library code in place — adapt at a seam you own (callback, config
> flag, route override, wrapper). And treat any generated/scaffolded file as **a PR to
> review, not a black box**. If matching the library to your app needs more than a few
> small adapters, reconsider the library.
