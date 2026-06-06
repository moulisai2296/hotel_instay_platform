# InStayOS — Key User Flows

## 1. Landing → Role Selection
- URL: yourdomain.com
- Two cards: "I'm a guest" → /guest/login | "Hotel staff / management" → /auth/login
- No auth required on landing page

## 2. Guest PIN Login
- URL: /guest/login (rendered on tablet)
- 6-digit PIN keypad
- POST /guest/verify-pin {pin, tablet_id}
- FastAPI: find active guest_session for this tablet's room_id + hotel_id
- Verify bcrypt(pin) against pin_hash
- Return guest JWT (expires at checkout_date 23:59)
- Redirect to /guest/home

## 3. Guest Request (Text)
- Guest types in chat input → POST /requests/create
- Body: {raw_input, input_mode: "text", tablet_id}
- FastAPI extracts hotel_id + room_id + session_id from guest JWT
- AIService.classify_intent() → department, priority, items, sentiment, title
- AIService.chat_response() → friendly confirmation message
- Write to requests + guest_interactions tables
- Write request_event (created)
- Supabase Realtime → staff kanban updates
- Return AI response to guest chat

## 4. Guest Request (Voice)
- Guest taps mic → browser MediaRecorder captures audio
- On stop: POST /ai/transcribe (multipart audio file)
- FastAPI uploads to Supabase Storage → Deepgram STT → returns text
- Same flow as text request from step 3 above
- voice_url stored on request record

## 5. Staff Updates Request
- Staff sees new card on kanban
- Clicks card → slide panel opens (request detail)
- Staff taps "Assign to me" → PATCH /requests/{id}/assign
- FastAPI: update assigned_to, status → assigned
- Write request_event (assigned)
- Supabase Realtime → guest tracker shows "Assigned"
- Staff taps "Mark complete" → PATCH /requests/{id}/complete
- FastAPI: update status → completed, set completed_at, compute resolution_time_mins
- Write request_event (completed)
- Supabase Realtime → guest tracker shows "Done ✓"

## 6. Manager Escalation Alert
- FastAPI background job checks requests older than 30 min with status != completed
- Writes notification for hotel_manager role (type: overdue)
- Supabase Realtime → manager alert bell count increments
- Manager clicks alert → guest journey timeline shown

## 7. Checkout
- Guest taps Checkout → GET /guest/bill-summary
- FastAPI returns itemized charges from PMS or manual entries
- Guest rates stay (1–5) → PATCH /guest-sessions/{id}/satisfaction
- Guest requests luggage/taxi → new request created (category: concierge)
- Guest confirms checkout → POST /guest-sessions/{id}/checkout
- is_checked_out = true, session_token invalidated

## 8. Hotel Staff Login
- POST /auth/login (fast-authkit) {email, password}
- JWT in HTTP-only cookie
- Middleware extracts role + hotel_id
- role = staff → redirect /staff/queue
- role = dept_manager → redirect /staff/queue (with broader view)
- role = hotel_manager → redirect /manager/overview
- role = admin → redirect /admin/users

## 9. Admin Creates Staff User
- POST /admin/users {email, display_name, role, hotel_id, department_id}
- FastAPI: create user via fast-authkit, send temp password email
- User appears in /admin/users table as active

## 10. PMS Sync (Cloudbeds example)
- Admin configures API key in /admin/pms → POST /pms/connect {provider, api_key}
- FastAPI encrypts api_key (AES-256) → stores in pms_connections
- Background sync job every 30 min:
  - Fetch active bookings from Cloudbeds API
  - Create/update guest_sessions for arriving guests
  - Generate PIN, bcrypt hash, store pin_hash
  - PIN sent to guest (SMS/email via PMS)
