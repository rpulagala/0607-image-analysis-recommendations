import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from backend.main import app

MOCK_USER = {"id": "user-123", "email": "test@test.com"}

MOCK_ANALYSIS = {
    "labels": ["outdoor", "sunny"],
    "description": "A sunny outdoor scene.",
    "objects": ["tree", "sky"],
    "attributes": {"mood": "bright"},
}

MOCK_RECOMMENDATIONS = [
    {"title": "Visit a park", "description": "Enjoy nature.", "relevance_score": 0.9},
    {"title": "Take a walk", "description": "Go outside.", "relevance_score": 0.8},
    {"title": "Plan a picnic", "description": "Bring food.", "relevance_score": 0.75},
    {"title": "Try photography", "description": "Capture moments.", "relevance_score": 0.7},
    {"title": "Join a club", "description": "Meet others.", "relevance_score": 0.65},
]


@pytest.mark.asyncio
async def test_analyze_unauthenticated():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/analyze")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_rejects_non_image():
    with patch("backend.routes.analyze.get_current_user", return_value=MOCK_USER):
        with patch("backend.routes.analyze.check_and_increment_usage", new_callable=AsyncMock):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/analyze",
                    files={"file": ("doc.pdf", b"fake", "application/pdf")},
                    headers={"Authorization": "Bearer token"},
                )
    assert response.status_code == 400
    assert "JPEG" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analyze_full_pipeline():
    with patch("backend.routes.analyze.get_current_user", return_value=MOCK_USER):
        with patch("backend.routes.analyze.check_and_increment_usage", new_callable=AsyncMock):
            with patch("backend.routes.analyze.upload_image", new_callable=AsyncMock, return_value="https://cdn.example.com/img.jpg"):
                with patch("backend.routes.analyze.analyze_image", new_callable=AsyncMock) as mock_analysis:
                    with patch("backend.routes.analyze.generate_recommendations", new_callable=AsyncMock) as mock_recs:
                        from backend.models.analysis import AnalysisResult, Recommendation

                        mock_analysis.return_value = AnalysisResult(**MOCK_ANALYSIS)
                        mock_recs.return_value = [Recommendation(**r) for r in MOCK_RECOMMENDATIONS]

                        with patch("backend.routes.analyze.supabase"):
                            async with AsyncClient(app=app, base_url="http://test") as client:
                                response = await client.post(
                                    "/api/analyze",
                                    files={"file": ("photo.jpg", b"fake-image", "image/jpeg")},
                                    headers={"Authorization": "Bearer token"},
                                )

    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert len(data["recommendations"]) == 5
