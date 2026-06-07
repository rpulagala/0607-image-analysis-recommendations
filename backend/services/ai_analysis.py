import json

from openai import AsyncOpenAI

from backend.config import settings
from backend.models.analysis import AnalysisResult

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

_PROMPT = """Analyze this image and return a JSON object with exactly these keys:
- labels: list of 5-10 descriptive tags
- description: 2-3 sentence description of the image
- objects: list of main objects or subjects detected
- attributes: dict of notable attributes (color, style, mood, condition, etc.)

Return only valid JSON, no markdown."""


async def analyze_image(image_url: str) -> AnalysisResult:
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url, "detail": "high"}},
                    {"type": "text", "text": _PROMPT},
                ],
            }
        ],
        max_tokens=800,
        response_format={"type": "json_object"},
    )
    raw = json.loads(response.choices[0].message.content)
    return AnalysisResult(**raw)
