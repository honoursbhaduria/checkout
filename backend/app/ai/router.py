import logging
from typing import Optional
from app.ai.contracts import LLMProvider, STTProvider, TTSProvider
from app.ai.providers.smart_engine import smart_engine, SmartIntelligenceEngine
from app.ai.providers.gemini_adapter import GeminiProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIRouter:
    def __init__(self):
        self._smart_engine = smart_engine
        self._gemini = GeminiProvider() if settings.GEMINI_API_KEY else None

    def get_llm_provider(self) -> LLMProvider:
        if settings.DEFAULT_AI_PROVIDER == "gemini" and self._gemini:
            return self._gemini
        return self._smart_engine

    def get_stt_provider(self) -> STTProvider:
        return self._smart_engine

    def get_tts_provider(self) -> TTSProvider:
        return self._smart_engine

    def get_intelligence_engine(self) -> SmartIntelligenceEngine:
        return self._smart_engine


ai_router = AIRouter()
