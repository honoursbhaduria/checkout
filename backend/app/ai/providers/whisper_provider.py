import os
import io
import tempfile
import logging
from typing import Optional
from faster_whisper import WhisperModel
from app.ai.contracts import STTProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class FasterWhisperProvider(STTProvider):
    def __init__(self, model_size: str = "tiny.en", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None

    def _get_model(self) -> WhisperModel:
        if self._model is None:
            logger.info(f"Loading faster-whisper model '{self.model_size}'...")
            self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            logger.info("faster-whisper model loaded successfully.")
        return self._model

    async def health_check(self) -> bool:
        return True

    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        if not audio_bytes or len(audio_bytes) < 100:
            return ""

        tmp_path = None
        transcript = ""

        # Determine extension based on magic header if possible, or default to webm
        ext = ".webm"
        if audio_bytes.startswith(b"RIFF"):
            ext = ".wav"
        elif audio_bytes.startswith(b"OggS"):
            ext = ".ogg"
        elif audio_bytes.startswith(b"\x1a\x45\xdf\xa3"):
            ext = ".webm"

        # 1. Try local faster-whisper
        try:
            model = self._get_model()
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            segments, info = model.transcribe(tmp_path, beam_size=1, language="en", vad_filter=True)
            transcript_parts = [segment.text.strip() for segment in segments]
            transcript = " ".join(transcript_parts).strip()
            if not transcript:
                # Retry without vad_filter in case VAD was too aggressive on short audio slice
                segments, info = model.transcribe(tmp_path, beam_size=1, language="en", vad_filter=False)
                transcript_parts = [segment.text.strip() for segment in segments]
                transcript = " ".join(transcript_parts).strip()
            if transcript:
                logger.info(f"faster-whisper transcribed {len(audio_bytes)} bytes into: '{transcript}'")
        except Exception as e:
            logger.warning(f"Local faster-whisper transcription warning: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        # 2. If faster-whisper returned empty, try Gemini 2.5 Flash Multimodal Audio STT
        if not transcript and settings.GEMINI_API_KEY:
            try:
                import base64
                import httpx
                b64_data = base64.b64encode(audio_bytes).decode("utf-8")
                mime = "audio/webm" if ext == ".webm" else "audio/wav"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"inlineData": {"mimeType": mime, "data": b64_data}},
                            {"text": "Transcribe the spoken English words in this audio recording accurately word for word. If silent or empty, return nothing. Return ONLY the transcription text, no preamble."}
                        ]
                    }]
                }
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        cand = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        if cand and cand.upper() != "SILENCE" and cand.lower() != "empty":
                            transcript = cand
                            logger.info(f"Gemini Flash STT transcribed audio: '{transcript}'")
            except Exception as e:
                logger.warning(f"Gemini Flash audio fallback warning: {e}")

        return transcript
