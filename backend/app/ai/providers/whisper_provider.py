import os
import io
import asyncio
import hashlib
import logging
from collections import OrderedDict
from typing import Optional
from faster_whisper import WhisperModel
from app.ai.contracts import STTProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class FasterWhisperProvider(STTProvider):
    def __init__(
        self,
        model_size: str = "tiny.en",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        is_render = bool(os.environ.get("RENDER") or os.environ.get("RENDER_SERVICE_ID"))
        if is_render:
            # Render Free Tier: 512 MB RAM, 0.1 shared vCPU — single thread avoids CPU throttling
            self.cpu_threads = 1
            self.num_workers = 1
            self._max_cache_size = 100
        else:
            self.cpu_threads = min(4, max(2, (os.cpu_count() or 4) // 2))
            self.num_workers = 1
            self._max_cache_size = 250
        self._model: Optional[WhisperModel] = None
        self._cache: OrderedDict[str, str] = OrderedDict()

    def _get_model(self) -> Optional[WhisperModel]:
        if self._model is None:
            try:
                logger.info(f"Loading faster-whisper model '{self.model_size}' with {self.cpu_threads} threads...")
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    cpu_threads=self.cpu_threads,
                    num_workers=self.num_workers
                )
                logger.info("faster-whisper model loaded successfully.")
            except Exception as e:
                logger.warning(f"Failed to load faster-whisper model (e.g. low memory on free tier): {e}")
                self._model = False
        return self._model if self._model is not False else None

    async def health_check(self) -> bool:
        return True

    def _sync_transcribe(self, audio_bytes: bytes, fast: bool = False) -> str:
        """Synchronous CPU-bound transcription executed in thread pool."""
        # On Render Free Tier or in fast mode, skip Silero VAD neural pass to save ~50MB RAM and 2-3s CPU latency
        is_render = bool(os.environ.get("RENDER") or os.environ.get("RENDER_SERVICE_ID"))
        use_vad = not fast and not is_render

        try:
            model = self._get_model()
            if not model:
                return ""
            # Fast in-memory buffer decode using PyAV
            audio_io = io.BytesIO(audio_bytes)
            segments, _ = model.transcribe(
                audio_io,
                beam_size=1,
                best_of=1,
                temperature=0.0,
                language="en",
                condition_on_previous_text=False,
                without_timestamps=True,
                suppress_blank=True,
                vad_filter=use_vad,
                vad_parameters=dict(min_silence_duration_ms=250, speech_pad_ms=50) if use_vad else None
            )
            parts = [s.text.strip() for s in segments if s.text.strip()]
            return " ".join(parts).strip()
        except Exception as e:
            logger.debug(f"FasterWhisper in-memory decode warning: {e}, attempting temporary buffer fallback")
            tmp_path = None
            try:
                ext = ".webm"
                if audio_bytes.startswith(b"RIFF"):
                    ext = ".wav"
                elif audio_bytes.startswith(b"OggS"):
                    ext = ".ogg"
                elif audio_bytes.startswith(b"ID3") or (len(audio_bytes) > 2 and audio_bytes[:2] == b"\xff\xfb"):
                    ext = ".mp3"
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp.write(audio_bytes)
                    tmp_path = tmp.name

                segments, _ = model.transcribe(
                    tmp_path,
                    beam_size=1,
                    best_of=1,
                    temperature=0.0,
                    language="en",
                    condition_on_previous_text=False,
                    without_timestamps=True,
                    suppress_blank=True,
                    vad_filter=use_vad,
                )
                parts = [s.text.strip() for s in segments if s.text.strip()]
                return " ".join(parts).strip()
            except Exception as e2:
                logger.warning(f"FasterWhisper temp buffer fallback failed: {e2}")
                return ""
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

    async def _groq_transcribe(self, audio_bytes: bytes) -> Optional[str]:
        groq_key = os.environ.get("GROQ_API_KEY") or getattr(settings, "GROQ_API_KEY", None)
        if not groq_key:
            return None
        try:
            import httpx
            ext = "wav" if audio_bytes.startswith(b"RIFF") else ("ogg" if audio_bytes.startswith(b"OggS") else "mp3")
            files = {"file": (f"audio.{ext}", audio_bytes, f"audio/{ext}")}
            data = {"model": "whisper-large-v3-turbo", "language": "en"}
            headers = {"Authorization": f"Bearer {groq_key}"}
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.post("https://api.groq.com/openai/v1/audio/transcriptions", files=files, data=data, headers=headers)
                if resp.status_code == 200:
                    text = resp.json().get("text", "").strip()
                    if text:
                        logger.info(f"Groq Whisper transcribed {len(audio_bytes)} bytes in cloud: '{text}'")
                        return text
        except Exception as e:
            logger.debug(f"Groq Whisper fallback bypass: {e}")
        return None

    async def transcribe_audio(self, audio_bytes: bytes, fast: bool = False) -> str:
        if not audio_bytes or len(audio_bytes) < 300:
            return ""

        # Check in-memory transcription cache (instant return for duplicate/identical audio)
        cache_key = hashlib.md5(audio_bytes[:4096] + len(audio_bytes).to_bytes(4, "big")).hexdigest()
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        # 1. Cloud-accelerated Groq Whisper (~150ms) if GROQ_API_KEY is configured
        groq_text = await self._groq_transcribe(audio_bytes)
        if groq_text:
            if len(self._cache) >= self._max_cache_size:
                self._cache.popitem(last=False)
            self._cache[cache_key] = groq_text
            return groq_text

        # 2. Execute optimized FasterWhisper in worker thread (non-blocking for FastAPI event loop)
        transcript = await asyncio.to_thread(self._sync_transcribe, audio_bytes, fast)

        if transcript:
            logger.info(f"faster-whisper transcribed {len(audio_bytes)} bytes into: '{transcript}'")
            # Store in cache
            if len(self._cache) >= self._max_cache_size:
                self._cache.popitem(last=False)
            self._cache[cache_key] = transcript
            return transcript

        # 2. Strict fast fallback: If faster-whisper returned empty on a final full recording
        # and Gemini is available, call Gemini STT with a short 3s timeout
        if not transcript and not fast and settings.GEMINI_API_KEY:
            try:
                import base64
                import httpx
                ext = ".webm"
                if audio_bytes.startswith(b"RIFF"):
                    ext = ".wav"
                mime = "audio/webm" if ext == ".webm" else "audio/wav"
                b64_data = base64.b64encode(audio_bytes).decode("utf-8")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"inlineData": {"mimeType": mime, "data": b64_data}},
                            {"text": "Transcribe the spoken English words accurately word for word. If silent, return empty. Return ONLY transcription text."}
                        ]
                    }]
                }
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        cand = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        if cand and cand.upper() != "SILENCE" and cand.lower() != "empty":
                            transcript = cand
                            logger.info(f"Gemini Flash STT transcribed audio: '{transcript}'")
            except Exception as e:
                logger.debug(f"Gemini Flash audio fallback: {e}")

        if transcript:
            if len(self._cache) >= self._max_cache_size:
                self._cache.popitem(last=False)
            self._cache[cache_key] = transcript

        return transcript
