"""
Day 2 Tests — AI Analysis & Recommendations Pipeline

Run:  pytest backend/tests/test_day2_ai_pipeline.py -v

Covers:
  - backend/services/ai_analysis.py    (GPT-4o Vision call, response parsing)
  - backend/services/recommendations.py (follow-up prompt, 5 recs returned)
  - backend/models/analysis.py         (Pydantic model validation)
  - POST /api/analyze                  (full endpoint: upload → analyze → recs → DB write)
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from backend.main import app
from backend.models.analysis import AnalysisResult, Recommendation
from backend.tests.conftest import (
    IMAGE_URL,
    MOCK_ANALYSIS_DATA,
    MOCK_RECS_DATA,
    MOCK_USER,
    make_upload_file,
)


# ── Model validation ──────────────────────────────────────────────────────────

def test_analysis_result_valid():
    result = AnalysisResult(**MOCK_ANALYSIS_DATA)
    assert result.labels == MOCK_ANALYSIS_DATA["labels"]
    assert result.description == MOCK_ANALYSIS_DATA["description"]
    assert isinstance(result.objects, list)
    assert isinstance(result.attributes, dict)


def test_analysis_result_missing_field_raises():
    with pytest.raises(Exception):
        AnalysisResult(labels=["tag"], description="desc")  # missing objects + attributes


def test_recommendation_valid():
    rec = Recommendation(**MOCK_RECS_DATA[0])
    assert rec.title == "Visit a park"
    assert 0.0 <= rec.relevance_score <= 1.0


def test_recommendation_score_stored_as_float():
    rec = Recommendation(title="Test", description="Desc", relevance_score=0.88)
    assert isinstance(rec.relevance_score, float)


# ── ai_analysis service ───────────────────────────────────────────────────────

async def test_analyze_image_calls_openai_with_image_url():
    from backend.services.ai_analysis import analyze_image

    mock_message = MagicMock()
    mock_message.content = json.dumps(MOCK_ANALYSIS_DATA)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("backend.services.ai_analysis.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        result = await analyze_image(IMAGE_URL)

    call_args = mock_client.chat.completions.create.call_args
    content = call_args.kwargs["messages"][0]["content"]
    image_part = next(p for p in content if p["type"] == "image_url")
    assert image_part["image_url"]["url"] == IMAGE_URL


async def test_analyze_image_returns_analysis_result():
    from backend.services.ai_analysis import analyze_image

    mock_message = MagicMock()
    mock_message.content = json.dumps(MOCK_ANALYSIS_DATA)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("backend.services.ai_analysis.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        result = await analyze_image(IMAGE_URL)

    assert isinstance(result, AnalysisResult)
    assert result.labels == MOCK_ANALYSIS_DATA["labels"]
    assert result.description == MOCK_ANALYSIS_DATA["description"]


async def test_analyze_image_uses_gpt4o_model():
    from backend.services.ai_analysis import analyze_image

    mock_message = MagicMock()
    mock_message.content = json.dumps(MOCK_ANALYSIS_DATA)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("backend.services.ai_analysis.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        await analyze_image(IMAGE_URL)

    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o"


async def test_analyze_image_requests_json_response_format():
    from backend.services.ai_analysis import analyze_image

    mock_message = MagicMock()
    mock_message.content = json.dumps(MOCK_ANALYSIS_DATA)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("backend.services.ai_analysis.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        await analyze_image(IMAGE_URL)

    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs.get("response_format") == {"type": "json_object"}


# ── recommendations service ───────────────────────────────────────────────────

async def test_generate_recommendations_returns_five():
    from backend.services.recommendations import generate_recommendations

    mock_message = MagicMock()
    mock_message.content = json.dumps({"recommendations": MOCK_RECS_DATA})
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("backend.services.recommendations.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        analysis = AnalysisResult(**MOCK_ANALYSIS_DATA)
        recs = await generate_recommendations(analysis)

    assert len(recs) == 5
    assert all(isinstance(r, Recommendation) for r in recs)


async def test_generate_recommendations_caps_at_five_even_if_more_returned():
    from backend.services.recommendations import generate_recommendations

    more_than_five = MOCK_RECS_DATA + [
        {"title": "Extra rec", "description": "Extra.", "relevance_score": 0.5}
    ]
    mock_message = MagicMock()
    mock_message.content = json.dumps({"recommendations": more_than_five})
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("backend.services.recommendations.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        analysis = AnalysisResult(**MOCK_ANALYSIS_DATA)
        recs = await generate_recommendations(analysis)

    assert len(recs) == 5


async def test_generate_recommendations_sends_analysis_in_prompt():
    from backend.services.recommendations import generate_recommendations

    mock_message = MagicMock()
    mock_message.content = json.dumps({"recommendations": MOCK_RECS_DATA})
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("backend.services.recommendations.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        analysis = AnalysisResult(**MOCK_ANALYSIS_DATA)
        await generate_recommendations(analysis)

    prompt_text = mock_client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "labels" in prompt_text or "outdoor" in prompt_text


# ── POST /api/analyze endpoint ────────────────────────────────────────────────

async def test_analyze_endpoint_requires_auth():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post("/api/analyze")
    assert r.status_code == 422


async def test_analyze_endpoint_rejects_pdf(mock_current_user):
    with patch("backend.routes.analyze.check_and_increment_usage", new_callable=AsyncMock):
        with patch("backend.routes.analyze.upload_image", new_callable=AsyncMock) as mock_upload:
            # Storage will raise 400 for PDF
            from fastapi import HTTPException
            mock_upload.side_effect = HTTPException(status_code=400, detail="Only JPEG, PNG, and WEBP images are allowed")
            async with AsyncClient(app=app, base_url="http://test") as client:
                r = await client.post(
                    "/api/analyze",
                    files={"file": ("doc.pdf", b"fake", "application/pdf")},
                    headers={"Authorization": "Bearer token"},
                )
    assert r.status_code == 400
    assert "JPEG" in r.json()["detail"] or "allowed" in r.json()["detail"].lower()


async def test_analyze_endpoint_full_pipeline_success(mock_current_user):
    analysis_obj = AnalysisResult(**MOCK_ANALYSIS_DATA)
    rec_objects = [Recommendation(**r) for r in MOCK_RECS_DATA]

    with patch("backend.routes.analyze.check_and_increment_usage", new_callable=AsyncMock):
        with patch("backend.routes.analyze.upload_image", new_callable=AsyncMock, return_value=IMAGE_URL):
            with patch("backend.routes.analyze.analyze_image", new_callable=AsyncMock, return_value=analysis_obj):
                with patch("backend.routes.analyze.generate_recommendations", new_callable=AsyncMock, return_value=rec_objects):
                    with patch("backend.routes.analyze.supabase") as mock_sb:
                        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock()
                        async with AsyncClient(app=app, base_url="http://test") as client:
                            r = await client.post(
                                "/api/analyze",
                                files={"file": ("photo.jpg", b"fake-jpeg", "image/jpeg")},
                                headers={"Authorization": "Bearer token"},
                            )

    assert r.status_code == 200
    data = r.json()
    assert data["image_url"] == IMAGE_URL
    assert data["analysis"]["labels"] == MOCK_ANALYSIS_DATA["labels"]
    assert len(data["recommendations"]) == 5
    assert "id" in data
    assert "created_at" in data


async def test_analyze_endpoint_writes_to_db(mock_current_user):
    analysis_obj = AnalysisResult(**MOCK_ANALYSIS_DATA)
    rec_objects = [Recommendation(**r) for r in MOCK_RECS_DATA]
    insert_calls = []

    with patch("backend.routes.analyze.check_and_increment_usage", new_callable=AsyncMock):
        with patch("backend.routes.analyze.upload_image", new_callable=AsyncMock, return_value=IMAGE_URL):
            with patch("backend.routes.analyze.analyze_image", new_callable=AsyncMock, return_value=analysis_obj):
                with patch("backend.routes.analyze.generate_recommendations", new_callable=AsyncMock, return_value=rec_objects):
                    with patch("backend.routes.analyze.supabase") as mock_sb:
                        def capture_insert(data):
                            insert_calls.append(data)
                            return MagicMock(execute=MagicMock(return_value=MagicMock()))

                        mock_sb.table.return_value.insert.side_effect = capture_insert
                        async with AsyncClient(app=app, base_url="http://test") as client:
                            await client.post(
                                "/api/analyze",
                                files={"file": ("photo.jpg", b"fake-jpeg", "image/jpeg")},
                                headers={"Authorization": "Bearer token"},
                            )

    assert len(insert_calls) == 1
    record = insert_calls[0]
    assert record["user_id"] == MOCK_USER["id"]
    assert record["image_url"] == IMAGE_URL
    assert "analysis" in record
    assert "recommendations" in record


async def test_analyze_endpoint_increments_usage(mock_current_user):
    analysis_obj = AnalysisResult(**MOCK_ANALYSIS_DATA)
    rec_objects = [Recommendation(**r) for r in MOCK_RECS_DATA]

    with patch("backend.routes.analyze.check_and_increment_usage", new_callable=AsyncMock) as mock_usage:
        with patch("backend.routes.analyze.upload_image", new_callable=AsyncMock, return_value=IMAGE_URL):
            with patch("backend.routes.analyze.analyze_image", new_callable=AsyncMock, return_value=analysis_obj):
                with patch("backend.routes.analyze.generate_recommendations", new_callable=AsyncMock, return_value=rec_objects):
                    with patch("backend.routes.analyze.supabase") as mock_sb:
                        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock()
                        async with AsyncClient(app=app, base_url="http://test") as client:
                            await client.post(
                                "/api/analyze",
                                files={"file": ("photo.jpg", b"fake-jpeg", "image/jpeg")},
                                headers={"Authorization": "Bearer token"},
                            )

    mock_usage.assert_awaited_once_with(MOCK_USER["id"])
