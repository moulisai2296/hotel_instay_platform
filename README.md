<div align="center">

# InStayOS

### The in-stay guest experience your guests remember.

**InStayOS** is a multi-role, AI-powered hotel in-stay platform. It turns every
guest request into instant action — and every interaction into insight — from
check-in to checkout, on the guest's own phone.

</div>

---

## ✨ What it does

| For… | They get |
|------|----------|
| **Guests** | An AI concierge on their own phone (chat **and** voice), live request tracking, the hotel guide, offers, and checkout — no app store, no tablet. |
| **Staff** | A live, real-time queue of requests for their department — picked up and completed in a tap. |
| **Managers** | A live hotel overview: active requests, department load, response times, escalations and alerts. |
| **Admins** | One-screen guest check-in (room + auto-generated PIN), in-house guests, and the team roster. |

### The guest journey becomes data
Every request, message, sentiment signal and response time is captured across the
stay — giving you a structured picture of the **whole guest journey** (resolution
time per department, sentiment trend, offer uptake) so you can see where you
delight or disappoint, and act before checkout.

## 🧠 How it works

- **AI concierge** — guests ask in plain language; an intent-gated AI classifies
  each turn (real request vs. needs-more-info vs. off-topic) **before** any write,
  routes it to the right department, and replies instantly. Voice notes are
  transcribed and handled the same way.
- **Real-time ops** — staff/manager boards read live from the database (row-level
  security scopes what each role sees) and update over Supabase Realtime.
- **Mobile-first guest auth** — guests open `/(hotel)/h/{slug}`, enter their room
  number + 6-digit PIN, and get a short-lived session that expires at checkout.

## 🛠 Tech stack

- **Frontend** — Next.js 14 (App Router), TypeScript, Tailwind + shadcn/ui,
  Framer Motion, Zustand, React Query
- **Backend** — FastAPI (Python 3.11+), Pydantic v2, SQLAlchemy async
- **Data** — Supabase (PostgreSQL + Row Level Security + Realtime)
- **AI** — LangChain (provider-agnostic; default Google Gemini) · Deepgram (voice)
- **Auth** — fast-authkit (staff) + a custom PIN flow (guests)

## 📂 Monorepo

```
apps/
  web/      Next.js frontend (guest app, staff/manager/admin, marketing landing)
  api/      FastAPI backend (auth, guest, requests + AI, staff/manager writes)
docs/       API.md (source of truth), PRD, SCHEMA, FLOWS, BUGFIXES, Postman
supabase/   SQL migrations (schema, RLS, realtime)
```

## 🚀 Quickstart

**Backend**
```bash
cd apps/api
uv sync
cp .env.example .env          # add Supabase DB URL, AUTHKIT_SECRET_KEY, GEMINI/DEEPGRAM keys
uv run uvicorn main:app --reload --port 8000
uv run pytest -q              # 56 tests, DB-free
```

**Frontend**
```bash
cd apps/web
cp .env.example .env.local    # NEXT_PUBLIC_API_BASE_URL + Supabase URL/anon key
npm install
npm run dev                   # http://localhost:3000
```

| Route | Surface |
|-------|---------|
| `/` | Landing router (guest vs. staff) |
| `/landing` | Marketing site |
| `/h/{slug}` | Guest app (PIN → home → chat → requests → guide → offers → checkout) |
| `/login` → `/dashboard` `/manager` `/admin` | Staff / manager / admin |

## 📖 Docs

- **[docs/API.md](docs/API.md)** — API reference (REST + direct-from-Supabase reads) — the UI's source of truth
- **[docs/InStayOS.postman_collection.json](docs/InStayOS.postman_collection.json)** — runnable Postman collection
- **[docs/BUGFIXES.md](docs/BUGFIXES.md)** — running log of bugs & fixes
- **[CLAUDE.md](CLAUDE.md)** — architecture & conventions

## 🗺 Roadmap

Tablets & PMS integration (Cloudbeds/Mews) · hotel onboarding/provisioning ·
amenities-backed hotel guide · persisted guest ratings · product demo video ·
deployment (Vercel + Railway) & CI/CD.

<div align="center"><sub>InStayOS · Your stay, your way.</sub></div>
