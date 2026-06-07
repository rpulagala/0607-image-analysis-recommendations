"""
Day 4 Tests — Stripe Subscriptions, Usage Gating & Webhooks

Run:  pytest backend/tests/test_day4_billing_webhooks.py -v

Covers:
  - backend/services/usage.py          (free tier limit, pro bypass, increment)
  - backend/services/stripe_service.py (customer creation, checkout, portal)
  - GET  /api/billing/usage
  - POST /api/billing/checkout
  - POST /api/billing/portal
  - POST /webhooks/stripe              (signature, event routing, DB updates)
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from backend.main import app
from backend.tests.conftest import MOCK_USER, USER_ID, make_supabase_result


# ── usage service ─────────────────────────────────────────────────────────────

async def test_usage_pro_tier_bypasses_limit():
    from backend.services.usage import check_and_increment_usage

    with patch("backend.services.usage.supabase") as sb:
        sb.table.return_value.select.return_value.eq.return_value \
            .execute.return_value = make_supabase_result([{"tier": "pro"}])
        # Should not raise even though we provide no usage record
        await check_and_increment_usage(USER_ID)


async def test_usage_free_tier_under_limit_passes():
    from backend.services.usage import check_and_increment_usage

    def mock_table(name):
        m = MagicMock()
        if name == "subscriptions":
            m.select.return_value.eq.return_value.execute.return_value = make_supabase_result([{"tier": "free"}])
        elif name == "monthly_usage":
            m.select.return_value.eq.return_value.eq.return_value.execute.return_value = make_supabase_result([{"count": 2}])
            m.upsert.return_value.execute.return_value = make_supabase_result(None)
        return m

    with patch("backend.services.usage.supabase") as sb:
        sb.table.side_effect = mock_table
        await check_and_increment_usage(USER_ID)  # count=2, limit=5 → should pass


async def test_usage_free_tier_at_limit_raises_402():
    from backend.services.usage import check_and_increment_usage

    def mock_table(name):
        m = MagicMock()
        if name == "subscriptions":
            m.select.return_value.eq.return_value.execute.return_value = make_supabase_result([{"tier": "free"}])
        elif name == "monthly_usage":
            m.select.return_value.eq.return_value.eq.return_value.execute.return_value = make_supabase_result([{"count": 5}])
        return m

    with patch("backend.services.usage.supabase") as sb:
        sb.table.side_effect = mock_table
        with pytest.raises(HTTPException) as exc:
            await check_and_increment_usage(USER_ID)

    assert exc.value.status_code == 402
    assert "upgrade" in exc.value.detail.lower() or "limit" in exc.value.detail.lower()


async def test_usage_free_tier_no_prior_record_starts_at_zero():
    from backend.services.usage import check_and_increment_usage

    upsert_data = {}

    def mock_table(name):
        m = MagicMock()
        if name == "subscriptions":
            m.select.return_value.eq.return_value.execute.return_value = make_supabase_result([{"tier": "free"}])
        elif name == "monthly_usage":
            m.select.return_value.eq.return_value.eq.return_value.execute.return_value = make_supabase_result([])

            def capture_upsert(data):
                upsert_data.update(data)
                return MagicMock(execute=MagicMock(return_value=MagicMock()))

            m.upsert.side_effect = capture_upsert
        return m

    with patch("backend.services.usage.supabase") as sb:
        sb.table.side_effect = mock_table
        await check_and_increment_usage(USER_ID)

    assert upsert_data.get("count") == 1


async def test_get_usage_free_tier():
    from backend.services.usage import get_usage

    def mock_table(name):
        m = MagicMock()
        if name == "monthly_usage":
            m.select.return_value.eq.return_value.eq.return_value.execute.return_value = make_supabase_result([{"count": 3}])
        elif name == "subscriptions":
            m.select.return_value.eq.return_value.execute.return_value = make_supabase_result([{"tier": "free"}])
        return m

    with patch("backend.services.usage.supabase") as sb:
        sb.table.side_effect = mock_table
        result = await get_usage(USER_ID)

    assert result["tier"] == "free"
    assert result["used"] == 3
    assert result["limit"] == 5


async def test_get_usage_pro_tier_limit_is_none():
    from backend.services.usage import get_usage

    def mock_table(name):
        m = MagicMock()
        if name == "monthly_usage":
            m.select.return_value.eq.return_value.eq.return_value.execute.return_value = make_supabase_result([{"count": 42}])
        elif name == "subscriptions":
            m.select.return_value.eq.return_value.execute.return_value = make_supabase_result([{"tier": "pro"}])
        return m

    with patch("backend.services.usage.supabase") as sb:
        sb.table.side_effect = mock_table
        result = await get_usage(USER_ID)

    assert result["tier"] == "pro"
    assert result["limit"] is None


# ── stripe_service ────────────────────────────────────────────────────────────

async def test_get_or_create_customer_returns_existing():
    from backend.services.stripe_service import get_or_create_customer

    with patch("backend.services.stripe_service.supabase") as sb:
        sb.table.return_value.select.return_value.eq.return_value \
            .execute.return_value = make_supabase_result([{"stripe_customer_id": "cus_existing"}])
        result = await get_or_create_customer(USER_ID, "test@example.com")

    assert result == "cus_existing"


async def test_get_or_create_customer_creates_new_when_none():
    from backend.services.stripe_service import get_or_create_customer

    with patch("backend.services.stripe_service.supabase") as sb:
        sb.table.return_value.select.return_value.eq.return_value \
            .execute.return_value = make_supabase_result([])
        sb.table.return_value.upsert.return_value.execute.return_value = MagicMock()

        with patch("backend.services.stripe_service.stripe") as mock_stripe:
            mock_customer = MagicMock()
            mock_customer.id = "cus_new"
            mock_stripe.Customer.create.return_value = mock_customer
            result = await get_or_create_customer(USER_ID, "test@example.com")

    assert result == "cus_new"
    mock_stripe.Customer.create.assert_called_once()


async def test_create_checkout_session_returns_url():
    from backend.services.stripe_service import create_checkout_session

    with patch("backend.services.stripe_service.get_or_create_customer", new_callable=AsyncMock, return_value="cus_123"):
        with patch("backend.services.stripe_service.stripe") as mock_stripe:
            mock_session = MagicMock()
            mock_session.url = "https://checkout.stripe.com/pay/cs_test"
            mock_stripe.checkout.Session.create.return_value = mock_session
            result = await create_checkout_session(
                USER_ID, "test@example.com", "price_test", "https://app/success", "https://app/cancel"
            )

    assert result == "https://checkout.stripe.com/pay/cs_test"


async def test_create_billing_portal_session_returns_url():
    from backend.services.stripe_service import create_billing_portal_session

    with patch("backend.services.stripe_service.supabase") as sb:
        sb.table.return_value.select.return_value.eq.return_value \
            .single.return_value.execute.return_value = make_supabase_result({"stripe_customer_id": "cus_123"})

        with patch("backend.services.stripe_service.stripe") as mock_stripe:
            mock_portal = MagicMock()
            mock_portal.url = "https://billing.stripe.com/session/bps_test"
            mock_stripe.billing_portal.Session.create.return_value = mock_portal
            result = await create_billing_portal_session(USER_ID, "https://app/settings")

    assert "stripe.com" in result


# ── billing routes ────────────────────────────────────────────────────────────

async def test_billing_usage_endpoint_free_tier(mock_current_user):
    with patch("backend.routes.billing.get_usage", new_callable=AsyncMock,
               return_value={"tier": "free", "used": 2, "limit": 5}):
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get("/api/billing/usage", headers={"Authorization": "Bearer token"})

    assert r.status_code == 200
    data = r.json()
    assert data["tier"] == "free"
    assert data["used"] == 2
    assert data["limit"] == 5


async def test_billing_usage_endpoint_pro_tier(mock_current_user):
    with patch("backend.routes.billing.get_usage", new_callable=AsyncMock,
               return_value={"tier": "pro", "used": 99, "limit": None}):
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get("/api/billing/usage", headers={"Authorization": "Bearer token"})

    assert r.status_code == 200
    assert r.json()["limit"] is None


async def test_billing_usage_requires_auth():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/api/billing/usage")
    assert r.status_code == 422


async def test_billing_checkout_returns_stripe_url(mock_current_user):
    with patch("backend.routes.billing.create_checkout_session", new_callable=AsyncMock,
               return_value="https://checkout.stripe.com/pay/cs_test"):
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
    assert "stripe.com" in r.json()["url"]


async def test_billing_checkout_missing_price_id_is_422(mock_current_user):
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post(
            "/api/billing/checkout",
            json={"success_url": "https://app.com/ok", "cancel_url": "https://app.com/cancel"},
            headers={"Authorization": "Bearer token"},
        )
    assert r.status_code == 422


async def test_billing_portal_returns_url(mock_current_user):
    with patch("backend.routes.billing.create_billing_portal_session", new_callable=AsyncMock,
               return_value="https://billing.stripe.com/session/bps_test"):
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.post(
                "/api/billing/portal?return_url=https://app.com/settings",
                headers={"Authorization": "Bearer token"},
            )

    assert r.status_code == 200
    assert "stripe.com" in r.json()["url"]


# ── Stripe webhook ────────────────────────────────────────────────────────────

def _make_webhook_payload(event_type: str, data: dict) -> dict:
    return {"type": event_type, "data": {"object": data}}


async def test_webhook_rejects_invalid_signature():
    import stripe

    with patch("backend.webhooks.stripe_webhook.stripe") as mock_stripe:
        mock_stripe.Webhook.construct_event.side_effect = stripe.error.SignatureVerificationError(
            "Bad sig", "sig"
        )
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.post(
                "/webhooks/stripe",
                content=b'{"type":"test"}',
                headers={"stripe-signature": "bad-sig", "content-type": "application/json"},
            )

    assert r.status_code == 400


async def test_webhook_checkout_completed_upgrades_user_to_pro():
    session_data = {
        "metadata": {"user_id": USER_ID},
        "subscription": "sub_123",
    }
    event = _make_webhook_payload("checkout.session.completed", session_data)
    updated_data = {}

    with patch("backend.webhooks.stripe_webhook.stripe") as mock_stripe:
        mock_stripe.Webhook.construct_event.return_value = event
        mock_stripe.error = MagicMock()
        mock_stripe.error.SignatureVerificationError = Exception

        with patch("backend.webhooks.stripe_webhook.supabase") as sb:
            def capture_update(data):
                updated_data.update(data)
                return MagicMock(eq=MagicMock(return_value=MagicMock(execute=MagicMock(return_value=None))))

            sb.table.return_value.update.side_effect = capture_update

            async with AsyncClient(app=app, base_url="http://test") as client:
                r = await client.post(
                    "/webhooks/stripe",
                    content=b"{}",
                    headers={"stripe-signature": "valid", "content-type": "application/json"},
                )

    assert r.status_code == 200
    assert r.json() == {"received": True}
    assert updated_data.get("tier") == "pro"
    assert updated_data.get("status") == "active"


async def test_webhook_subscription_canceled_downgrades_to_free():
    subscription_data = {
        "customer": "cus_123",
        "status": "canceled",
        "current_period_end": 1893456000,
    }
    event = _make_webhook_payload("customer.subscription.deleted", subscription_data)
    updated_data = {}

    with patch("backend.webhooks.stripe_webhook.stripe") as mock_stripe:
        mock_stripe.Webhook.construct_event.return_value = event
        mock_stripe.error = MagicMock()
        mock_stripe.error.SignatureVerificationError = Exception

        with patch("backend.webhooks.stripe_webhook.supabase") as sb:
            def capture_update(data):
                updated_data.update(data)
                return MagicMock(eq=MagicMock(return_value=MagicMock(execute=MagicMock(return_value=None))))

            sb.table.return_value.update.side_effect = capture_update

            async with AsyncClient(app=app, base_url="http://test") as client:
                r = await client.post(
                    "/webhooks/stripe",
                    content=b"{}",
                    headers={"stripe-signature": "valid", "content-type": "application/json"},
                )

    assert r.status_code == 200
    assert updated_data.get("tier") == "free"


async def test_webhook_subscription_updated_to_active_stays_pro():
    subscription_data = {
        "customer": "cus_123",
        "status": "active",
        "current_period_end": 1893456000,
    }
    event = _make_webhook_payload("customer.subscription.updated", subscription_data)
    updated_data = {}

    with patch("backend.webhooks.stripe_webhook.stripe") as mock_stripe:
        mock_stripe.Webhook.construct_event.return_value = event
        mock_stripe.error = MagicMock()
        mock_stripe.error.SignatureVerificationError = Exception

        with patch("backend.webhooks.stripe_webhook.supabase") as sb:
            def capture_update(data):
                updated_data.update(data)
                return MagicMock(eq=MagicMock(return_value=MagicMock(execute=MagicMock(return_value=None))))

            sb.table.return_value.update.side_effect = capture_update

            async with AsyncClient(app=app, base_url="http://test") as client:
                r = await client.post(
                    "/webhooks/stripe",
                    content=b"{}",
                    headers={"stripe-signature": "valid", "content-type": "application/json"},
                )

    assert r.status_code == 200
    assert updated_data.get("tier") == "pro"


async def test_webhook_unknown_event_type_is_ignored():
    event = _make_webhook_payload("payment_intent.created", {"id": "pi_123"})

    with patch("backend.webhooks.stripe_webhook.stripe") as mock_stripe:
        mock_stripe.Webhook.construct_event.return_value = event
        mock_stripe.error = MagicMock()
        mock_stripe.error.SignatureVerificationError = Exception

        with patch("backend.webhooks.stripe_webhook.supabase") as sb:
            async with AsyncClient(app=app, base_url="http://test") as client:
                r = await client.post(
                    "/webhooks/stripe",
                    content=b"{}",
                    headers={"stripe-signature": "valid", "content-type": "application/json"},
                )
            sb.table.assert_not_called()

    assert r.status_code == 200
