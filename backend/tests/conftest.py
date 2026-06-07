"""
Shared fixtures and test data for all day test suites.
os.environ MUST be set before any backend module is imported.
"""
import os

os.environ.update({
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_SERVICE_KEY": "test-service-key",
    "SUPABASE_ANON_KEY": "test-anon-key",
    "OPENAI_API_KEY": "sk-test-key",
    "STRIPE_SECRET_KEY": "sk_test_stripe",
    "STRIPE_WEBHOOK_SECRET": "whsec_test_secret",
    "STRIPE_PRO_PRICE_ID": "price_test123",
    "REDIS_URL": "redis://localhost:6379",
    "FREE_TIER_LIMIT": "5",
})

from unittest.mock import AsyncMock, MagicMock

import pytest

# ── Shared test constants ─────────────────────────────────────────────────────

USER_ID = "user-abc-123"
USER_EMAIL = "test@example.com"
MOCK_USER = {"id": USER_ID, "email": USER_EMAIL}
IMAGE_URL = "https://test.supabase.co/storage/v1/object/public/user-images/user-abc-123/img.jpg"

MOCK_ANALYSIS_DATA = {
    "labels": ["outdoor", "sunny", "nature", "greenery", "peaceful"],
    "description": "A bright outdoor scene with lush greenery and blue sky.",
    "objects": ["tree", "sky", "grass"],
    "attributes": {"mood": "bright", "style": "natural", "color": "green"},
}

MOCK_RECS_DATA = [
    {"title": "Visit a park", "description": "Enjoy nature outdoors.", "relevance_score": 0.95},
    {"title": "Try landscape photography", "description": "Capture the scenery.", "relevance_score": 0.88},
    {"title": "Plan a picnic", "description": "Pack food and relax outside.", "relevance_score": 0.80},
    {"title": "Join a hiking club", "description": "Meet fellow nature lovers.", "relevance_score": 0.75},
    {"title": "Buy a houseplant", "description": "Bring nature indoors.", "relevance_score": 0.70},
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def make_upload_file(filename: str, content: bytes, content_type: str) -> MagicMock:
    """Mock UploadFile for unit-testing services directly."""
    mock = MagicMock()
    mock.filename = filename
    mock.content_type = content_type
    mock.read = AsyncMock(return_value=content)
    return mock


def make_supabase_result(data: list | dict | None) -> MagicMock:
    """Mock the object returned by a supabase query .execute() call."""
    result = MagicMock()
    result.data = data
    return result


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-jwt-token"}


@pytest.fixture
def mock_current_user(monkeypatch):
    """Patch get_current_user across all route modules."""
    async def _fake_user(*args, **kwargs):
        return MOCK_USER

    monkeypatch.setattr("backend.routes.analyze.get_current_user", _fake_user)
    monkeypatch.setattr("backend.routes.history.get_current_user", _fake_user)
    monkeypatch.setattr("backend.routes.profile.get_current_user", _fake_user)
    monkeypatch.setattr("backend.routes.billing.get_current_user", _fake_user)
    return MOCK_USER
