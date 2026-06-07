# Project Plan: AI-Powered Image Analysis & Recommendations MVP

**Client:** [TBD]
**Date:** 2026-06-07
**Author:** rpulagala

---

## Overview

Build an MVP web application that lets users upload images, receive AI-generated insights, and get personalized recommendations — with user accounts, subscription billing, and a deployment-ready architecture.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend | Next.js 14 (React + TypeScript) | SSR, SEO, file upload UX, fast routing |
| Backend | FastAPI (Python) | Async, OpenAI SDK native, easy to extend |
| AI | OpenAI GPT-4o Vision | Image analysis + text recommendations in one call |
| Auth | Supabase Auth | Built-in OAuth, JWT, user management |
| Database | Supabase PostgreSQL | Row-level security, works with Auth out of the box |
| File Storage | Supabase Storage | Image uploads, CDN, public URLs |
| Payments | Stripe (Checkout + Billing) | Subscriptions, webhooks, usage metering |
| Hosting | Vercel (frontend) + Render (backend) | Zero-config deploys, free tiers for MVP |
| Cache / Rate Limit | Redis (Upstash) | Per-user request throttling |

---

## Deployment Status

| Service | URL | Status |
|---|---|---|
| Frontend | https://0607-image-analysis-recommendations.vercel.app | Live |
| Backend | https://image-analysis-api-rw8j.onrender.com | Live |
| Database | Supabase project `visqdxkijkemkhczodxk` | Live |
| Storage | Supabase bucket `user-images` | Live |
| Redis | Upstash `stunning-tahr-144691` | Live |

---

## MVP Feature Scope

### Phase 1 — Core ✅ COMPLETE
- [x] Project scaffold: Next.js + FastAPI, deployed via GitHub
- [x] User auth: signup, signin, signout (Supabase Auth + JWT)
- [x] Image upload: drag-and-drop UI, 10 MB limit, JPEG/PNG/WEBP, stored in Supabase Storage
- [x] AI analysis endpoint: GPT-4o Vision → structured JSON (labels, description, objects, attributes)
- [x] Recommendations engine: follow-up GPT-4o prompt → 5 personalized suggestions with relevance scores
- [x] Results page: image display, analysis summary, recommendations cards

### Phase 2 — Accounts & History ✅ COMPLETE
- [x] User dashboard: recent analyses shown after upload
- [x] Profile page: name, email, subscription tier badge
- [x] Analysis history: paginated list with thumbnail + description preview
- [x] Analysis detail view: revisit any past result via `/history/{id}`
- [ ] Search/filter on history *(deferred to post-MVP)*

### Phase 3 — Payments ⚠️ PARTIALLY COMPLETE
- [x] Free tier gating: 5 analyses/month enforced, HTTP 402 on limit
- [x] Usage meter: progress bar on dashboard + profile page
- [x] Stripe checkout session flow (code complete)
- [x] Stripe billing portal link (code complete)
- [x] Webhook handler: `checkout.completed`, `subscription.updated/deleted` (code complete)
- [ ] **PENDING: Real Stripe keys** — `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRO_PRICE_ID` are placeholders; billing UI will error until configured

### Phase 4 — Polish & Deploy ✅ COMPLETE
- [x] Responsive UI (Tailwind CSS)
- [x] Error handling: 402 upgrade prompt, loading spinners, empty states
- [x] Rate limiting via Redis (per-user, per-minute)
- [x] CORS hardening (`ALLOWED_ORIGINS` env var)
- [x] Production deploy: Vercel + Render
- [x] End-to-end smoke test: signup → upload → GPT-4o analysis → recommendations → DB write verified

---

## Architecture Diagram (Simplified)

```
User Browser (Next.js on Vercel)
    │
    ├── Supabase Auth  ─────────────────────── PostgreSQL (profiles, analyses, subscriptions, monthly_usage)
    │
    ├── POST /api/analyze ──────────────────► FastAPI Backend (Render)
    │       │                                      │
    │       │  image (multipart)                   ├── Supabase Storage (save image → user-images bucket)
    │       │                                      ├── OpenAI GPT-4o Vision (analyze)
    │       │                                      ├── OpenAI GPT-4o (recommend)
    │       │                                      └── DB write (analyses + monthly_usage)
    │       │◄─── { analysis, recommendations } ──┘
    │
    └── Stripe Checkout / Billing Portal
```

---

## What's Been Built

### Backend (`/backend`)
| File | Status |
|---|---|
| `config.py` | Done — pydantic-settings, handles all env var formats |
| `database.py` | Done — Supabase singleton client |
| `main.py` | Done — FastAPI app, CORS, all routers mounted |
| `routes/auth.py` | Done — signup, signin, signout |
| `routes/analyze.py` | Done — full pipeline: upload → AI → recs → DB |
| `routes/history.py` | Done — paginated list + detail |
| `routes/profile.py` | Done — get + update profile |
| `routes/billing.py` | Done — usage, checkout, portal |
| `services/storage.py` | Done — Supabase Storage upload with validation |
| `services/ai_analysis.py` | Done — GPT-4o Vision → AnalysisResult |
| `services/recommendations.py` | Done — GPT-4o → 5 Recommendation objects |
| `services/usage.py` | Done — free tier gating + monthly tracking |
| `services/stripe_service.py` | Done — customer, checkout, portal (needs real keys) |
| `middleware/auth_guard.py` | Done — Supabase JWT validation dependency |
| `middleware/rate_limiter.py` | Done — Redis per-user rate limiter |
| `webhooks/stripe_webhook.py` | Done — subscription lifecycle events |

### Frontend (`/frontend`)
| File | Status |
|---|---|
| `app/page.tsx` | Done — landing / redirect |
| `app/auth/signin/page.tsx` | Done — sign in form |
| `app/auth/signup/page.tsx` | Done — sign up form |
| `app/dashboard/page.tsx` | Done — upload + results + recent history |
| `app/profile/page.tsx` | Done — profile edit + usage + subscription |
| `app/history/page.tsx` | Done — full history list |
| `app/history/[id]/page.tsx` | Done — analysis detail |
| `components/ImageUpload.tsx` | Done — drag-and-drop with client validation |
| `components/AnalysisResult.tsx` | Done — labels, description, objects, attributes, recs |
| `components/UsageMeter.tsx` | Done — free/pro usage display |
| `components/Navbar.tsx` | Done — nav with auth state |
| `lib/api.ts` | Done — typed API client |
| `lib/auth.ts` | Done — localStorage auth helpers |
| `lib/types.ts` | Done — TypeScript interfaces |

### Database (Supabase)
| Item | Status |
|---|---|
| `profiles` table | Done |
| `analyses` table | Done |
| `monthly_usage` table | Done |
| `subscriptions` table | Done |
| `user-images` storage bucket | Done |
| Storage RLS policies | Done |
| `handle_new_user` trigger | Done — auto-creates profile + subscription on signup |

### Tests (`/backend/tests`)
| File | Coverage |
|---|---|
| `test_day1_auth_upload.py` | 21 tests — auth endpoints, upload validation |
| `test_day2_ai_pipeline.py` | 14 tests — GPT-4o pipeline, recommendations |
| `test_day3_history_profile.py` | 18 tests — JWT guard, history, profile CRUD |
| `test_day4_billing_webhooks.py` | 22 tests — usage gating, Stripe, webhooks |
| `test_day5_7_integration.py` | 16 tests — rate limiter, e2e flows, security |

---

## Pending — Required for Full MVP

| Item | Priority | Notes |
|---|---|---|
| **Stripe live keys** | High | Set `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRO_PRICE_ID` in Render dashboard; add webhook endpoint in Stripe dashboard pointing to `https://image-analysis-api-rw8j.onrender.com/webhooks/stripe` |
| **ALLOWED_ORIGINS update** | Medium | Change from `["*"]` to `["https://0607-image-analysis-recommendations.vercel.app"]` in Render env vars |
| **Custom domain** | Low | Point client's domain to Vercel; update `ALLOWED_ORIGINS` and `NEXT_PUBLIC_API_URL` accordingly |
| **Email confirmation** | Medium | Supabase currently requires email confirmation on signup — test user was confirmed manually; configure Supabase Auth email templates for production |
| **Stripe Pro price** | High | Create a recurring price in Stripe dashboard, copy the `price_xxx` ID to Render + Vercel env vars |

---

## Pending — Nice-to-Have (Post-MVP)

| Item | Notes |
|---|---|
| History search/filter | Filter by date or keyword in analysis description |
| Password reset flow | Supabase supports it, just needs a frontend page |
| Client-side image resize | Resize to 1024px before upload to reduce latency + OpenAI cost |
| Mobile UI polish | Currently functional but not fully optimised for small screens |
| Admin analytics dashboard | Usage stats, revenue overview |
| Bulk image upload | Multi-file queue |
| Social sharing | Public result links |

---

## Timeline

| Day | Milestone | Status |
|---|---|---|
| 1 | Scaffold, auth, image upload + storage | Done |
| 2 | AI analysis + recommendations pipeline | Done |
| 3 | Dashboard, history, profile | Done |
| 4 | Stripe subscriptions, usage gating | Done (pending live keys) |
| 5–7 | Polish, rate limiting, deploy, handoff | Done |

**Total: 5–7 days — MVP deployed**

> **Assumption:** Timeline is based on client being available for 1–2 feedback sessions per day. Delays in client review or approval will extend the timeline accordingly.

---

## Cost Estimate

| Item | Range |
|---|---|
| Development (MVP) | $1,500 – $2,000 |
| Post-launch support (optional, 30 days) | $500 – $1,200 |
| **Total** | **$2,000 – $3,200** |

**Ongoing infrastructure costs (client pays directly):**
- Supabase Free → Pro: $0 – $25/month
- Render (backend): $7/month
- Vercel: $0 – $20/month
- OpenAI API: ~$0.01–$0.03 per analysis (GPT-4o Vision)
- Stripe: 2.9% + 30¢ per transaction

---

## Deliverables

1. Full source code (GitHub: `rpulagala/0607-image-analysis-recommendations`)
2. Working deployed MVP — Vercel + Render
3. README with local setup and environment variable docs
4. Supabase schema (tables, RLS policies, trigger) — documented in README
5. Transfer of all project assets and IP
6. Optional: 30-day post-launch bug-fix support

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| OpenAI API cost spikes | Per-user rate limiting (Redis) + free tier cap |
| Large image upload latency | Client-side resize to 1024px (post-MVP) |
| Stripe webhook reliability | Idempotent webhook handler with signature verification |
| Render cold starts (free tier) | ~30s wake-up on first request after inactivity; upgrade to $7/mo paid instance to eliminate |
| Scope creep | Clear MVP boundary; post-MVP backlog kept separate |

---

## Post-MVP Backlog (Not in Scope)

- Mobile app (React Native)
- Custom AI model fine-tuning
- Social sharing / public profiles
- Bulk image upload
- Admin analytics dashboard
- Multi-language support
- Password reset page
- Client-side image resize before upload
