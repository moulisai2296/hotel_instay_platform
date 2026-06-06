-- =============================================================================
-- InStayOS — Migration 0002: Tables (12)
-- Created in FK-dependency order. Idempotent via "create table if not exists".
-- Every table carries hotel_id (except hotels itself) per multi-tenancy rule.
-- =============================================================================

-- 1. hotels — root tenant entity ----------------------------------------------
create table if not exists hotels (
  id                uuid primary key default gen_random_uuid(),
  name              text not null,
  slug              text not null unique,
  logo_url          text,
  address           text,
  city              text,
  country           text,
  total_rooms       integer,
  property_type     text,                          -- luxury/boutique/resort/business
  timezone          text,                          -- e.g. Asia/Kolkata
  is_active         boolean not null default true,
  subscription_tier text,                          -- basic/pro/enterprise
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

-- 2. departments --------------------------------------------------------------
create table if not exists departments (
  id                  uuid primary key default gen_random_uuid(),
  hotel_id            uuid not null references hotels(id) on delete cascade,
  type                department_type not null,
  display_name        text,
  is_active           boolean not null default true,
  working_hours_start time,
  working_hours_end   time,
  created_at          timestamptz not null default now()
);

-- 3. rooms --------------------------------------------------------------------
create table if not exists rooms (
  id            uuid primary key default gen_random_uuid(),
  hotel_id      uuid not null references hotels(id) on delete cascade,
  room_number   text not null,                     -- "412", "PH1"
  room_type     text,                              -- standard/deluxe/suite/penthouse
  floor         integer,
  max_occupancy integer,
  pms_room_id   text,                              -- external PMS reference
  is_active     boolean not null default true,
  created_at    timestamptz not null default now()
);

-- 4. tablets ------------------------------------------------------------------
create table if not exists tablets (
  id            uuid primary key default gen_random_uuid(),
  hotel_id      uuid not null references hotels(id) on delete cascade,
  tablet_code   text not null,                     -- "TAB-001", unique per hotel
  location_name text not null,                     -- "Pool Area", "Lobby", "Room 412"
  location_type text,                              -- in_room/common_area
  room_id       uuid references rooms(id) on delete set null,  -- only if in_room
  status        tablet_status not null default 'offline',
  last_ping_at  timestamptz,
  device_info   jsonb,                             -- {model, os_version, app_version}
  is_active     boolean not null default true,
  created_at    timestamptz not null default now(),
  unique (hotel_id, tablet_code)
);

-- 5. users (fast-authkit extended) --------------------------------------------
-- Staff/managers/admins only. Guests live in guest_sessions.
create table if not exists users (
  id              uuid primary key default gen_random_uuid(),
  email           text not null unique,
  hashed_password text,
  role            staff_role,
  is_active       boolean not null default true,
  display_name    text not null,
  hotel_id        uuid references hotels(id) on delete cascade,    -- NULL for super-admin
  department_id   uuid references departments(id) on delete set null, -- NULL for managers
  avatar_url      text,
  last_seen_at    timestamptz,
  created_at      timestamptz not null default now()
);

-- 6. guest_sessions — one per guest stay; custom PIN auth lives here ----------
create table if not exists guest_sessions (
  id                 uuid primary key default gen_random_uuid(),
  hotel_id           uuid not null references hotels(id) on delete cascade,
  room_id            uuid not null references rooms(id) on delete restrict,
  guest_name         text not null,
  guest_email        text,
  guest_phone        text,
  nationality        text,                         -- ISO code
  pin_hash           text not null,                -- bcrypt(6-digit PIN)
  checkin_date       date not null,
  checkout_date      date not null,
  num_guests         integer not null default 1,
  pms_booking_id     text,
  is_checked_out     boolean not null default false,
  satisfaction_score smallint check (satisfaction_score between 1 and 5),
  session_token      text,                         -- JWT after PIN verified
  token_expires_at   timestamptz,                  -- expires at checkout EOD
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

-- 7. requests (CORE) ----------------------------------------------------------
create table if not exists requests (
  id                   uuid primary key default gen_random_uuid(),
  hotel_id             uuid not null references hotels(id) on delete cascade,        -- denormalized for fast RLS
  guest_session_id     uuid not null references guest_sessions(id) on delete cascade,
  room_id              uuid not null references rooms(id) on delete restrict,         -- denormalized for fast query
  department_id        uuid not null references departments(id) on delete restrict,   -- AI classified
  assigned_to          uuid references users(id) on delete set null,                  -- NULL if unassigned
  tablet_id            uuid references tablets(id) on delete set null,                -- origin tablet
  raw_input            text not null,                 -- original guest message
  input_mode           input_mode,
  voice_url            text,                          -- storage URL if voice
  ai_title             text,                          -- "Extra towels x2"
  ai_items             jsonb,                         -- [{item:"towel", qty:2}]
  ai_priority_reason   text,
  status               request_status not null default 'pending',
  priority             request_priority not null default 'medium',
  sentiment_score      double precision,              -- -1.0 to 1.0
  location_context     text,                          -- "Pool Area tablet"
  staff_notes          text,
  completed_at         timestamptz,
  resolution_time_mins integer,                        -- computed on complete
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now()
);

-- 8. request_events — IMMUTABLE append-only audit trail -----------------------
create table if not exists request_events (
  id          uuid primary key default gen_random_uuid(),
  request_id  uuid not null references requests(id) on delete cascade,
  hotel_id    uuid not null references hotels(id) on delete cascade,  -- denormalized for RLS
  actor_type  text not null,                          -- guest/staff/system/ai
  actor_id    uuid,                                   -- user.id or guest_session.id
  event_type  text not null,                          -- created/assigned/status_changed/escalated/note_added/completed
  from_status request_status,
  to_status   request_status,
  note        text,
  metadata    jsonb,                                  -- {assigned_to_name:"Priya"}
  created_at  timestamptz not null default now()
);

-- 9. offers -------------------------------------------------------------------
create table if not exists offers (
  id             uuid primary key default gen_random_uuid(),
  hotel_id       uuid not null references hotels(id) on delete cascade,
  title          text not null,
  description    text,
  image_url      text,
  discount_pct   smallint check (discount_pct between 0 and 100),
  original_price numeric(10,2),
  valid_from     timestamptz,
  valid_until    timestamptz,
  status         offer_status not null default 'active',
  created_at     timestamptz not null default now()
);

-- 10. guest_interactions — full AI chat history -------------------------------
create table if not exists guest_interactions (
  id               uuid primary key default gen_random_uuid(),
  hotel_id         uuid not null references hotels(id) on delete cascade,
  guest_session_id uuid not null references guest_sessions(id) on delete cascade,
  role             text not null,                    -- guest/assistant
  content          text not null,
  input_mode       input_mode,
  request_id       uuid references requests(id) on delete set null,
  sentiment_score  double precision,
  created_at       timestamptz not null default now()
);

-- 11. pms_connections — one per hotel -----------------------------------------
create table if not exists pms_connections (
  id               uuid primary key default gen_random_uuid(),
  hotel_id         uuid not null unique references hotels(id) on delete cascade,
  provider         pms_provider not null,
  api_key_encrypted text,                            -- AES-256 encrypted at rest
  api_endpoint     text,
  is_connected     boolean not null default false,
  last_sync_at     timestamptz,
  last_sync_status text,                             -- success/failed/partial
  sync_config      jsonb,                            -- {auto_sync, interval_mins}
  created_at       timestamptz not null default now()
);

-- 12. notifications -----------------------------------------------------------
create table if not exists notifications (
  id           uuid primary key default gen_random_uuid(),
  hotel_id     uuid not null references hotels(id) on delete cascade,
  recipient_id uuid not null references users(id) on delete cascade,
  type         text not null,                        -- new_request/escalation/overdue/sentiment_alert/assignment
  title        text not null,
  body         text,
  reference_id uuid,                                  -- request_id or guest_session_id
  is_read      boolean not null default false,
  created_at   timestamptz not null default now()
);
