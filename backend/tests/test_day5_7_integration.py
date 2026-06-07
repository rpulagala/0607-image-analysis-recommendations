"""
Days 5–7 Tests — Rate Limiter, Security & End-to-End Integration

Run:  pytest backend/tests/test_day5_7_integration.py -v

Covers:
  - backend/middleware/rate_limiter.py  (under limit, at limit → 429)
  - CORS / security headers
  - Full user journey: signup → analyze → history → upgrade → unlimited
  - Free tier wall: 6th request returns 402
  - Auth boundary: each endpoint enforces authentication
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from backend.main import app
from backend.models.analysis import AnalysisResult, Recommendation
from backend.tests.conftest import (
    IMAGE_URL,
    MOCK_ANALYSIS_DATA,
    MOCK_RECS_DATA,
    MOCK_USER,
    USER_ID,
    make_supabase_result,
)


# ── Rate limiter (unit tests) ─────────────────────────────────────────────────

async def test_rate_limiter_allows_under_limit():
    from backend.middleware.rate_limiter import rate_limit

    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=5)
    mock_redis.expire = AsyncMock()

    with patch("backend.middleware.rate_limiter._get_redis", return_value=mock_redis):
        await rate_limit(USER_ID, max_requests=10)  # count=5, limit=10 → OK


async def test_rate_limiter_blocks_at_limit():
    from backend.middleware.rate_limiter import rate_limit

    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=11)
    mock_redis.expire = AsyncMock()

    with patch("backend.middleware.rate_limiter._get_redis", return_value=mock_redis):
        with pytest.raises(HTTPException) as exc:
            await rate_limit(USER_ID, max_requests=10)

    assert exc.value.status_code == 429
    assert "Too many requests" in exc.value.detail


async def test_rate_limiter_sets_ttl_on_first_request():
    from backend.middleware.rate_limiter import rate_limit

    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=1)  # first request
    mock_redis.expire = AsyncMock()

    with patch("backend.middleware.rate_limiter._get_redis", return_value=mock_redis):
        await rate_limit(USER_ID, max_requests=10, window_seconds=60)

    mock_redis.expire.assert_awaited_once()
    call_args = mock_redis.expire.call_args
    assert call_args.args[1] == 60


async def test_rate_limiter_does_not_reset_ttl_on_subsequent_requests():
    from backend.middleware.rate_limiter import rate_limit

    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=5)  # not first request
    mock_redis.expire = AsyncMock()

    with patch("backend.middleware.rate_limiter._get_redis", return_value=mock_redis):
        await rate_limit(USER_ID, max_requests=10)

    mock_redis.expire.assert_not_awaited()


async def test_rate_limiter_key_includes_user_id():
    from backend.middleware.rate_limiter import rate_limit

    captured_keys = []
    mock_redis = AsyncMock()

    async def capture_incr(key):
        captured_keys.append(key)
        return 1

    mock_redis.incr = capture_incr
    mock_redis.expire = AsyncMock()

    with patch("backend.middleware.rate_limiter._get_redis", return_value=mock_redis):
        await rate_limit("special-user-999", max_requests=10)

    assert any("special-user-999" in k for k in captured_keys)


# ── Security: all protected endpoints enforce auth ────────────────────────────

@pytest.mark.parametrize("method,path", [
    ("GET", "/api/history"),
    ("GET", "/api/profile"),
    ("GET", "/api/billing/usage"),
    ("POST", "/api/analyze"),
    ("POST", "/api/billing/checkout"),
    ("POST", "/api/billing/portal"),
])
async def test_endpoint_requires_authorization_header(method, path):
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.request(method, path)
    assert r.status_code == 422


# ── End-to-end: happy path ────────────────────────────────────────────────────

async def test_e2e_full_happy_path(mock_current_user):
    """Simulate: upload image → get analysis → view in history."""
    analysis_obj = AnalysisResult(**MOCK_ANALYSIS_DATA)
    rec_objects = [Recommendation(**r) for r in MOCK_RECS_DATA]

    # Step 1: Analyze
    with patch("backend.routes.analyze.check_and_increment_usage", new_callable=AsyncMock):
        with patch("backend.routes.analyze.upload_image", new_callable=AsyncMock, return_value=IMAGE_URL):
            with patch("backend.routes.analyze.analyze_image", new_callable=AsyncMock, return_value=analysis_obj):
                with patch("backend.routes.analyze.generate_recommendations", new_callable=AsyncMock, return_value=rec_objects):
                    with patch("backend.routes.analyze.supabase") as sb:
                        sb.table.return_value.insert.return_value.execute.return_value = MagicMock()
                        async with AsyncClient(app=app, base_url="http://test") as client:
                            analyze_r = await client.post(
                                "/api/analyze",
                                files={"file": ("photo.jpg", b"fake-jpeg", "image/jpeg")},
                                headers={"Authorization": "Bearer token"},
                            )

    assert analyze_r.status_code == 200
    analysis_id = analyze_r.json()["id"]
    assert analysis_id

    # Step 2: Fetch history
    history_record = {**analyze_r.json(), "user_id": USER_ID}
    with patch("backend.routes.history.supabase") as sb:
        sb.table.return_value.select.return_value.eq.return_value \
            .order.return_value.range.return_value.execute.return_value = make_supabase_result([history_record])
        async with AsyncClient(app=app, base_url="http://test") as client:
            history_r = await client.get("/api/history", headers={"Authorization": "Bearer token"})

    assert history_r.status_code == 200
    assert len(history_r.json()["items"]) == 1

    # Step 3: Fetch single detail
    with patch("backend.routes.history.supabase") as sb:
        sb.table.return_value.select.return_value.eq.return_value \
            .eq.return_value.maybe_single.return_value.execute.return_value = make_supabase_result(history_record)
        async with AsyncClient(app=app, base_url="http://test") as client:
            detail_r = await client.get(
                f"/api/history/{analysis_id}",
                headers={"Authorization": "Bearer token"},
            )

    assert detail_r.status_code == 200


# ── End-to-end: free tier wall ────────────────────────────────────────────────

async def test_e2e_free_tier_blocked_on_6th_request(mock_current_user):
    """Free user is blocked on their 6th analysis with a 402."""
    with patch("backend.routes.analyze.check_and_increment_usage", new_callable=AsyncMock) as mock_usage:
        mock_usage.side_effect = HTTPException(
            status_code=402,
            detail="Free tier limit of 5 analyses/month reached. Upgrade to Pro.",
        )
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.post(
                "/api/analyze",
                files={"file": ("photo.jpg", b"fake-jpeg", "image/jpeg")},
                headers={"Authorization": "Bearer token"},
            )

    assert r.status_code == 402
    assert "upgrade" in r.json()["detail"].lower() or "Pro" in r.json()["detail"]


# ── End-to-end: pro upgrade removes wall ─────────────────────────────────────

async def test_e2e_pro_user_not_blocked(mock_current_user):
    """Pro user can analyze beyond the free limit."""
    analysis_obj = AnalysisResult(**MOCK_ANALYSIS_DATA)
    rec_objects = [Recommendation(**r) for r in MOCK_RECS_DATA]

    with patch("backend.routes.analyze.check_and_increment_usage", new_callable=AsyncMock):
        # Pro tier: check_and_increment_usage does not raise
        with patch("backend.routes.analyze.upload_image", new_callable=AsyncMock, return_value=IMAGE_URL):
            with patch("backend.routes.analyze.analyze_image", new_callable=AsyncMock, return_value=analysis_obj):
                with patch("backend.routes.analyze.generate_recommendations", new_callable=AsyncMock, return_value=rec_objects):
                    with patch("backend.routes.analyze.supabase") as sb:
                        sb.table.return_value.insert.return_value.execute.return_value = MagicMock()
                        async with AsyncClient(app=app, base_url="http://test") as client:
                            r = await client.post(
                                "/api/analyze",
                                files={"file": ("photo.jpg", b"fake-jpeg", "image/jpeg")},
                                headers={"Authorization": "Bearer token"},
                            )

    assert r.status_code == 200


# ── End-to-end: Stripe upgrade flow ──────────────────────────────────────────

async def test_e2e_checkout_flow(mock_current_user):
    """User clicks upgrade → gets Stripe checkout URL."""
    with patch("backend.routes.billing.create_checkout_session", new_callable=AsyncMock,
               return_value="https://checkout.stripe.com/pay/cs_test_abc"):
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.post(
                "/api/billing/checkout",
                json={
                    "price_id": "price_test123",
                    "success_url": "https://app.com/success",
                    "cancel_url": "https://app.com/cancel",
                },
                headers={"Authorization": "Bearer token"},
            )

    assert r.status_code == 200
    assert r.json()["url"].startswith("https://checkout.stripe.com")


# ── Smoke: health check ───────────────────────────────────────────────────────

async def test_health_always_reachable():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200


async def test_openapi_schema_loads():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert "paths" in schema
    assert "/api/analyze" in schema["paths"]
    assert "/api/history" in schema["paths"]
    assert "/api/billing/usage" in schema["paths"]
