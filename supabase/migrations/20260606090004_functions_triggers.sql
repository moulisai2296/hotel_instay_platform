-- =============================================================================
-- InStayOS — Migration 0004: Functions + Triggers
--   1. updated_at auto-maintenance (hotels, guest_sessions, requests)
--   2. requests completion: auto-fill completed_at + resolution_time_mins
--   3. request_events immutability guard (append-only invariant)
-- Idempotent: functions use CREATE OR REPLACE; triggers dropped + recreated.
-- =============================================================================

-- 1. updated_at -------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end $$;

drop trigger if exists trg_hotels_updated_at on hotels;
create trigger trg_hotels_updated_at before update on hotels
  for each row execute function public.set_updated_at();

drop trigger if exists trg_guest_sessions_updated_at on guest_sessions;
create trigger trg_guest_sessions_updated_at before update on guest_sessions
  for each row execute function public.set_updated_at();

drop trigger if exists trg_requests_updated_at on requests;
create trigger trg_requests_updated_at before update on requests
  for each row execute function public.set_updated_at();

-- 2. request completion -------------------------------------------------------
-- Defensive safety net: the API normally computes these, but this guarantees
-- completed_at + resolution_time_mins are set whenever status flips to
-- 'completed'. Idempotent — only fills values that are still NULL.
create or replace function public.set_request_completion()
returns trigger language plpgsql as $$
begin
  if new.status = 'completed' and old.status is distinct from 'completed' then
    if new.completed_at is null then
      new.completed_at := now();
    end if;
    if new.resolution_time_mins is null then
      new.resolution_time_mins :=
        greatest(0, round(extract(epoch from (new.completed_at - new.created_at)) / 60.0))::int;
    end if;
  end if;
  return new;
end $$;

drop trigger if exists trg_requests_completion on requests;
create trigger trg_requests_completion before update on requests
  for each row execute function public.set_request_completion();

-- 3. request_events immutability ----------------------------------------------
-- Append-only audit trail: block UPDATE and DELETE for everyone, including
-- the service role. INSERT is unaffected.
create or replace function public.block_request_events_mutation()
returns trigger language plpgsql as $$
begin
  raise exception 'request_events is append-only: % is not permitted', tg_op
    using errcode = 'check_violation';
end $$;

drop trigger if exists trg_request_events_no_update on request_events;
create trigger trg_request_events_no_update before update on request_events
  for each row execute function public.block_request_events_mutation();

drop trigger if exists trg_request_events_no_delete on request_events;
create trigger trg_request_events_no_delete before delete on request_events
  for each row execute function public.block_request_events_mutation();
