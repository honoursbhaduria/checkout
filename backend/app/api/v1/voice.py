import json
import logging
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from pydantic import BaseModel
from app.ai.router import ai_router
from app.domain.schemas import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice Engine"])


class TranscribeRequest(BaseModel):
    audio_base64: str


class SynthesizeRequest(BaseModel):
    text: str


import base64
from fastapi import UploadFile, File

@router.post("/transcribe")
async def transcribe_audio_rest(data: TranscribeRequest):
    engine = ai_router.get_stt_provider()
    audio_bytes = b""
    if data.audio_base64:
        try:
            b64 = data.audio_base64
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            audio_bytes = base64.b64decode(b64)
        except Exception as e:
            logger.error(f"Failed to decode base64 audio: {e}")

    transcript = await engine.transcribe_audio(audio_bytes)
    return APIResponse(data={"transcript": transcript})


@router.post("/transcribe-file")
async def transcribe_audio_file(file: UploadFile = File(...), fast: bool = False):
    engine = ai_router.get_stt_provider()
    audio_bytes = await file.read()
    transcript = await engine.transcribe_audio(audio_bytes, fast=fast)
    return APIResponse(data={"transcript": transcript})


@router.post("/synthesize")
async def synthesize_text_rest(data: SynthesizeRequest):
    """Server-side neural TTS via Gemini (works even when OS has no local voices).
    Falls back to client speechSynthesis mode when unavailable."""
    import httpx
    from app.core.config import settings

    text = (data.text or "").strip()
    if not text:
        return APIResponse(data={"status": "ready", "mode": "client_speech_synthesis"})
    # Cap length to keep TTS fast
    if len(text) > 800:
        text = text[:800]

    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": f"Say naturally, at a steady interview pace: {text}"}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}},
                },
            }
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    body = resp.json()
                    # Collect EVERY audio part — long texts come back split across
                    # multiple parts; playing only the first one cuts speech off mid-way.
                    pcm_chunks: list[bytes] = []
                    rate = 24000
                    for cand in body.get("candidates", []):
                        for part in cand.get("content", {}).get("parts", []):
                            inline = part.get("inlineData") or {}
                            b64 = inline.get("data")
                            if not b64:
                                continue
                            import base64 as _b64
                            raw = _b64.b64decode(b64)
                            if raw[:4] == b"RIFF":
                                # Already containerized — use as-is
                                return APIResponse(data={
                                    "status": "ready",
                                    "mode": "server_tts",
                                    "audio_base64": b64,
                                    "mime_type": inline.get("mimeType", "audio/wav"),
                                })
                            m = (inline.get("mimeType") or "").lower()
                            if "rate=16000" in m or "16000" in m:
                                rate = 16000
                            pcm_chunks.append(raw)
                    if pcm_chunks:
                        import base64 as _b64
                        import struct as _struct
                        pcm = b"".join(pcm_chunks)
                        n = len(pcm)
                        header = _struct.pack(
                            "<4sI4s4sIHHIIHH4sI",
                            b"RIFF", 36 + n, b"WAVE",
                            b"fmt ", 16, 1, 1, rate,
                            rate * 2, 2, 16,
                            b"data", n,
                        )
                        return APIResponse(data={
                            "status": "ready",
                            "mode": "server_tts",
                            "audio_base64": _b64.b64encode(header + pcm).decode("utf-8"),
                            "mime_type": "audio/wav",
                        })
                else:
                    logger.warning(f"Gemini TTS HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Gemini TTS fallback warning: {e}")

    return APIResponse(data={"status": "ready", "text": text, "mode": "client_speech_synthesis"})


@router.websocket("/sessions/{session_id}/stream")
async def voice_stream_websocket(websocket: WebSocket, session_id: str):
    """
    Bidirectional WebSocket connection for live voice interaction.
    Handles audio chunk ingestion, live transcription updates, and TTS question playback.
    """
    await websocket.accept()
    logger.info(f"Voice WebSocket connected for session {session_id}")

    try:
        # Send session confirmation
        await websocket.send_json({
            "type": "session.ready",
            "session_id": session_id,
            "sample_rate": 16000,
            "message": "Connected to AI Voice Engine"
        })

        while True:
            # Receive message (JSON control or binary audio)
            message = await websocket.receive()
            if "text" in message:
                payload = json.loads(message["text"])
                msg_type = payload.get("type")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "user.barge_in":
                    # Handle barge-in: immediately acknowledge and halt TTS audio streaming
                    await websocket.send_json({
                        "type": "server.interrupted",
                        "timestamp": payload.get("timestamp_ms")
                    })
                elif msg_type == "audio.finished":
                    # Emit simulated transcription confirmation
                    await websocket.send_json({
                        "type": "transcript.final",
                        "text": payload.get("transcript", "Transcript received successfully.")
                    })
            elif "bytes" in message:
                # Handle binary audio frame
                # In full Whisper stream, feed to audio ring buffer
                pass

    except WebSocketDisconnect:
        logger.info(f"Voice WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
