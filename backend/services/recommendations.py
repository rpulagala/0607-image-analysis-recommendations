import json
from typing import List

from openai import AsyncOpenAI

from backend.config import settings
from backend.models.analysis import AnalysisResult, Recommendation

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

_PROMPT = """Based on this image analysis, provide exactly 5 personalized recommendations.

Analysis:
{analysis}

Return a JSON object with key "recommendations" containing an array of 5 objects, each with:
- title: short action title (max 6 words)
- description: 1-2 sentence recommendation
- relevance_score: float between 0.0 and 1.0

Return only valid JSON, no markdown."""


async def generate_recommendations(analysis: AnalysisResult) -> List[Recommendation]:
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": _PROMPT.format(analysis=analysis.model_dump_json())}
        ],
        max_tokens=600,
        response_format={"type": "json_object"},
    )
    raw = json.loads(response.choices[0].message.content)
    items = raw.get("recommendations", raw) if isinstance(raw, dict) else raw
    return [Recommendation(**item) for item in items[:5]]
