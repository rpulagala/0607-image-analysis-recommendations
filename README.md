# AI Image Analysis & Recommendations

An MVP web application where users upload images, receive AI-generated insights, and get personalized recommendations — with user accounts, usage history, and Stripe subscription billing.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (React + TypeScript) |
| Backend | FastAPI (Python) |
| AI | OpenAI GPT-4o Vision |
| Auth + Database + Storage | Supabase |
| Payments | Stripe Checkout + Billing |
| Rate Limiting | Redis (Upstash) |
| Hosting | Vercel (frontend) + Render (backend) |

---

## Project Structure

```
.
├── backend/
│   ├── main.py                   # FastAPI app, CORS, router mounts
│   ├── config.py                 # Env vars via pydantic-settings
│   ├── database.py               # Supabase client singleton
│   ├── models/
│   │   ├── analysis.py           # AnalysisResult, Recommendation, AnalysisResponse
│   │   ├── user.py               # UserProfile, UpdateProfileRequest
│   │   └── subscription.py       # Subscription, SubscriptionTier, CheckoutSessionRequest
│   ├── routes/
│   │   ├── auth.py               # POST /auth/signup, /signin, /signout
│   │   ├── analyze.py            # POST /api/analyze
│   │   ├── history.py            # GET  /api/history, /api/history/{id}
│   │   ├── profile.py            # GET/PATCH /api/profile
│   │   └── billing.py            # POST /api/billing/checkout, /portal  GET /usage
│   ├── services/
│   │   ├── storage.py            # Image upload to Supabase Storage
│   │   ├── ai_analysis.py        # GPT-4o Vision → AnalysisResult
│   │   ├── recommendations.py    # Follow-up GPT-4o prompt → recommendations
│   │   ├── stripe_service.py     # Stripe customer, checkout session, billing portal
│   │   └── usage.py              # Free tier gating, monthly usage tracking
│   ├── middleware/
│   │   ├── auth_guard.py         # Supabase JWT dependency
│   │   └── rate_limiter.py       # Redis per-user request throttle
│   ├── webhooks/
│   │   └── stripe_webhook.py     # Stripe event handler (checkout, subscription)
│   └── tests/
│       ├── conftest.py           # Shared fixtures and test data
│       ├── test_day1_auth_upload.py
│       ├── test_day2_ai_pipeline.py
│       ├── test_day3_history_profile.py
│       ├── test_day4_billing_webhooks.py
│       └── test_day5_7_integration.py
├── requirements.txt
├── pytest.ini
└── project_plan.md
```

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | — | Health check |
| `POST` | `/auth/signup` | — | Register new user |
| `POST` | `/auth/signin` | — | Sign in, returns JWT |
| `POST` | `/auth/signout` | Bearer | Sign out |
| `POST` | `/api/analyze` | Bearer | Upload image → analysis + recommendations |
| `GET` | `/api/history` | Bearer | Paginated analysis history |
| `GET` | `/api/history/{id}` | Bearer | Single analysis detail |
| `GET` | `/api/profile` | Bearer | User profile + usage count |
| `PATCH` | `/api/profile` | Bearer | Update display name |
| `GET` | `/api/billing/usage` | Bearer | Current tier and monthly usage |
| `POST` | `/api/billing/checkout` | Bearer | Create Stripe checkout session |
| `POST` | `/api/billing/portal` | Bearer | Open Stripe billing portal |
| `POST` | `/webhooks/stripe` | Stripe sig | Handle subscription events |

---

## Local Setup

### Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) project
- An [OpenAI](https://platform.openai.com) API key
- A [Stripe](https://stripe.com) account
- A Redis instance ([Upstash](https://upstash.com) free tier works)

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd 0607-image-analysis-recommendations
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

OPENAI_API_KEY=sk-...

STRIPE_SECRET_KEY=sk_live_... (or sk_test_... for testing)
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_PRICE_ID=price_...

REDIS_URL=redis://...

ALLOWED_ORIGINS=http://localhost:3000
FREE_TIER_LIMIT=5
```

### 3. Set up Supabase

Run the following SQL in the Supabase SQL editor to create the required tables:

```sql
-- User profiles (extends Supabase auth.users)
create table profiles (
  id uuid references auth.users primary key,
  full_name text,
  subscription_tier text default 'free'
);

-- Analysis records
create table analyses (
  id uuid primary key,
  user_id uuid references auth.users not null,
  image_url text not null,
  analysis jsonb not null,
  recommendations jsonb not null,
  created_at timestamptz default now()
);

-- Monthly usage tracking
create table monthly_usage (
  user_id uuid references auth.users,
  month text,               -- format: YYYY-MM
  count int default 0,
  primary key (user_id, month)
);

-- Subscription records
create table subscriptions (
  user_id uuid references auth.users primary key,
  stripe_customer_id text,
  stripe_subscription_id text,
  tier text default 'free',
  status text default 'active',
  current_period_end bigint
);

-- Storage bucket for user images
insert into storage.buckets (id, name, public) values ('user-images', 'user-images', true);
```

Enable Row Level Security and add policies so users can only access their own records.

### 4. Run the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

## Running Tests

Tests are organized by build day and can be run individually or all at once.

```bash
# All tests
pytest -v

# By day
pytest backend/tests/test_day1_auth_upload.py -v
pytest backend/tests/test_day2_ai_pipeline.py -v
pytest backend/tests/test_day3_history_profile.py -v
pytest backend/tests/test_day4_billing_webhooks.py -v
pytest backend/tests/test_day5_7_integration.py -v
```

| Test file | Day | Coverage |
|---|---|---|
| `test_day1_auth_upload.py` | Day 1 | Auth endpoints, image upload validation |
| `test_day2_ai_pipeline.py` | Day 2 | GPT-4o Vision, recommendations, analyze endpoint |
| `test_day3_history_profile.py` | Day 3 | JWT guard, history pagination, profile CRUD |
| `test_day4_billing_webhooks.py` | Day 4 | Usage gating, Stripe service, webhook event routing |
| `test_day5_7_integration.py` | Days 5–7 | Rate limiter, e2e flows, free-tier wall, security |

---

## Deployment

### Backend (Render)

1. Create a new **Web Service** on [render.com](https://render.com)
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables from `.env` in the Render dashboard

### Frontend (Vercel)

1. Create a new project on [vercel.com](https://vercel.com)
2. Connect your GitHub repository (Next.js frontend folder)
3. Add `NEXT_PUBLIC_API_URL=https://your-render-service.onrender.com` as an environment variable

### Stripe Webhooks

1. In the Stripe dashboard, go to **Developers → Webhooks**
2. Add endpoint: `https://your-render-service.onrender.com/webhooks/stripe`
3. Subscribe to events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copy the signing secret into `STRIPE_WEBHOOK_SECRET`

---

## Build Plan

See [`project_plan.md`](project_plan.md) for the full day-by-day breakdown.

| Day | Milestone |
|---|---|
| 1 | Scaffold, auth, image upload + storage |
| 2 | AI analysis + recommendations pipeline |
| 3 | Dashboard, history, profile |
| 4 | Stripe subscriptions + usage gating |
| 5–7 | Polish, rate limiting, deploy, handoff |

---

## Subscription Tiers

| Feature | Free | Pro |
|---|---|---|
| Analyses per month | 5 | Unlimited |
| Image history | ✓ | ✓ |
| Personalized recommendations | ✓ | ✓ |
| Priority support | — | ✓ |

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Service role key (backend only) |
| `SUPABASE_ANON_KEY` | Yes | Anon key (for client-side use) |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `STRIPE_SECRET_KEY` | Yes | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Yes | Stripe webhook signing secret |
| `STRIPE_PRO_PRICE_ID` | Yes | Stripe Price ID for Pro tier |
| `REDIS_URL` | Yes | Redis connection URL |
| `ALLOWED_ORIGINS` | No | CORS origins (default: `http://localhost:3000`) |
| `FREE_TIER_LIMIT` | No | Monthly analysis limit for free users (default: `5`) |
