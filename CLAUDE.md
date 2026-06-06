# InStayOS — Claude Code Instructions

## Project Overview
InStayOS is a multi-role, AI-powered hotel in-stay guest experience SaaS platform.
It tracks the complete guest journey from check-in to checkout via an AI chat/voice interface,
and gives hotel staff, managers, and admins real-time operational dashboards.

## Tech Stack — Non-Negotiable
- **Frontend**: Next.js 14 (App Router), Tailwind CSS, shadcn/ui, Framer Motion, Zustand
- **Backend**: FastAPI (Python 3.11+), Pydantic v2, SQLAlchemy async
- **Auth**: fast-authkit (PyPI: fast-authkit==0.1.3) for staff/manager/admin. Custom PIN flow for guests.
- **Database**: Supabase (PostgreSQL), Row Level Security enabled on all tables
- **Realtime**: Supabase Realtime on: requests, request_events, notifications, tablets
- **AI Chat**: Google Gemini Pro API (gemini-1.5-pro) — provider-agnostic abstraction layer
- **Voice**: Deepgram API — speech-to-text for guest voice notes
- **Storage**: Supabase Storage — voice audio files, hotel logos, offer images
- **Deployment**: Frontend → Vercel, Backend → Railway, Domain → Cloudflare DNS

## Monorepo Structure
```
instayos/
├── CLAUDE.md                    # This file
├── .env.example                 # Environment variable template
├── apps/
│   ├── web/                     # Next.js 14 frontend
│   │   ├── app/                 # App Router pages
│   │   │   ├── (guest)/         # Guest-facing routes
│   │   │   ├── (staff)/         # Staff dashboard routes
│   │   │   ├── (manager)/       # Manager dashboard routes
│   │   │   ├── (admin)/         # Admin panel routes
│   │   │   └── auth/            # Login / PIN entry routes
│   │   ├── components/          # Shared UI components
│   │   │   ├── ui/              # shadcn/ui base components
│   │   │   ├── guest/           # Guest-specific components
│   │   │   ├── staff/           # Staff-specific components
│   │   │   ├── manager/         # Manager-specific components
│   │   │   └── admin/           # Admin-specific components
│   │   ├── lib/                 # Utilities, supabase client, api client
│   │   ├── stores/              # Zustand state stores
│   │   ├── hooks/               # Custom React hooks
│   │   └── types/               # TypeScript type definitions
│   └── api/                     # FastAPI backend
│       ├── main.py              # FastAPI app entry point
│       ├── auth/                # fast-authkit setup + guest PIN auth
│       ├── routers/             # API route modules
│       │   ├── guest.py         # Guest session, PIN verify
│       │   ├── requests.py      # Request CRUD + AI routing
│       │   ├── staff.py         # Staff operations
│       │   ├── manager.py       # Manager views + analytics
│       │   ├── admin.py         # Admin user/hotel management
│       │   ├── ai.py            # Gemini chat + Deepgram voice
│       │   └── pms.py           # PMS integration (Cloudbeds, Mews)
│       ├── services/            # Business logic layer
│       │   ├── ai_service.py    # Provider-agnostic AI abstraction
│       │   ├── voice_service.py # Deepgram integration
│       │   ├── request_service.py
│       │   ├── notification_service.py
│       │   └── pms_service.py
│       ├── models/              # SQLAlchemy models
│       ├── schemas/             # Pydantic v2 schemas
│       ├── middleware/          # hotel_id isolation, rate limiting
│       └── utils/               # Encryption, helpers
├── packages/
│   └── shared-types/            # Shared TypeScript types (optional)
└── docs/
    ├── PRD.md
    ├── SCHEMA.md
    ├── API.md
    └── FLOWS.md
└── ui_prototypes/
    ├── instayos_guest_prototype.html
    ├── instayos_landing_router.html
    └──instayos_staff_manager_admin.html

```

## Coding Standards — Always Follow

### Python / FastAPI
- Python 3.11+, type hints everywhere, no untyped functions
- Pydantic v2 models for all request/response schemas
- Async everywhere — use `async def` for all route handlers and services
- Never hardcode secrets — always use environment variables via `os.getenv()`
- Never store raw API keys — encrypt with AES-256 before writing to DB
- Use SQLAlchemy async sessions, never sync
- All routes must have role guard via fast-authkit dependency injection
- Hotel isolation middleware on every route that touches hotel data
- Return consistent error format: `{"error": "message", "code": "ERROR_CODE"}`

### TypeScript / Next.js
- TypeScript strict mode — no `any` types
- Use App Router, not Pages Router
- Server Components by default, Client Components only when needed (interactivity)
- All API calls go through `/lib/api-client.ts` — never fetch directly in components
- Zustand for global state, React Query (TanStack) for server state/caching
- Never expose Supabase service role key to frontend — only anon key
- All forms use React Hook Form + Zod validation

### General
- All database writes go through FastAPI — never write directly from Next.js to Supabase
- Read-only queries (SELECT) can use Supabase client directly from Next.js (with RLS)
- Every table has hotel_id — always filter by it
- Never log sensitive data (PINs, passwords, API keys, guest PII)
- All timestamps in UTC, display in hotel timezone

## Authentication Flow

### Hotel Staff / Manager / Admin
- Email + password login via fast-authkit `/auth/login`
- JWT in HTTP-only cookie (web) or Bearer header (API)
- Role from `users.role` enum: staff | dept_manager | hotel_manager | admin
- hotel_id from `users.hotel_id` — enforced on every request via middleware

### Guest (Custom PIN Flow)
- Guest enters 6-digit PIN on tablet
- POST `/guest/verify-pin` → FastAPI verifies bcrypt hash against `guest_sessions.pin_hash`
- Returns short-lived JWT (expires at checkout date)
- Guest JWT contains: session_id, hotel_id, room_id, guest_name
- Store in memory / sessionStorage only — never localStorage

## AI Layer Architecture (Provider-Agnostic)

```python
# services/ai_service.py — always use this abstraction
class AIService:
    async def classify_intent(self, text: str, hotel_context: dict) -> IntentResult
    async def chat_response(self, messages: list, hotel_context: dict) -> str
    async def analyze_sentiment(self, text: str) -> float  # -1.0 to 1.0
    async def extract_items(self, text: str) -> list[dict]

# Current provider: Gemini Pro
# To swap provider: only change the implementation inside AIService
# Never call Gemini/Claude/OpenAI directly from routes — always via AIService
```

## Supabase Realtime Subscriptions
Enable realtime on these tables ONLY:
- `requests` — staff kanban board live updates
- `request_events` — guest request tracker live status
- `notifications` — alert bell count
- `tablets` — online/offline status

## Environment Variables Required
```
# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=     # Backend only, never expose to frontend

# fast-authkit
AUTHKIT_SECRET_KEY=
AUTHKIT_DATABASE_URL=          # Supabase postgres connection string

# AI
GEMINI_API_KEY=
DEEPGRAM_API_KEY=

# Encryption
AES_ENCRYPTION_KEY=            # For PMS API keys at rest

# Railway (backend URL)
API_BASE_URL=

# Frontend
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_BASE_URL=
```

## Build Order (Follow This Sequence)
1. Supabase schema + enums + RLS policies
2. FastAPI project setup + fast-authkit integration + User model extension
3. Hotel isolation middleware + rate limiting
4. Guest PIN auth custom flow
5. AI service abstraction (Gemini + Deepgram)
6. Request creation + AI classification endpoint
7. Supabase Realtime setup
8. Next.js — landing + auth screens
9. Next.js — Guest app (PIN → home → chat → requests → guide → offers → checkout)
10. Next.js — Staff dashboard (kanban, request detail panel)
11. Next.js — Manager dashboard (overview, guest journey, alerts, analytics)
12. Next.js — Admin panel (users, roles, tablets, hotel setup, PMS)
13. Vercel + Railway deployment config
14. GitHub Actions CI/CD

## UI/UX Design System
- **Colors**: Navy #0F1E3C (primary), Gold #C9A84C (accent), Stone #F2EDE8 (background)
- **Font**: DM Sans (UI), Playfair Display (guest headings only)
- **Components**: shadcn/ui base + custom hospitality components
- **Guest app**: Dark mode (navy bg, gold accents)
- **Staff/Manager/Admin**: Light mode (white/stone bg, navy text)
- **Animations**: Framer Motion — slide panels, screen transitions, chat bubbles
- Prototype reference: See /ui_prototypes

## Do Not Do
- Do NOT use Pages Router — App Router only
- Do NOT use Redux — use Zustand
- Do NOT call AI APIs directly from routes — use AIService abstraction
- Do NOT write directly to Supabase from Next.js for mutations
- Do NOT store guest PINs in plain text — always bcrypt
- Do NOT expose service role key to frontend
- Do NOT use the built-in fast-authkit admin dashboard HTML — we have our own Next.js admin panel
- Do NOT skip hotel_id on any new table you create
- Do NOT use `any` in TypeScript
- Do NOT hardcode hotel names, room numbers, or any test data in production code

