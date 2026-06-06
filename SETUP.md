# InStayOS — Local Development Setup Guide

## Prerequisites
- Node.js 20+ and pnpm
- Python 3.11+ and uv (pip install uv)
- Git
- Supabase account + project created
- Gemini API key (Google AI Studio — free)
- Deepgram API key ($200 free credits)

## Step 1 — Clone and Structure
```bash
mkdir instayos && cd instayos
git init
mkdir -p apps/web apps/api docs
# Copy all docs from /docs folder into docs/
```

## Step 2 — Supabase Setup
1. Create project at supabase.com
2. Go to SQL Editor
3. Run SCHEMA.md enum definitions first
4. Run full table DDL (Claude Code will generate this from SCHEMA.md)
5. Enable Realtime on: requests, request_events, notifications, tablets
6. Copy: Project URL, anon key, service role key

## Step 3 — FastAPI Backend Setup
```bash
cd apps/api
uv init
uv add fastapi uvicorn sqlalchemy asyncpg pydantic python-dotenv \
       fast-authkit bcrypt google-generativeai deepgram-sdk \
       python-multipart aiofiles slowapi cryptography supabase
cp .env.example .env
# Fill in .env with your keys
uv run uvicorn main:app --reload --port 8000
```

## Step 4 — Next.js Frontend Setup
```bash
cd apps/web
pnpm create next-app@latest . --typescript --tailwind --app --src-dir=false
pnpm add @supabase/supabase-js @supabase/ssr framer-motion zustand \
         @tanstack/react-query react-hook-form zod @hookform/resolvers
pnpm dlx shadcn@latest init
# Add shadcn components as needed
cp .env.local.example .env.local
# Fill in with your keys
pnpm dev
```

## Step 5 — Claude Code Project Setup
```bash
# In project root (instayos/)
cp CLAUDE.md ./CLAUDE.md          # Claude Code reads this automatically
cp mcp.json ./.mcp.json           # Claude Code MCP config
# Set environment variables for MCP servers
export SUPABASE_URL=your_url
export SUPABASE_SERVICE_ROLE_KEY=your_key
export GITHUB_TOKEN=your_token
```

## Step 6 — Start Claude Code
```bash
# In project root
claude
# Claude Code will read CLAUDE.md automatically
# First prompt to Claude Code:
# "Read CLAUDE.md, PRD.md, SCHEMA.md, ARCHITECTURE.md and FLOWS.md in /docs.
#  Then start with Step 1 of the build order: generate the Supabase SQL DDL
#  for all 12 tables based on SCHEMA.md, including RLS policies and indexes."
```

## .env.example (Backend)
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
AUTHKIT_SECRET_KEY=your_generated_secret
AUTHKIT_DATABASE_URL=postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres
AUTHKIT_COOKIE_SECURE=False
AUTHKIT_COOKIE_SAMESITE=lax
GEMINI_API_KEY=your_gemini_key
DEEPGRAM_API_KEY=your_deepgram_key
AES_ENCRYPTION_KEY=your_32_byte_key
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

## .env.local.example (Frontend)
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## First Claude Code Prompts (In Order)
1. "Generate complete Supabase SQL DDL for all 12 tables in SCHEMA.md with RLS and indexes"
2. "Set up FastAPI project structure in apps/api with fast-authkit (download from pypi using uv add fast-authkit), extend User model with hotel_id, department_id, display_name, avatar_url, last_seen_at"
3. "Create hotel isolation middleware and add rate limiting on auth endpoints"
4. "Create guest PIN verification endpoint POST /guest/verify-pin"
5. "Create provider-agnostic AIService with Gemini Pro implementation"
6. "Create POST /requests/create endpoint with full AI classification flow"
7. "Set up Next.js project structure with Supabase client, Zustand stores, TanStack Query"
8. "Build the landing screen with guest/hotel role selection routing"
9. (Continue through build order in CLAUDE.md)
