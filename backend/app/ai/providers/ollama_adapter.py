import json
import logging
import httpx
from typing import Optional, TypeVar, Any
from pydantic import BaseModel
from app.ai.contracts import LLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class OllamaProvider(LLMProvider):
    """
    Local / Offline LLM Fallback using Ollama (e.g. llama3.2, mistral, deepseek-r1).
    Zero cloud cost, runs locally via Ollama HTTP REST API.
    """

    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL, model: str = "llama3.2"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def generate_text(self, prompt: str, system_prompt: str = "", temperature: float = 0.2) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": temperature}
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    return data.get("message", {}).get("content", "")
                raise RuntimeError(f"Ollama returned {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Ollama local execution failed: {e}. Falling back to SmartEngine.")
            raise

    async def generate_structured(self, prompt: str, system_prompt: str, schema: type[T]) -> T:
        schema_json = json.dumps(schema.model_json_schema())
        augmented_system = (
            f"{system_prompt}\nYou MUST output valid JSON adhering strictly to this JSON Schema:\n{schema_json}"
        )
        text = await self.generate_text(prompt, system_prompt=augmented_system, temperature=0.1)
        # Parse JSON
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            clean_json = text[start:end+1]
            return schema.model_validate_json(clean_json)
        return schema.model_validate_json(text)
