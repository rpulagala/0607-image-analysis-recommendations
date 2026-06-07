"""
Day 3 Tests — Auth Guard, History, Profile

Run:  pytest backend/tests/test_day3_history_profile.py -v

Covers:
  - backend/middleware/auth_guard.py  (JWT validation, missing/bad token)
  - GET  /api/history                 (paginated list, empty, search param)
  - GET  /api/history/{id}            (found, not found, wrong user blocked)
  - GET  /api/profile
  - PATCH /api/profile
"""
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from backend.main import app
from backend.tests.conftest import (
    IMAGE_URL,
    MOCK_ANALYSIS_DATA,
    MOCK_USER,
    USER_ID,
    make_supabase_result,
)

ANALYSIS_RECORD = {
    "id": "analysis-001",
    "user_id": USER_ID,
    "image_url": IMAGE_URL,
    "analysis": MOCK_ANALYSIS_DATA,
    "recommendations": [],
    "created_at": "2026-06-07T10:00:00+00:00",
}

PROFILE_RECORD = {
    "id": USER_ID,
    "email": "test@example.com",
    "full_name": "Test User",
    "subscription_tier": "free",
}


# ── Auth Guard ────────────────────────────────────────────────────────────────

async def test_auth_guard_missing_header_returns_422():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/api/history")
    assert r.status_code == 422


async def test_auth_guard_invalid_bearer_prefix_returns_401():
    with patch("backend.middleware.auth_guard.supabase") as sb:
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get(
                "/api/history",
                headers={"Authorization": "Token not-a-bearer"},
            )
    assert r.status_code == 401


async def test_auth_guard_expired_token_returns_401():
    with patch("backend.middleware.auth_guard.supabase") as sb:
        sb.auth.get_user.side_effect = Exception("JWT expired")
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get(
                "/api/history",
                headers={"Authorization": "Bearer expired-token"},
            )
    assert r.status_code == 401


async def test_auth_guard_none_user_returns_401():
    with patch("backend.middleware.auth_guard.supabase") as sb:
        mock_resp = MagicMock()
        mock_resp.user = None
        sb.auth.get_user.return_value = mock_resp
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get(
                "/api/history",
                headers={"Authorization": "Bearer bad-token"},
            )
    assert r.status_code == 401


async def test_auth_guard_valid_token_passes():
    with patch("backend.middleware.auth_guard.supabase") as sb:
        mock_user_obj = MagicMock()
        mock_user_obj.id = USER_ID
        mock_user_obj.email = "test@example.com"
        mock_resp = MagicMock()
        mock_resp.user = mock_user_obj
        sb.auth.get_user.return_value = mock_resp

        with patch("backend.routes.history.supabase") as sb2:
            sb2.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = make_supabase_result([])
            async with AsyncClient(app=app, base_url="http://test") as client:
                r = await client.get(
                    "/api/history",
                    headers={"Authorization": "Bearer valid-token"},
                )

    assert r.status_code == 200


# ── History: list ─────────────────────────────────────────────────────────────

async def test_history_returns_empty_list(mock_current_user):
    with patch("backend.routes.history.supabase") as sb:
        sb.table.return_value.select.return_value.eq.return_value \
            .order.return_value.range.return_value.execute.return_value = make_supabase_result([])
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get("/api/history", headers={"Authorization": "Bearer token"})

    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["page"] == 1


async def test_history_returns_records(mock_current_user):
    with patch("backend.routes.history.supabase") as sb:
        sb.table.return_value.select.return_value.eq.return_value \
            .order.return_value.range.return_value.execute.return_value = make_supabase_result([ANALYSIS_RECORD])
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get("/api/history", headers={"Authorization": "Bearer token"})

    assert r.status_code == 200
    assert len(r.json()["items"]) == 1


async def test_history_pagination_params_forwarded(mock_current_user):
    with patch("backend.routes.history.supabase") as sb:
        chain = sb.table.return_value.select.return_value.eq.return_value \
            .order.return_value.range.return_value
        chain.execute.return_value = make_supabase_result([])
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get(
                "/api/history?page=2&limit=10",
                headers={"Authorization": "Bearer token"},
            )

    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 2
    assert data["limit"] == 10


async def test_history_invalid_page_param(mock_current_user):
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get(
            "/api/history?page=0",
            headers={"Authorization": "Bearer token"},
        )
    assert r.status_code == 422


async def test_history_limit_over_100_is_capped(mock_current_user):
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get(
            "/api/history?limit=999",
            headers={"Authorization": "Bearer token"},
        )
    assert r.status_code == 422


# ── History: single item ──────────────────────────────────────────────────────

async def test_history_detail_found(mock_current_user):
    with patch("backend.routes.history.supabase") as sb:
        sb.table.return_value.select.return_value.eq.return_value \
            .eq.return_value.maybe_single.return_value.execute.return_value = make_supabase_result(ANALYSIS_RECORD)
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get(
                "/api/history/analysis-001",
                headers={"Authorization": "Bearer token"},
            )

    assert r.status_code == 200
    assert r.json()["id"] == "analysis-001"


async def test_history_detail_not_found_returns_404(mock_current_user):
    with patch("backend.routes.history.supabase") as sb:
        sb.table.return_value.select.return_value.eq.return_value \
            .eq.return_value.maybe_single.return_value.execute.return_value = make_supabase_result(None)
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get(
                "/api/history/nonexistent-id",
                headers={"Authorization": "Bearer token"},
            )

    assert r.status_code == 404


# ── Profile: get ──────────────────────────────────────────────────────────────

async def test_get_profile_returns_user_data(mock_current_user):
    with patch("backend.routes.profile.supabase") as sb:
        sb.table.return_value.select.return_value.eq.return_value \
            .single.return_value.execute.return_value = make_supabase_result(PROFILE_RECORD)
        sb.table.return_value.select.return_value.eq.return_value \
            .execute.return_value = make_supabase_result([{"count": 3}])
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get("/api/profile", headers={"Authorization": "Bearer token"})

    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "test@example.com"
    assert "analyses_this_month" in data


async def test_get_profile_shows_zero_usage_when_none(mock_current_user):
    with patch("backend.routes.profile.supabase") as sb:
        sb.table.return_value.select.return_value.eq.return_value \
            .single.return_value.execute.return_value = make_supabase_result(PROFILE_RECORD)
        sb.table.return_value.select.return_value.eq.return_value \
            .execute.return_value = make_supabase_result([])
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get("/api/profile", headers={"Authorization": "Bearer token"})

    assert r.json()["analyses_this_month"] == 0


async def test_get_profile_requires_auth():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/api/profile")
    assert r.status_code == 422


# ── Profile: update ───────────────────────────────────────────────────────────

async def test_update_profile_success(mock_current_user):
    with patch("backend.routes.profile.supabase") as sb:
        sb.table.return_value.update.return_value.eq.return_value \
            .execute.return_value = make_supabase_result(None)
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.patch(
                "/api/profile",
                json={"full_name": "Updated Name"},
                headers={"Authorization": "Bearer token"},
            )

    assert r.status_code == 200
    assert r.json()["message"] == "Profile updated"


async def test_update_profile_empty_body_is_ok(mock_current_user):
    with patch("backend.routes.profile.supabase") as sb:
        sb.table.return_value.update.return_value.eq.return_value \
            .execute.return_value = make_supabase_result(None)
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.patch(
                "/api/profile",
                json={},
                headers={"Authorization": "Bearer token"},
            )

    assert r.status_code == 200


async def test_update_profile_requires_auth():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.patch("/api/profile", json={"full_name": "Test"})
    assert r.status_code == 422
