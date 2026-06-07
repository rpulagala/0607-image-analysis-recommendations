# AI Image Analysis & Recommendations

An MVP web application where users upload images, receive AI-generated insights, and get personalized recommendations — with user accounts, usage history, and Stripe subscription billing.

**Live Demo:**
- Frontend: https://0607-image-analysis-recommendations.vercel.app
- Backend API: https://image-analysis-api-rw8j.onrender.com/health

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (React + TypeScript + Tailwind CSS) |
| Backend | FastAPI (Python 3.11) |
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
│       ├── conftest.py
│       ├── test_day1_auth_upload.py
│       ├── test_day2_ai_pipeline.py
│       ├── test_day3_history_profile.py
│       ├── test_day4_billing_webhooks.py
│       └── test_day5_7_integration.py
├── frontend/
│   ├── app/
│   │   ├── page.tsx              # Landing / redirect
│   │   ├── auth/signin/page.tsx  # Sign in
│   │   ├── auth/signup/page.tsx  # Sign up
│   │   ├── dashboard/page.tsx    # Upload + results + recent history
│   │   ├── profile/page.tsx      # Profile + usage + subscription
│   │   ├── history/page.tsx      # Full history list
│   │   └── history/[id]/page.tsx # Analysis detail
│   ├── components/
│   │   ├── ImageUpload.tsx       # Drag-and-drop upload with validation
│   │   ├── AnalysisResult.tsx    # Labels, description, objects, attributes, recs
│   │   ├── UsageMeter.tsx        # Free/pro usage display
│   │   └── Navbar.tsx            # Navigation with auth state
│   └── lib/
│       ├── api.ts                # Typed API client
│       ├── auth.ts               # localStorage auth helpers
│       └── types.ts              # TypeScript interfaces
├── .python-version               # Pins Python 3.11 for Render
├── render.yaml                   # Render backend service config
├── requirements.txt              # Pinned Python dependencies
├── pytest.ini                    # asyncio_mode = auto
└── project_plan.md               # Full build plan and status
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
- Node.js 18+
- A [Supabase](https://supabase.com) project
- An [OpenAI](https://platform.openai.com) API key
- A [Stripe](https://stripe.com) account (optional for local dev)
- A Redis instance ([Upstash](https://upstash.com) free tier works)

### 1. Clone and install backend dependencies

```bash
git clone https://github.com/rpulagala/0607-image-analysis-recommendations.git
cd 0607-image-analysis-recommendations
pip install -r requirements.txt
```

### 2. Configure backend environment variables

Create a `.env` file in the project root (see `.env.example` for all keys):

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

OPENAI_API_KEY=sk-...

STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_PRICE_ID=price_...

REDIS_URL=rediss://...

ALLOWED_ORIGINS=["http://localhost:3000"]
FREE_TIER_LIMIT=5
```

> **Note:** `ALLOWED_ORIGINS` must be a JSON array string. Stripe keys default to placeholders if omitted — the app will start but billing endpoints will error.

### 3. Set up Supabase

Run the following SQL in the [Supabase SQL Editor](https://supabase.com/dashboard/project/_/sql/new):

```sql
-- Tables
create table profiles (
  id uuid references auth.users primary key,
  full_name text,
  subscription_tier text default 'free'
);

create table analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users not null,
  image_url text not null,
  analysis jsonb not null,
  recommendations jsonb not null,
  created_at timestamptz default now()
);

create table monthly_usage (
  user_id uuid references auth.users,
  month text,
  count int default 0,
  primary key (user_id, month)
);

create table subscriptions (
  user_id uuid references auth.users primary key,
  stripe_customer_id text,
  stripe_subscription_id text,
  tier text default 'free',
  status text default 'active',
  current_period_end bigint
);

-- Storage bucket
insert into storage.buckets (id, name, public)
values ('user-images', 'user-images', true)
on conflict (id) do nothing;

-- Storage RLS policies
create policy "Users upload own images" on storage.objects
  for insert to authenticated
  with check (bucket_id = 'user-images' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "Public read images" on storage.objects
  for select using (bucket_id = 'user-images');

-- Auto-create profile + subscription on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, full_name)
  values (new.id, new.raw_user_meta_data->>'full_name');

  insert into public.subscriptions (user_id, tier)
  values (new.id, 'free');

  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
```

### 4. Run the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

API available at `http://localhost:8000` · Swagger docs at `http://localhost:8000/docs`

### 5. Configure and run the frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PRO_PRICE_ID=price_...
```

```bash
npm run dev
```

Frontend available at `http://localhost:3000`

---

## Running Tests

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

| Test file | Coverage |
|---|---|
| `test_day1_auth_upload.py` | 21 tests — auth endpoints, image upload validation |
| `test_day2_ai_pipeline.py` | 14 tests — GPT-4o Vision, recommendations, analyze endpoint |
| `test_day3_history_profile.py` | 18 tests — JWT guard, history pagination, profile CRUD |
| `test_day4_billing_webhooks.py` | 22 tests — usage gating, Stripe service, webhook event routing |
| `test_day5_7_integration.py` | 16 tests — rate limiter, e2e flows, free-tier wall, security |

---

## Deployment

### Backend (Render) — Live at https://image-analysis-api-rw8j.onrender.com

1. Create a **Web Service** on [render.com](https://render.com)
2. Connect `rpulagala/0607-image-analysis-recommendations`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add all env vars from `.env` in the Render dashboard
6. Set `ALLOWED_ORIGINS` to `["https://your-vercel-url.vercel.app"]`

> Render free tier spins down after 15 min of inactivity — first request after sleep takes ~30s. Upgrade to the $7/mo instance to eliminate cold starts.

### Frontend (Vercel) — Live at https://0607-image-analysis-recommendations.vercel.app

1. Create a project on [vercel.com](https://vercel.com)
2. Import `rpulagala/0607-image-analysis-recommendations`
3. Set **Root Directory** to `frontend`
4. Add env vars:
   - `NEXT_PUBLIC_API_URL` = your Render URL
   - `NEXT_PUBLIC_STRIPE_PRO_PRICE_ID` = your Stripe price ID

### Stripe Webhooks

1. In Stripe dashboard → **Developers → Webhooks**
2. Add endpoint: `https://image-analysis-api-rw8j.onrender.com/webhooks/stripe`
3. Subscribe to events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copy the signing secret → `STRIPE_WEBHOOK_SECRET` in Render

---

## Subscription Tiers

| Feature | Free | Pro |
|---|---|---|
| Analyses per month | 5 | Unlimited |
| Image history | Yes | Yes |
| Personalized recommendations | Yes | Yes |
| Priority support | — | Yes |

---

## Environment Variables Reference

### Backend (`.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `SUPABASE_URL` | Yes | — | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | — | Service role key (backend only) |
| `SUPABASE_ANON_KEY` | Yes | — | Anon key |
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `STRIPE_SECRET_KEY` | No | `sk_test_placeholder` | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | No | `whsec_placeholder` | Stripe webhook signing secret |
| `STRIPE_PRO_PRICE_ID` | No | `price_placeholder` | Stripe Price ID for Pro tier |
| `REDIS_URL` | No | `redis://localhost:6379` | Redis connection URL |
| `ALLOWED_ORIGINS` | No | `*` | CORS origins — JSON array string or plain URL |
| `FREE_TIER_LIMIT` | No | `5` | Monthly analysis limit for free users |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Yes | Backend URL (Render in prod, `http://localhost:8000` locally) |
| `NEXT_PUBLIC_STRIPE_PRO_PRICE_ID` | No | Stripe Price ID shown on upgrade button |
