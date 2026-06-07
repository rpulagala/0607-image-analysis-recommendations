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
| File Storage | Supabase Storage (or S3) | Image uploads, CDN, signed URLs |
| Payments | Stripe (Checkout + Billing) | Subscriptions, webhooks, usage metering |
| Hosting | Vercel (frontend) + Render (backend) | Zero-config deploys, free tiers for MVP |
| Cache / Rate Limit | Redis (Upstash) | Per-user request throttling |

---

## MVP Feature Scope

### Phase 1 — Core (Weeks 1–2)
- [ ] Project scaffold: Next.js + FastAPI repos, CI/CD via GitHub Actions
- [ ] User auth: signup, login, password reset, protected routes (Supabase Auth)
- [ ] Image upload: drag-and-drop UI, 10 MB limit, JPEG/PNG/WEBP, stored in Supabase Storage
- [ ] AI analysis endpoint: send image to GPT-4o Vision, return structured JSON (labels, description, detected objects/attributes)
- [ ] Recommendations engine: follow-up GPT-4o prompt using analysis output → 3–5 personalized suggestions
- [ ] Results page: display image, analysis summary, recommendations cards

### Phase 2 — Accounts & History (Week 3)
- [ ] User dashboard: history of uploaded images + past analyses
- [ ] Profile page: name, email, subscription tier badge
- [ ] Analysis detail view: revisit any past result
- [ ] Basic search/filter on history

### Phase 3 — Payments (Week 4)
- [ ] Stripe integration: Free tier (5 analyses/month) + Pro tier ($X/month, unlimited)
- [ ] Stripe Checkout session flow
- [ ] Webhook handler: activate/cancel subscriptions in DB
- [ ] Usage gating: enforce free-tier limits, prompt upgrade
- [ ] Billing portal link for plan management

### Phase 4 — Polish & Deploy (Week 5)
- [ ] Responsive mobile UI polish
- [ ] Error handling, loading states, empty states
- [ ] Rate limiting (Redis) to protect AI costs
- [ ] Environment hardening: secrets management, CORS, input validation
- [ ] Production deploy: Vercel + Render + custom domain
- [ ] Smoke testing end-to-end

---

## Architecture Diagram (Simplified)

```
User Browser (Next.js)
    │
    ├── Supabase Auth  ─────────────────────── PostgreSQL (users, history, subscriptions)
    │
    ├── POST /api/analyze ──────────────────► FastAPI Backend
    │       │                                      │
    │       │  image (multipart)                   ├── Supabase Storage (save image)
    │       │                                      ├── OpenAI GPT-4o Vision (analyze)
    │       │                                      ├── OpenAI GPT-4o (recommend)
    │       │                                      └── DB write (result record)
    │       │◄─── { analysis, recommendations } ──┘
    │
    └── Stripe Checkout / Billing Portal
```

---

## Timeline

| Day | Milestone |
|---|---|
| 1 | Scaffold, auth, image upload + storage |
| 2 | AI analysis + recommendations pipeline, results page |
| 3 | Dashboard, history, profile |
| 4 | Stripe subscriptions, usage gating |
| 5 | Polish, deploy, docs, handoff |

**Total: 5-7 days**

---

## Daily File Build Plan

### Day 1 — Scaffold, Auth, Image Upload
| File | Purpose |
|---|---|
| `backend/__init__.py` | Package root |
| `backend/config.py` | Env vars and settings via pydantic-settings |
| `backend/database.py` | Supabase client singleton |
| `backend/main.py` | FastAPI app, CORS middleware, router mounts |
| `backend/models/__init__.py` | Models package |
| `backend/routes/__init__.py` | Routes package |
| `backend/services/__init__.py` | Services package |
| `backend/middleware/__init__.py` | Middleware package |
| `backend/webhooks/__init__.py` | Webhooks package |
| `backend/routes/auth.py` | POST /auth/signup, /auth/signin, /auth/signout |
| `backend/services/storage.py` | Upload image to Supabase Storage, validate type/size |

### Day 2 — AI Analysis + Recommendations Pipeline
| File | Purpose |
|---|---|
| `backend/models/analysis.py` | Pydantic models: AnalysisResult, Recommendation, AnalysisResponse |
| `backend/services/ai_analysis.py` | GPT-4o Vision call → structured AnalysisResult |
| `backend/services/recommendations.py` | Follow-up GPT-4o prompt → list of Recommendation |
| `backend/routes/analyze.py` | POST /api/analyze — orchestrates upload → analysis → recs → DB write |

### Day 3 — Dashboard, History, Profile
| File | Purpose |
|---|---|
| `backend/models/user.py` | UserProfile, UpdateProfileRequest models |
| `backend/middleware/auth_guard.py` | get_current_user dependency — validates Supabase JWT |
| `backend/routes/history.py` | GET /api/history (paginated + search), GET /api/history/{id} |
| `backend/routes/profile.py` | GET /api/profile, PATCH /api/profile |

### Day 4 — Stripe Subscriptions + Usage Gating
| File | Purpose |
|---|---|
| `backend/models/subscription.py` | Subscription, SubscriptionTier, CheckoutSessionRequest models |
| `backend/services/usage.py` | check_and_increment_usage (enforces free tier), get_usage |
| `backend/services/stripe_service.py` | Stripe customer, checkout session, billing portal session |
| `backend/routes/billing.py` | POST /api/billing/checkout, /billing/portal, GET /billing/usage |
| `backend/webhooks/stripe_webhook.py` | POST /webhooks/stripe — handle checkout.completed + subscription changes |

### Days 5–7 — Rate Limiting, Tests, Deploy
| File | Purpose |
|---|---|
| `backend/middleware/rate_limiter.py` | Redis-backed per-user request throttle (10 req/min default) |
| `backend/tests/__init__.py` | Tests package |
| `backend/tests/test_auth.py` | Signup validation, signin bad credentials, auth guard |
| `backend/tests/test_analyze.py` | Rejects non-images, full pipeline with mocks |
| `backend/tests/test_billing.py` | Usage endpoint, free/pro tier, checkout URL |
| `requirements.txt` | Pinned dependencies |

---

## Cost Estimate

| Item | Range |
|---|---|
| Development (MVP) | $1,500 – $2,000 |
| Post-launch support (optional, 30 days) | $500 – $1200 |
| **Total** | **$2,000 – $3,200** |

**Ongoing infrastructure costs (client pays directly):**
- Supabase Free → Pro: $0 – $25/month
- Render (backend): $7/month
- Vercel: $0 – $20/month
- OpenAI API: ~$0.01–$0.03 per analysis (GPT-4o Vision)
- Stripe: 2.9% + 30¢ per transaction

---

## Deliverables

1. Full source code (GitHub repo, client-owned)
2. Working deployed MVP (Vercel + Render)
3. README with local setup and environment variable docs
4. Deployment guide (Vercel, Render, Supabase, Stripe setup steps)
5. Transfer of all project assets and IP
6. Optional: 30-day post-launch bug-fix support

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| OpenAI API cost spikes | Per-user rate limiting + usage alerts |
| Large image upload latency | Client-side resize to 1024px before upload |
| Stripe webhook reliability | Idempotent webhook handler with retry logging |
| Scope creep | Clear MVP boundary; post-MVP backlog kept separate |

---

## Post-MVP Backlog (Not in Scope)

- Mobile app (React Native)
- Custom AI model fine-tuning
- Social sharing / public profiles
- Bulk image upload
- Admin analytics dashboard
- Multi-language support
