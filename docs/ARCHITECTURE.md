# InStayOS — Architecture Reference

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                          │
│  Guest Tablet (browser)  │  Staff/Mgr/Admin (browser)  │
└────────────┬─────────────────────────┬───────────────────┘
             │                         │
             ▼                         ▼
┌─────────────────────────────────────────────────────────┐
│              Next.js 14 Frontend (Vercel)                │
│  App Router │ Tailwind │ shadcn/ui │ Framer Motion      │
│  Zustand (global state) │ TanStack Query (server state) │
│  Supabase client (READ-only, RLS enforced)              │
└────────────┬─────────────────────────┬───────────────────┘
             │ HTTPS API calls         │ Supabase Realtime
             ▼                         ▼
┌──────────────────────┐  ┌───────────────────────────────┐
│  FastAPI (Railway)   │  │     Supabase (PostgreSQL)     │
│                      │  │                               │
│  fast-authkit JWT    │  │  12 Tables + RLS policies     │
│  Guest PIN auth      │◄─┤  Realtime subscriptions       │
│  AI Service layer    │  │  Storage (voice, images)      │
│  Request routing     │  │  Auth (service role)          │
│  Notification svc    │  │                               │
└──────┬───────┬───────┘  └───────────────────────────────┘
       │       │
       ▼       ▼
┌──────────┐ ┌──────────┐
│ Gemini   │ │Deepgram  │
│ Pro API  │ │Voice API │
│ (AI chat)│ │(STT)     │
└──────────┘ └──────────┘
```

## Request Lifecycle (Most Critical Flow)

```
Guest types/speaks
       │
       ▼
Next.js captures input
       │
       ├── voice? → upload to Supabase Storage → FastAPI /ai/transcribe
       │                                               │
       │                                          Deepgram STT
       │                                               │
       └── text input ──────────────────────────────────┤
                                                        ▼
                                             FastAPI /requests/create
                                                        │
                                                  Gemini Pro
                                              (classify intent,
                                               extract items,
                                               set priority,
                                               score sentiment)
                                                        │
                                             Write to Supabase
                                             requests table
                                                        │
                                          Supabase Realtime fires
                                                  │         │
                                                  ▼         ▼
                                           Staff kanban  Guest tracker
                                           updates live  updates live
```

## Multi-Tenancy Architecture

```
Every API request:
  1. JWT decoded → extract hotel_id + role
  2. hotel_id injected into all DB queries automatically
  3. Supabase RLS provides second enforcement layer
  4. Never trust hotel_id from request body — always from JWT

Hotel isolation dependency (FastAPI):
  def get_hotel_context(user = Depends(auth_kit.current_active_user)):
      return {"hotel_id": user.hotel_id, "role": user.role}
```

## AI Service Abstraction

```python
# Provider-agnostic — swap Gemini for Claude/GPT with zero route changes
class AIService:
    provider: str = "gemini"  # change this to swap

    async def classify_intent(text, hotel_context) -> IntentResult:
        # Returns: department, priority, items, sentiment, ai_title

    async def chat_response(messages, hotel_context) -> str:
        # Returns: friendly AI response to show guest

    async def analyze_sentiment(text) -> float:
        # Returns: -1.0 (very negative) to 1.0 (very positive)
```

## Supabase Realtime Pattern (Frontend)

```typescript
// Staff kanban — subscribe to new requests for their department
const subscription = supabase
  .channel('requests')
  .on('postgres_changes', {
    event: '*',
    schema: 'public',
    table: 'requests',
    filter: `department_id=eq.${user.department_id}`
  }, (payload) => {
    // Update kanban board
  })
  .subscribe()

// Guest tracker — subscribe to own request events
const guestSub = supabase
  .channel('request_events')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'request_events',
    filter: `hotel_id=eq.${hotelId}`
  }, (payload) => {
    // Update request status in UI
  })
  .subscribe()
```

## Deployment Architecture

```
yourdomain.com ──────► Vercel (Next.js)
                          │
api.yourdomain.com ──► Railway (FastAPI)
                          │
                       Supabase (managed PostgreSQL)
                          │
                    Cloudflare DNS (domain registrar)
```

## Key Design Decisions

1. **FastAPI for all writes, Supabase client for reads**
   - Mutations always go through FastAPI (business logic, AI, validation)
   - Simple SELECTs can use Supabase JS client directly (faster, RLS enforced)

2. **hotel_id denormalized on requests + request_events**
   - Avoids expensive JOINs on every RLS check
   - Small storage cost, massive query performance gain

3. **guest_sessions separate from users**
   - Guests never touch fast-authkit JWT system
   - Cleaner separation of concerns
   - Guest data (PII) isolated from staff auth system

4. **request_events is append-only**
   - Never UPDATE or DELETE — full immutable audit trail
   - Powers both guest tracker AND manager guest journey timeline
   - Single source of truth for "what happened to this request"

5. **Provider-agnostic AI layer**
   - Today: Gemini Pro (free tier for prototype)
   - Production: swap to Claude Haiku 4.5 — zero frontend changes
   - One config change in ai_service.py

## Performance Considerations
- Index all hotel_id, status, department_id, created_at columns
- Supabase connection pooling via pgBouncer (built-in)
- Next.js Server Components for manager analytics (heavy data, no client bundle)
- TanStack Query for caching — avoid redundant API calls on tab switch
- Deepgram streaming (real-time transcript) for better UX on voice notes
