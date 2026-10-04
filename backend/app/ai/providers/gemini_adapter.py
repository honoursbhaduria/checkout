import json
import logging
import httpx
from typing import Any, Optional, Dict
from app.ai.contracts import LLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    async def health_check(self) -> bool:
        return bool(self.api_key)

    async def generate_text(self, prompt: str, system_prompt: str = "", temperature: float = 0.2) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        url = f"{self.base_url}?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"System Instructions: {system_prompt}\n\nUser Request: {prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def generate_structured(self, prompt: str, system_prompt: str, schema: Any) -> Any:
        # Prompt model with JSON schema directive
        json_prompt = (
            f"{prompt}\n\nIMPORTANT: Return ONLY a valid JSON object matching this schema:\n"
            f"{json.dumps(schema.model_json_schema())}"
        )
        raw_text = await self.generate_text(json_prompt, system_prompt, temperature=0.1)
        
        # Clean potential markdown fences ```json ... ```
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
        
        parsed = json.loads(cleaned)
        return schema.model_validate(parsed)
