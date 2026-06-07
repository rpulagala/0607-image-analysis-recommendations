import pytest
from httpx import AsyncClient

from backend.main import app


@pytest.mark.asyncio
async def test_signup_missing_fields():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/auth/signup", json={"email": "test@test.com"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_signup_invalid_email():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/signup",
            json={"email": "not-an-email", "password": "pass123", "full_name": "Test"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_signin_invalid_credentials(mock_supabase_auth_fail):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/signin",
            json={"email": "bad@test.com", "password": "wrong"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_profile_requires_auth():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/profile")
    assert response.status_code == 422  # missing Authorization header
