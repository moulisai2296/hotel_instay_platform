-- =============================================================================
-- InStayOS — Migration 0007: fast-authkit support tables + users reconciliation
--
-- fast-authkit (BaseUserMixin / BaseRefreshTokenMixin / BaseAuditLogMixin)
-- expects three tables: users, refresh_tokens, audit_logs.
--   * `users` already exists (migration 0002) but is missing two columns the
--     mixin requires (is_verified, updated_at) — added below.
--   * `refresh_tokens` and `audit_logs` are framework-internal and are created
--     here to match the authkit mixin column shapes exactly.
--
-- NOTE on the hotel_id rule: these two tables are auth-framework internals
-- (per-user sessions / audit), NOT hotel-scoped business data — tenancy is
-- reached through users.hotel_id. They intentionally omit hotel_id.
--
-- Idempotent: safe to re-run in the Supabase SQL Editor.
-- =============================================================================

-- ---- A. Reconcile `users` with fast-authkit BaseUserMixin -------------------
alter table users add column if not exists is_verified boolean     not null default false;
alter table users add column if not exists updated_at  timestamptz not null default now();

-- ---- B. refresh_tokens (active user sessions) -------------------------------
create table if not exists refresh_tokens (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references users(id) on delete cascade,
  jti         text not null unique,                  -- token id
  token_hash  text not null,
  expires_at  timestamptz not null,
  is_revoked  boolean not null default false,
  ip_address  text,                                  -- max 45 chars (IPv6) at app layer
  user_agent  text,
  created_at  timestamptz not null default now()
);
create index if not exists idx_refresh_tokens_user_id on refresh_tokens (user_id);
create index if not exists idx_refresh_tokens_jti     on refresh_tokens (jti);

-- ---- C. audit_logs ----------------------------------------------------------
create table if not exists audit_logs (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references users(id) on delete set null,  -- nullable: keep log if user removed
  action      text not null,
  details     jsonb,
  ip_address  text,
  user_agent  text,
  created_at  timestamptz not null default now()
);
create index if not exists idx_audit_logs_user_id on audit_logs (user_id);

-- ---- D. RLS — auth-internal tables, FastAPI service role only ---------------
-- Consistent with migration 0005: the frontend never reads these tables.
-- Enable RLS with NO policies => the `authenticated` role sees no rows; the
-- Supabase service role (used by FastAPI) bypasses RLS for all writes/reads.
alter table refresh_tokens enable row level security;
alter table audit_logs     enable row level security;
