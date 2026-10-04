from abc import ABC, abstractmethod
from typing import AsyncGenerator, TypeVar, Optional, Dict, Any, List
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: str = "", temperature: float = 0.2) -> str:
        pass

    @abstractmethod
    async def generate_structured(self, prompt: str, system_prompt: str, schema: type[T]) -> T:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass


class STTProvider(ABC):
    @abstractmethod
    async def transcribe_audio(self, audio_bytes: bytes, fast: bool = False) -> str:
        """Transcribe audio. fast=True = single greedy pass for live slices (speed over accuracy)."""


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        pass
