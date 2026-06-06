# InStayOS — Database Schema Reference

## Supabase (PostgreSQL) — 12 Tables

### Enums (create first)
```sql
CREATE TYPE staff_role AS ENUM ('staff','dept_manager','hotel_manager','admin');
CREATE TYPE department_type AS ENUM ('housekeeping','fb','maintenance','concierge','spa','front_desk');
CREATE TYPE request_status AS ENUM ('pending','assigned','in_progress','completed','escalated','cancelled');
CREATE TYPE request_priority AS ENUM ('low','medium','high','urgent');
CREATE TYPE input_mode AS ENUM ('text','voice','chip');
CREATE TYPE tablet_status AS ENUM ('online','offline','maintenance');
CREATE TYPE offer_status AS ENUM ('active','expired','claimed');
CREATE TYPE pms_provider AS ENUM ('cloudbeds','mews','opera','apaleo','manual');
```

### Table: hotels
Root entity. Every other table references this via hotel_id.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | gen_random_uuid() |
| name | text NN | Hotel display name |
| slug | text NN UNIQUE IDX | URL-safe e.g. grand-horizon |
| logo_url | text | Supabase Storage URL |
| address | text | |
| city | text | |
| country | text | |
| total_rooms | integer | |
| property_type | text | luxury/boutique/resort/business |
| timezone | text | e.g. Asia/Kolkata |
| is_active | boolean | default true |
| subscription_tier | text | basic/pro/enterprise |
| created_at | timestamptz | default now() |
| updated_at | timestamptz | auto-trigger |

### Table: departments
Active departments per hotel. Configurable by admin.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| hotel_id | uuid FK NN IDX | → hotels.id |
| type | department_type NN | enum |
| display_name | text | Custom override |
| is_active | boolean | default true |
| working_hours_start | time | e.g. 08:00 |
| working_hours_end | time | e.g. 22:00 |
| created_at | timestamptz | |

### Table: users (fast-authkit extended)
Staff, managers, admins only. Guests are in guest_sessions.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | from BaseUserMixin |
| email | text NN UNIQUE IDX | from BaseUserMixin |
| hashed_password | text | from BaseUserMixin |
| role | staff_role | from BaseUserMixin, typed as enum |
| is_active | boolean | from BaseUserMixin |
| display_name | text NN | ✦ Extended |
| hotel_id | uuid FK IDX | ✦ Extended → hotels.id. NULL for super-admin |
| department_id | uuid FK | ✦ Extended → departments.id. NULL for managers |
| avatar_url | text | ✦ Extended |
| last_seen_at | timestamptz | ✦ Extended |
| created_at | timestamptz | from BaseUserMixin |

### Table: rooms
All rooms. Synced from PMS or manually added.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| hotel_id | uuid FK NN IDX | → hotels.id |
| room_number | text NN IDX | e.g. "412", "PH1" |
| room_type | text | standard/deluxe/suite/penthouse |
| floor | integer | |
| max_occupancy | integer | |
| pms_room_id | text IDX | External PMS reference |
| is_active | boolean | default true |
| created_at | timestamptz | |

### Table: guest_sessions
One record per guest stay. Custom PIN auth lives here.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| hotel_id | uuid FK NN IDX | → hotels.id |
| room_id | uuid FK NN IDX | → rooms.id |
| guest_name | text NN | |
| guest_email | text | Optional |
| guest_phone | text | Optional |
| nationality | text | ISO code |
| pin_hash | text NN | bcrypt(6-digit PIN) |
| checkin_date | date NN | |
| checkout_date | date NN | |
| num_guests | integer | default 1 |
| pms_booking_id | text IDX | External reference |
| is_checked_out | boolean | default false |
| satisfaction_score | smallint | 1–5 from checkout |
| session_token | text IDX | JWT after PIN verified |
| token_expires_at | timestamptz | Expires at checkout EOD |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### Table: requests (CORE)
Every guest request. The most important table.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| hotel_id | uuid FK NN IDX | Denormalized for fast RLS |
| guest_session_id | uuid FK NN IDX | → guest_sessions.id |
| room_id | uuid FK NN IDX | Denormalized for fast query |
| department_id | uuid FK NN IDX | → departments.id. AI classified. |
| assigned_to | uuid FK IDX | → users.id. NULL if unassigned. |
| tablet_id | uuid FK | → tablets.id. Origin tablet. |
| raw_input | text NN | Original guest message |
| input_mode | input_mode | text/voice/chip |
| voice_url | text | Storage URL if voice |
| ai_title | text | "Extra towels ×2" |
| ai_items | jsonb | [{item: "towel", qty: 2}] |
| ai_priority_reason | text | Why this priority |
| status | request_status NN IDX | default pending |
| priority | request_priority NN | default medium |
| sentiment_score | float | -1.0 to 1.0 |
| location_context | text | "Pool Area tablet" |
| staff_notes | text | Internal notes |
| completed_at | timestamptz IDX | |
| resolution_time_mins | integer | Computed on complete |
| created_at | timestamptz NN IDX | |
| updated_at | timestamptz | |

### Table: request_events
Immutable audit trail. Powers guest tracker + guest journey timeline.
NEVER UPDATE OR DELETE rows in this table.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| request_id | uuid FK NN IDX | → requests.id |
| hotel_id | uuid FK NN IDX | Denormalized for RLS |
| actor_type | text NN | guest/staff/system/ai |
| actor_id | uuid | user.id or guest_session.id |
| event_type | text NN | created/assigned/status_changed/escalated/note_added/completed |
| from_status | request_status | Previous status |
| to_status | request_status | New status |
| note | text | Optional human note |
| metadata | jsonb | e.g. {assigned_to_name: "Priya"} |
| created_at | timestamptz NN IDX | IMMUTABLE |

### Table: tablets
Registered tablets across the hotel.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| hotel_id | uuid FK NN IDX | → hotels.id |
| tablet_code | text NN IDX | e.g. TAB-001. Unique per hotel. |
| location_name | text NN | "Pool Area", "Lobby", "Room 412" |
| location_type | text | in_room/common_area |
| room_id | uuid FK | → rooms.id. Only if in_room. |
| status | tablet_status | online/offline/maintenance |
| last_ping_at | timestamptz | Heartbeat |
| device_info | jsonb | {model, os_version, app_version} |
| is_active | boolean | default true |
| created_at | timestamptz | |

### Table: offers
Hotel offers shown to guests during stay.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| hotel_id | uuid FK NN IDX | → hotels.id |
| title | text NN | |
| description | text | |
| image_url | text | Supabase Storage |
| discount_pct | smallint | 0–100 |
| original_price | numeric(10,2) | |
| valid_from | timestamptz | |
| valid_until | timestamptz | |
| status | offer_status | active/expired/claimed |
| created_at | timestamptz | |

### Table: guest_interactions
Full AI chat history per guest session.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| hotel_id | uuid FK NN IDX | Denormalized |
| guest_session_id | uuid FK NN IDX | → guest_sessions.id |
| role | text NN | guest/assistant |
| content | text NN | Message text |
| input_mode | input_mode | text/voice/chip |
| request_id | uuid FK | → requests.id if created a request |
| sentiment_score | float | AI scored per message |
| created_at | timestamptz NN IDX | |

### Table: pms_connections
PMS integration config per hotel.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| hotel_id | uuid FK NN IDX UNIQUE | One per hotel |
| provider | pms_provider NN | |
| api_key_encrypted | text | AES-256 encrypted |
| api_endpoint | text | PMS API base URL |
| is_connected | boolean | default false |
| last_sync_at | timestamptz | |
| last_sync_status | text | success/failed/partial |
| sync_config | jsonb | {auto_sync, interval_mins} |
| created_at | timestamptz | |

### Table: notifications
In-app notifications. Drives alert bell in topbar.
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| hotel_id | uuid FK NN IDX | → hotels.id |
| recipient_id | uuid FK NN IDX | → users.id |
| type | text NN | new_request/escalation/overdue/sentiment_alert/assignment |
| title | text NN | Short notification title |
| body | text | Full text |
| reference_id | uuid | request_id or guest_session_id |
| is_read | boolean | default false |
| created_at | timestamptz NN IDX | |

## RLS Summary
- All tables: hotel_id filter enforced
- guest_sessions: guests see own only, staff see guest_name + room only
- requests: staff see own dept only, managers see all in hotel
- notifications: users see own only
- pms_connections: api_key masked from non-admin
- request_events: append-only, no update/delete

## Supabase Realtime — Enable On
- requests, request_events, notifications, tablets

## Indexes — Critical For Performance
- All hotel_id columns
- requests: status, department_id, created_at, assigned_to
- guest_sessions: room_id, is_checked_out
- request_events: request_id, created_at
- notifications: recipient_id, is_read
