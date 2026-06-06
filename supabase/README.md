# InStayOS — Supabase Schema (Build Order Step 1)

This directory holds the database migrations for InStayOS: the source of truth for
the Supabase (PostgreSQL) schema, enums, indexes, triggers, RLS policies, and Realtime.

## Migration files (run in order)

| # | File | What it does |
|---|------|--------------|
| 1 | `migrations/20260606090001_enums.sql` | `pgcrypto` extension + 8 enum types |
| 2 | `migrations/20260606090002_tables.sql` | 12 tables, FK-ordered |
| 3 | `migrations/20260606090003_indexes.sql` | Performance indexes (all `hotel_id`, hot paths) |
| 4 | `migrations/20260606090004_functions_triggers.sql` | `updated_at`, request completion, `request_events` immutability |
| 5 | `migrations/20260606090005_rls.sql` | JWT claim helpers + Row Level Security policies |
| 6 | `migrations/20260606090006_realtime.sql` | Realtime publication on 4 tables |

All files are **idempotent** — safe to re-run.

## How to apply

### Option A — Supabase SQL Editor (no tooling)
Open your project → **SQL Editor** → paste each file's contents **in numeric order**
(0001 → 0006) and run. Do them one at a time so an error in one doesn't hide the next.

### Option B — Supabase CLI
```bash
supabase link --project-ref <your-project-ref>
supabase db push
```
The CLI runs files in timestamp order, which matches the numbering above.

## Auth model — READ THIS before frontend reads

InStayOS does **not** use Supabase Auth. Staff authenticate via fast-authkit; guests
via a custom PIN flow. For RLS to enforce isolation on the frontend's **direct read
queries** (`supabase-js` SELECTs), the app's JWTs must be **signed with the Supabase
JWT secret** and include these claims:

| Claim | Value |
|-------|-------|
| `sub` | `users.id` (staff/manager/admin) |
| `role` | `"authenticated"` — the Postgres role. **Reserved, do not overwrite.** |
| `app_role` | `staff` \| `dept_manager` \| `hotel_manager` \| `admin` \| `guest` |
| `hotel_id` | uuid |
| `department_id` | uuid (staff / dept_manager) |
| `session_id` | `guest_sessions.id` (guests) |

**Writes** go through FastAPI using the **service role key**, which **bypasses RLS**.
So the RLS policies here govern the read path only. There are intentionally **no
INSERT/UPDATE/DELETE policies** → the `authenticated` role cannot write directly,
enforcing "no direct mutations from Next.js."

## Not handled by RLS (do at API / view layer)

- **Column masking** — RLS is row-level. Hiding guest PII columns from sub-manager
  staff, and masking `pms_connections.api_key_encrypted` from non-admins, must be
  done in FastAPI responses or via dedicated views.
- **`request_events` is append-only** — enforced by a trigger that blocks UPDATE/DELETE
  for everyone (including the service role). Only INSERT is allowed.

## RLS policy summary

| Table | Who can SELECT |
|-------|----------------|
| hotels | own hotel (all roles) |
| departments / rooms / tablets / offers | tenant-wide (own `hotel_id`) |
| users | staff/managers in own hotel (guests excluded) |
| guest_sessions | guest: own; staff: all in hotel |
| requests | guest: own; staff/dept_manager: own department; manager/admin: all in hotel |
| request_events | guest: own requests; staff: hotel-wide |
| guest_interactions | guest: own; managers+admin only (not sub-manager staff) |
| pms_connections | admin only |
| notifications | recipient only |

## Verifying after apply

```sql
-- 12 tables present?
select count(*) from information_schema.tables
where table_schema = 'public';

-- RLS enabled everywhere?
select relname, relrowsecurity from pg_class
where relnamespace = 'public'::regnamespace and relkind = 'r' order by relname;

-- Realtime on exactly the 4 tables?
select tablename from pg_publication_tables where pubname = 'supabase_realtime';
```
