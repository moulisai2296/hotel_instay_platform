-- =============================================================================
-- InStayOS — Migration 0003: Indexes
-- Critical for multi-tenant query performance. Idempotent.
-- =============================================================================

-- hotels: slug already UNIQUE (auto-indexed)

-- departments
create index if not exists idx_departments_hotel_id on departments (hotel_id);

-- rooms
create index if not exists idx_rooms_hotel_id    on rooms (hotel_id);
create index if not exists idx_rooms_room_number on rooms (hotel_id, room_number);
create index if not exists idx_rooms_pms_room_id on rooms (pms_room_id);

-- tablets ((hotel_id, tablet_code) already UNIQUE)
create index if not exists idx_tablets_hotel_id on tablets (hotel_id);
create index if not exists idx_tablets_room_id  on tablets (room_id);

-- users (email already UNIQUE)
create index if not exists idx_users_hotel_id      on users (hotel_id);
create index if not exists idx_users_department_id on users (department_id);

-- guest_sessions
create index if not exists idx_guest_sessions_hotel_id      on guest_sessions (hotel_id);
create index if not exists idx_guest_sessions_room_id       on guest_sessions (room_id);
create index if not exists idx_guest_sessions_is_checkedout on guest_sessions (hotel_id, is_checked_out);
create index if not exists idx_guest_sessions_pms_booking   on guest_sessions (pms_booking_id);
create index if not exists idx_guest_sessions_token         on guest_sessions (session_token);

-- requests (hot path — index every filter/sort column)
create index if not exists idx_requests_hotel_id      on requests (hotel_id);
create index if not exists idx_requests_session_id    on requests (guest_session_id);
create index if not exists idx_requests_room_id       on requests (room_id);
create index if not exists idx_requests_department_id on requests (department_id);
create index if not exists idx_requests_assigned_to   on requests (assigned_to);
create index if not exists idx_requests_status        on requests (hotel_id, status);
create index if not exists idx_requests_created_at    on requests (created_at desc);
create index if not exists idx_requests_completed_at  on requests (completed_at);

-- request_events
create index if not exists idx_request_events_request_id on request_events (request_id);
create index if not exists idx_request_events_hotel_id   on request_events (hotel_id);
create index if not exists idx_request_events_created_at on request_events (created_at);

-- offers
create index if not exists idx_offers_hotel_id on offers (hotel_id);

-- guest_interactions
create index if not exists idx_guest_interactions_hotel_id   on guest_interactions (hotel_id);
create index if not exists idx_guest_interactions_session_id on guest_interactions (guest_session_id);
create index if not exists idx_guest_interactions_created_at on guest_interactions (created_at);

-- pms_connections (hotel_id already UNIQUE)

-- notifications
create index if not exists idx_notifications_hotel_id     on notifications (hotel_id);
create index if not exists idx_notifications_recipient_id on notifications (recipient_id);
create index if not exists idx_notifications_is_read      on notifications (recipient_id, is_read);
create index if not exists idx_notifications_created_at   on notifications (created_at desc);
