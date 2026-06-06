# InStayOS — Product Requirements Document (PRD)

## Product Vision
InStayOS is an AI-powered in-stay guest experience platform that tracks the complete
guest journey from check-in to checkout. Guests interact via AI chat or voice notes
on tablets placed throughout the hotel. All requests are auto-classified and routed
to the correct department. Staff, managers, and admins get real-time dashboards.

## Problem Statement
Hotels invest heavily in pre-arrival booking systems but have no unified system to
track the guest journey during their stay. Requests are fragmented across walkie-talkies,
WhatsApp groups, paper logs, and phone calls. Staff have zero context when a guest calls.
Guest sentiment is invisible until a bad review appears post-checkout.

## Target Users

### Primary
- Mid-scale independent hotels (50–200 rooms)
- Willing to pay $3–10/room/month SaaS subscription
- Currently using fragmented tools (WhatsApp, walkie-talkies, paper logs)

### Roles Within Product
| Role | Description |
|---|---|
| Guest | Hotel guest during their stay |
| Staff | Department-level (housekeeping, F&B, maintenance, concierge, spa, front desk) |
| Dept Manager | Manages one department's queue and staff |
| Hotel Manager | Full visibility across all departments + analytics |
| Admin | Super-admin — manages hotels, users, configuration, PMS |

## Core Features

### Guest App (Tablet / Web)
- PIN login (6-digit, bcrypt hashed, auto-issued at check-in)
- AI concierge chat (Gemini Pro) — text or voice note (Deepgram)
- Intent classification → auto-routes to correct department
- Real-time request tracker (status: pending → in progress → done)
- Hotel guide (amenities, hours, info)
- Exclusive offers (claim during stay)
- Checkout screen (bill summary, rate stay, luggage/taxi request)

### Staff Dashboard (Web)
- Role-based login (email + password via fast-authkit)
- Live request queue (Kanban: New / In Progress / Completed)
- Request detail slide-over (AI-extracted items, timeline, assign, complete, escalate)
- Completed log with resolution time stats

### Manager Dashboard (Web)
- All-departments overview (color-coded status cards)
- Guest journey timeline (every interaction per guest)
- Alerts & escalations (overdue, sentiment flags, understaffing)
- Analytics (request volume, resolution time trends, satisfaction scores)
- Sentiment monitor (heatmap by room/day)

### Admin Panel (Web)
- User management (add, edit, deactivate staff)
- Role & permissions matrix (toggle-based)
- Tablet & location config (register tablets, assign locations)
- Hotel setup (name, rooms, departments, timezone)
- PMS integration (Cloudbeds, Mews, Opera, Apaleo — API key config + sync logs)

## User Flows

### Guest Request Flow
1. Guest enters PIN on tablet → verified against guest_sessions.pin_hash
2. Guest types or records voice note in AI chat
3. Voice → Deepgram → text transcription
4. Text → Gemini Pro → intent classified → department assigned → priority set → items extracted
5. Request written to Supabase requests table
6. Supabase Realtime → staff kanban updates instantly
7. Staff assigns + marks in progress → request_event logged
8. Supabase Realtime → guest tracker updates
9. Staff marks complete → completion time logged
10. Guest sees "Done" in their request tracker

### Hotel Login Flow
1. User visits /auth/login → selects role (visual only, actual role from DB)
2. Email + password → fast-authkit /auth/login → JWT in HTTP-only cookie
3. JWT decoded → role + hotel_id extracted → routed to correct dashboard
4. Hotel isolation middleware verifies hotel_id on every subsequent request

## Non-Functional Requirements
- Real-time latency: < 500ms for request status updates (Supabase Realtime)
- AI response time: < 3 seconds for chat responses (Gemini Pro)
- Voice transcription: < 2 seconds for average 15-second note (Deepgram)
- Uptime: 99.5% (Vercel + Railway SLAs)
- Mobile-responsive: All dashboards work on tablet and desktop
- Multi-tenancy: hotel_id isolation enforced at DB (RLS) + API (middleware) levels
- Data privacy: Guest PII never exposed to staff below manager level

## Business Model
- SaaS subscription: $3–10/room/month (tiered: Basic / Pro / Enterprise)
- Basic: Guest app + staff queue
- Pro: + Manager analytics + sentiment + guest journey
- Enterprise: + PMS integration + multi-property + custom branding
- Domain: Customer buys own domain, InStayOS deployed on their subdomain or whitelabeled

## Out of Scope (v1)
- Native iOS / Android apps (web-first, tablet browser)
- Payment processing within the app
- Direct OTA / booking engine integration
- Multi-language guest UI (English only v1)
- Push notifications (in-app notifications only v1)
