import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from backend.main import app

MOCK_USER = {"id": "user-123", "email": "test@test.com"}


@pytest.mark.asyncio
async def test_usage_free_tier():
    with patch("backend.routes.billing.get_current_user", return_value=MOCK_USER):
        with patch(
            "backend.routes.billing.get_usage",
            new_callable=AsyncMock,
            return_value={"tier": "free", "used": 2, "limit": 5},
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/billing/usage",
                    headers={"Authorization": "Bearer token"},
                )
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "free"
    assert data["limit"] == 5


@pytest.mark.asyncio
async def test_usage_pro_tier():
    with patch("backend.routes.billing.get_current_user", return_value=MOCK_USER):
        with patch(
            "backend.routes.billing.get_usage",
            new_callable=AsyncMock,
            return_value={"tier": "pro", "used": 42, "limit": None},
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/billing/usage",
                    headers={"Authorization": "Bearer token"},
                )
    assert response.status_code == 200
    assert response.json()["limit"] is None


@pytest.mark.asyncio
async def test_checkout_returns_url():
    with patch("backend.routes.billing.get_current_user", return_value=MOCK_USER):
        with patch(
            "backend.routes.billing.create_checkout_session",
            new_callable=AsyncMock,
            return_value="https://checkout.stripe.com/pay/test_session",
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/billing/checkout",
                    json={
                        "price_id": "price_test123",
                        "success_url": "https://app.com/success",
                        "cancel_url": "https://app.com/cancel",
                    },
                    headers={"Authorization": "Bearer token"},
                )
    assert response.status_code == 200
    assert "stripe.com" in response.json()["url"]
