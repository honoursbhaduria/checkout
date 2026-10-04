import os
import io
import tempfile
import logging
from typing import Optional
from faster_whisper import WhisperModel
from app.ai.contracts import STTProvider

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
        try:
            model = self._get_model()
            # Determine extension based on magic header if possible, or default to webm
            ext = ".webm"
            if audio_bytes.startswith(b"RIFF"):
                ext = ".wav"
            elif audio_bytes.startswith(b"OggS"):
                ext = ".ogg"
            elif audio_bytes.startswith(b"\x1a\x45\xdf\xa3"):
                ext = ".webm"

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            segments, info = model.transcribe(tmp_path, beam_size=5, language="en")
            transcript_parts = [segment.text.strip() for segment in segments]
            transcript = " ".join(transcript_parts).strip()
            logger.info(f"faster-whisper transcribed {len(audio_bytes)} bytes into: '{transcript}'")
            return transcript
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}", exc_info=True)
            return ""
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
