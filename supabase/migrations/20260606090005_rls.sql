-- =============================================================================
-- InStayOS — Migration 0005: Row Level Security
--
-- AUTH MODEL (important):
--   InStayOS does NOT use Supabase Auth. Staff use fast-authkit JWTs and guests
--   use a custom PIN JWT. For RLS to enforce isolation on the frontend's direct
--   read queries, those JWTs MUST be signed with the Supabase JWT secret and
--   carry these claims:
--
--     sub           -> users.id            (staff/manager/admin)
--     role          -> "authenticated"     (Postgres role; reserved — keep as-is)
--     app_role      -> staff | dept_manager | hotel_manager | admin | guest
--     hotel_id      -> uuid
--     department_id -> uuid                 (staff / dept_manager)
--     session_id    -> guest_sessions.id    (guests)
--
--   WRITES: all mutations go through FastAPI using the Supabase SERVICE ROLE key,
--   which BYPASSES RLS. So these policies govern only the frontend read path.
--   Therefore we intentionally define SELECT policies only — no INSERT/UPDATE/
--   DELETE policies => the `authenticated` role cannot write directly (matches
--   "no direct writes from Next.js").
--
--   COLUMN MASKING (guest PII for sub-manager staff, encrypted PMS api_key) is
--   NOT done here — RLS is row-level. Enforce column visibility at the API layer
--   or via dedicated views. These policies handle ROW access only.
-- =============================================================================

-- ---- JWT claim helper functions --------------------------------------------
create or replace function public.jwt_claims() returns jsonb
language sql stable as $$
  select coalesce(nullif(current_setting('request.jwt.claims', true), '')::jsonb, '{}'::jsonb);
$$;

create or replace function public.auth_hotel_id() returns uuid
language sql stable as $$ select nullif(public.jwt_claims() ->> 'hotel_id', '')::uuid; $$;

create or replace function public.auth_department_id() returns uuid
language sql stable as $$ select nullif(public.jwt_claims() ->> 'department_id', '')::uuid; $$;

create or replace function public.auth_session_id() returns uuid
language sql stable as $$ select nullif(public.jwt_claims() ->> 'session_id', '')::uuid; $$;

create or replace function public.auth_user_id() returns uuid
language sql stable as $$ select nullif(public.jwt_claims() ->> 'sub', '')::uuid; $$;

create or replace function public.auth_app_role() returns text
language sql stable as $$ select public.jwt_claims() ->> 'app_role'; $$;

create or replace function public.is_staff() returns boolean
language sql stable as $$ select coalesce(public.auth_app_role() <> 'guest', false); $$;

create or replace function public.is_manager() returns boolean
language sql stable as $$ select public.auth_app_role() in ('hotel_manager', 'admin'); $$;

-- ---- Enable RLS on all tables ----------------------------------------------
alter table hotels             enable row level security;
alter table departments        enable row level security;
alter table rooms              enable row level security;
alter table tablets            enable row level security;
alter table users              enable row level security;
alter table guest_sessions     enable row level security;
alter table requests           enable row level security;
alter table request_events     enable row level security;
alter table offers             enable row level security;
alter table guest_interactions enable row level security;
alter table pms_connections    enable row level security;
alter table notifications      enable row level security;

-- ---- hotels: anyone in the tenant can read their own hotel ------------------
drop policy if exists hotels_select on hotels;
create policy hotels_select on hotels for select to authenticated
  using (id = public.auth_hotel_id());

-- ---- departments / rooms / tablets / offers: tenant-wide read ---------------
drop policy if exists departments_select on departments;
create policy departments_select on departments for select to authenticated
  using (hotel_id = public.auth_hotel_id());

drop policy if exists rooms_select on rooms;
create policy rooms_select on rooms for select to authenticated
  using (hotel_id = public.auth_hotel_id());

drop policy if exists tablets_select on tablets;
create policy tablets_select on tablets for select to authenticated
  using (hotel_id = public.auth_hotel_id());

drop policy if exists offers_select on offers;
create policy offers_select on offers for select to authenticated
  using (hotel_id = public.auth_hotel_id());

-- ---- users: staff/managers see colleagues in their hotel; guests cannot -----
drop policy if exists users_select on users;
create policy users_select on users for select to authenticated
  using (hotel_id = public.auth_hotel_id() and public.is_staff());

-- ---- guest_sessions: guest sees own; staff see sessions in their hotel ------
drop policy if exists guest_sessions_select on guest_sessions;
create policy guest_sessions_select on guest_sessions for select to authenticated
  using (
    (public.auth_app_role() = 'guest' and id = public.auth_session_id())
    or (public.is_staff() and hotel_id = public.auth_hotel_id())
  );

-- ---- requests: guest sees own; staff/dept_mgr dept-scoped; mgr/admin all -----
drop policy if exists requests_select on requests;
create policy requests_select on requests for select to authenticated
  using (
    (public.auth_app_role() = 'guest' and guest_session_id = public.auth_session_id())
    or (public.is_manager() and hotel_id = public.auth_hotel_id())
    or (public.auth_app_role() in ('staff', 'dept_manager')
        and hotel_id = public.auth_hotel_id()
        and department_id = public.auth_department_id())
  );

-- ---- request_events: guest sees events for own requests; staff hotel-wide ---
drop policy if exists request_events_select on request_events;
create policy request_events_select on request_events for select to authenticated
  using (
    (public.auth_app_role() = 'guest'
      and request_id in (
        select r.id from requests r where r.guest_session_id = public.auth_session_id()
      ))
    or (public.is_staff() and hotel_id = public.auth_hotel_id())
  );

-- ---- guest_interactions: guest sees own; only managers+ among staff ---------
-- (PRD: guest PII / chat content never exposed to staff below manager level.)
drop policy if exists guest_interactions_select on guest_interactions;
create policy guest_interactions_select on guest_interactions for select to authenticated
  using (
    (public.auth_app_role() = 'guest' and guest_session_id = public.auth_session_id())
    or (public.is_manager() and hotel_id = public.auth_hotel_id())
  );

-- ---- pms_connections: admins only -------------------------------------------
drop policy if exists pms_connections_select on pms_connections;
create policy pms_connections_select on pms_connections for select to authenticated
  using (public.auth_app_role() = 'admin' and hotel_id = public.auth_hotel_id());

-- ---- notifications: recipient sees own only ---------------------------------
drop policy if exists notifications_select on notifications;
create policy notifications_select on notifications for select to authenticated
  using (recipient_id = public.auth_user_id() and hotel_id = public.auth_hotel_id());
