import logging
import subprocess
import shutil
from typing import Optional
from app.ai.contracts import TTSProvider

logger = logging.getLogger(__name__)


class PiperTTSProvider(TTSProvider):
    """
    Local Text-to-Speech using Piper (ultra-fast, local neural TTS).
    Zero cloud cost, produces natural speech WAV offline.
    """

    def __init__(self, voice_model: str = "en_US-lessac-medium"):
        self.voice_model = voice_model
        self.has_piper = shutil.which("piper") is not None

    async def synthesize(self, text: str) -> bytes:
        if self.has_piper:
            try:
                process = subprocess.Popen(
                    ["piper", "--model", self.voice_model, "--output_stdout"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, _ = process.communicate(input=text.encode("utf-8"))
                if process.returncode == 0:
                    return stdout
            except Exception as e:
                logger.warning(f"Piper binary execution failed: {e}. Delegating to client speech synthesis.")

        # In browser environments or when Piper binary is absent, return empty bytes
        # Frontend detects empty audio and uses Web Speech API (window.speechSynthesis)
        return b""
