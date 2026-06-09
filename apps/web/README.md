# InStayOS — Web (Next.js 14)

Frontend for the InStayOS in-stay guest experience platform. App Router,
Tailwind + shadcn/ui, Framer Motion, Zustand, React Query.

## Setup

```bash
cp .env.example .env.local   # fill in API + Supabase values
npm install
npm run dev                  # http://localhost:3000
```

The FastAPI backend (`../api`) must be running at `NEXT_PUBLIC_API_BASE_URL`.

## Architecture

- **`lib/api-client.ts`** — the single entry point for all REST calls (writes +
  AI/aggregation). Never `fetch` directly in components.
- **`lib/supabase.ts`** — direct "my rows" reads + realtime via the anon key,
  authenticated with the app JWT for RLS (see `docs/API.md` §6).
- **`stores/`** — Zustand auth: `guest-store` (PIN session, sessionStorage only)
  and `staff-store` (email/password). React Query owns server-state caching.
- **Theming** — light = staff/manager/admin; dark (`.dark`) = guest app. Tokens
  live in `app/globals.css` + `tailwind.config.ts`.

## Routes (this release — foundation + auth)

| Route | Purpose |
|---|---|
| `/` | Landing router (guest vs. staff) |
| `/stay` | Guest hotel-code entry (fallback to room QR) |
| `/h/[slug]` | Guest PIN login (room + 6-digit PIN) |
| `/h/[slug]/home` | Authed guest home (placeholder → full app in PR 2) |
| `/login` | Staff / manager / admin login |
| `/dashboard` | Authed staff landing (placeholder → role dashboards in PR 3) |

Source of truth for the API: [`docs/API.md`](../../docs/API.md).
