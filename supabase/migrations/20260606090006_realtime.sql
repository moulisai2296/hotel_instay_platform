-- =============================================================================
-- InStayOS — Migration 0006: Supabase Realtime
-- Enable Realtime ONLY on: requests, request_events, notifications, tablets.
-- REPLICA IDENTITY FULL so UPDATE/DELETE payloads carry old-row values
-- (needed for client-side filters like department_id / recipient_id).
-- Idempotent: add-to-publication guarded against duplicates.
-- =============================================================================

alter table requests       replica identity full;
alter table request_events replica identity full;
alter table notifications  replica identity full;
alter table tablets        replica identity full;

do $$
declare
  t text;
begin
  -- The supabase_realtime publication exists by default on Supabase projects.
  if not exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    create publication supabase_realtime;
  end if;

  foreach t in array array['requests','request_events','notifications','tablets'] loop
    if not exists (
      select 1 from pg_publication_tables
      where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = t
    ) then
      execute format('alter publication supabase_realtime add table public.%I', t);
    end if;
  end loop;
end $$;
