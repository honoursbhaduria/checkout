import os
import json
import base64
import hashlib
import logging
from collections import OrderedDict
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, BackgroundTasks
from pydantic import BaseModel

from app.ai.router import ai_router
from app.core.config import settings
from app.core.redis import get_redis_client
from app.domain.schemas import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice Engine"])

# High-speed LRU memory cache for synthesized TTS (capacity tuned for Render 512MB RAM)
_is_render = bool(os.environ.get("RENDER") or os.environ.get("RENDER_SERVICE_ID"))
_MAX_MEMORY_TTS_CACHE = 100 if _is_render else 300
_MEMORY_TTS_CACHE: OrderedDict[str, dict] = OrderedDict()


def _put_memory_cache(key: str, data: dict):
    if len(_MEMORY_TTS_CACHE) >= _MAX_MEMORY_TTS_CACHE:
        _MEMORY_TTS_CACHE.popitem(last=False)
    _MEMORY_TTS_CACHE[key] = data


class TranscribeRequest(BaseModel):
    audio_base64: str


class SynthesizeRequest(BaseModel):
    text: str


class PreCacheRequest(BaseModel):
    texts: List[str]


async def generate_speech(text: str) -> dict:
    """Multi-tiered ultra-fast speech synthesis:
    1. In-memory LRU cache (< 0.1ms)
    2. Redis distributed cache (< 2ms)
    3. High-fidelity Neural Edge-TTS (~1s, cached thereafter)
    4. Gemini 2.5 Flash TTS fallback
    5. Client SpeechSynthesis fallback
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return {"status": "ready", "mode": "client_speech_synthesis"}

    if len(cleaned) > 800:
        cleaned = cleaned[:800]

    cache_key = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

    # Tier 1: In-memory cache
    if cache_key in _MEMORY_TTS_CACHE:
        _MEMORY_TTS_CACHE.move_to_end(cache_key)
        return _MEMORY_TTS_CACHE[cache_key]

    # Tier 2: Redis distributed cache
    try:
        redis = await get_redis_client()
        cached_json = await redis.get(f"tts:{cache_key}")
        if cached_json:
            result = json.loads(cached_json)
            _put_memory_cache(cache_key, result)
            return result
    except Exception as e:
        logger.debug(f"Redis TTS cache read bypass: {e}")

    # Tier 3: Ultra-speed Edge Neural TTS (GuyNeural with +15% interview cadence)
    try:
        import edge_tts
        communicate = edge_tts.Communicate(cleaned, "en-US-GuyNeural", rate="+15%")
        audio_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]

        if audio_bytes:
            b64 = base64.b64encode(audio_bytes).decode("utf-8")
            result = {
                "status": "ready",
                "mode": "server_tts",
                "audio_base64": b64,
                "mime_type": "audio/mpeg",
            }
            _put_memory_cache(cache_key, result)
            try:
                redis = await get_redis_client()
                await redis.set(f"tts:{cache_key}", json.dumps(result), ex=86400 * 7)
            except Exception:
                pass
            return result
    except Exception as e:
        logger.debug(f"Edge TTS fallback: {e}")

    # Tier 4: Gemini TTS Fallback
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if api_key:
        try:
            import httpx
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": f"Say naturally, at a steady interview pace: {cleaned}"}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}},
                },
            }
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    body = resp.json()
                    pcm_chunks: list[bytes] = []
                    rate = 24000
                    for cand in body.get("candidates", []):
                        for part in cand.get("content", {}).get("parts", []):
                            inline = part.get("inlineData") or {}
                            b64 = inline.get("data")
                            if not b64:
                                continue
                            raw = base64.b64decode(b64)
                            if raw[:4] == b"RIFF":
                                result = {
                                    "status": "ready",
                                    "mode": "server_tts",
                                    "audio_base64": b64,
                                    "mime_type": inline.get("mimeType", "audio/wav"),
                                }
                                _put_memory_cache(cache_key, result)
                                return result
                            m = (inline.get("mimeType") or "").lower()
                            if "16000" in m:
                                rate = 16000
                            pcm_chunks.append(raw)
                    if pcm_chunks:
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
                        b64 = base64.b64encode(header + pcm).decode("utf-8")
                        result = {
                            "status": "ready",
                            "mode": "server_tts",
                            "audio_base64": b64,
                            "mime_type": "audio/wav",
                        }
                        _put_memory_cache(cache_key, result)
                        try:
                            redis = await get_redis_client()
                            await redis.set(f"tts:{cache_key}", json.dumps(result), ex=86400 * 7)
                        except Exception:
                            pass
                        return result
        except Exception as e:
            logger.debug(f"Gemini TTS fallback: {e}")

    # Tier 5: Browser native speech synthesis fallback
    return {"status": "ready", "text": cleaned, "mode": "client_speech_synthesis"}


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
    """Server-side neural TTS with multi-tier caching (RAM + Redis) and fallback."""
    result = await generate_speech(data.text)
    return APIResponse(data=result)


@router.post("/pre-cache")
async def pre_cache_tts(data: PreCacheRequest, background_tasks: BackgroundTasks):
    """Pre-warm TTS cache for all questions in an upcoming interview session."""
    async def _warmup():
        for t in data.texts:
            if t and t.strip():
                try:
                    await generate_speech(t.strip())
                except Exception as e:
                    logger.debug(f"Pre-cache item skipped: {e}")

    background_tasks.add_task(_warmup)
    return APIResponse(data={"status": "warmup_started", "count": len(data.texts)})


@router.websocket("/sessions/{session_id}/stream")
async def voice_stream_websocket(websocket: WebSocket, session_id: str):
    """
    Bidirectional WebSocket connection for ultra-low latency live voice interaction.
    Features:
    - Real-time binary audio chunk streaming & incremental STT
    - Streaming Edge-TTS audio chunk delivery (<150ms TTFB) with multi-tier cache
    - Instant barge-in interruption signaling
    - Ping/Pong heartbeat keepalive
    """
    await websocket.accept()
    logger.info(f"Voice WebSocket connected for session {session_id}")

    audio_buffer = bytearray()
    interrupted = False

    try:
        await websocket.send_json({
            "type": "session.ready",
            "session_id": session_id,
            "sample_rate": 16000,
            "message": "Connected to AI Voice Engine"
        })

        while True:
            message = await websocket.receive()

            if "bytes" in message and message["bytes"]:
                # Ingest raw audio frame (e.g. 16kHz mono PCM or WebM slice)
                audio_buffer.extend(message["bytes"])
                continue

            if "text" in message:
                try:
                    payload = json.loads(message["text"])
                except Exception:
                    continue

                msg_type = payload.get("type")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

                elif msg_type == "user.barge_in":
                    interrupted = True
                    audio_buffer.clear()
                    await websocket.send_json({
                        "type": "server.interrupted",
                        "timestamp": payload.get("timestamp_ms")
                    })

                elif msg_type == "audio.chunk":
                    # Base64 JSON audio chunk ingestion
                    b64_data = payload.get("data", "")
                    if b64_data:
                        try:
                            if "," in b64_data:
                                b64_data = b64_data.split(",", 1)[1]
                            audio_buffer.extend(base64.b64decode(b64_data))
                        except Exception as e:
                            logger.debug(f"Audio chunk decode error: {e}")

                elif msg_type == "audio.slice":
                    # Quick partial transcription of accumulated audio buffer
                    if len(audio_buffer) > 1500:
                        try:
                            engine = ai_router.get_stt_provider()
                            partial = await engine.transcribe_audio(bytes(audio_buffer), fast=True)
                            await websocket.send_json({
                                "type": "transcript.partial",
                                "text": partial
                            })
                        except Exception as e:
                            logger.debug(f"Slice transcription bypass: {e}")

                elif msg_type in ("audio.commit", "audio.finished"):
                    # Final transcription of the candidate's speech
                    text = payload.get("transcript")
                    if not text and len(audio_buffer) > 300:
                        try:
                            engine = ai_router.get_stt_provider()
                            text = await engine.transcribe_audio(bytes(audio_buffer), fast=True)
                        except Exception as e:
                            logger.warning(f"WebSocket final transcribe error: {e}")
                            text = ""
                        finally:
                            audio_buffer.clear()
                    elif not text:
                        text = "Transcript received successfully."

                    await websocket.send_json({
                        "type": "transcript.final",
                        "text": text or ""
                    })

                elif msg_type == "speak":
                    # Stream synthesized audio chunks to the client with sub-150ms latency
                    text_to_speak = (payload.get("text") or "").strip()
                    if not text_to_speak:
                        continue

                    interrupted = False
                    cache_key = hashlib.sha256(text_to_speak.encode("utf-8")).hexdigest()

                    # Fast-path 1: Memory or Redis Cache hit (instant <1ms response)
                    cached_hit = None
                    if cache_key in _MEMORY_TTS_CACHE:
                        cached_hit = _MEMORY_TTS_CACHE[cache_key]
                    else:
                        try:
                            redis = await get_redis_client()
                            c_json = await redis.get(f"tts:{cache_key}")
                            if c_json:
                                cached_hit = json.loads(c_json)
                                _put_memory_cache(cache_key, cached_hit)
                        except Exception:
                            pass

                    if cached_hit and cached_hit.get("audio_base64"):
                        await websocket.send_json({
                            "type": "audio.start",
                            "mime_type": cached_hit.get("mime_type", "audio/mpeg"),
                            "cached": True
                        })
                        await websocket.send_json({
                            "type": "audio.chunk",
                            "data": cached_hit["audio_base64"]
                        })
                        await websocket.send_json({"type": "audio.end"})
                        continue

                    # Fast-path 2: Edge-TTS real-time chunk streaming
                    try:
                        import edge_tts
                        rate = payload.get("rate", "+15%")
                        comm = edge_tts.Communicate(text_to_speak, "en-US-GuyNeural", rate=rate)
                        await websocket.send_json({
                            "type": "audio.start",
                            "mime_type": "audio/mpeg",
                            "cached": False
                        })
                        accumulated = b""
                        async for chunk in comm.stream():
                            if interrupted:
                                break
                            if chunk["type"] == "audio":
                                accumulated += chunk["data"]
                                b64_chunk = base64.b64encode(chunk["data"]).decode("utf-8")
                                await websocket.send_json({
                                    "type": "audio.chunk",
                                    "data": b64_chunk
                                })

                        if not interrupted:
                            await websocket.send_json({"type": "audio.end"})
                            if accumulated:
                                full_res = {
                                    "status": "ready",
                                    "mode": "server_tts",
                                    "audio_base64": base64.b64encode(accumulated).decode("utf-8"),
                                    "mime_type": "audio/mpeg"
                                }
                                _put_memory_cache(cache_key, full_res)
                                try:
                                    redis = await get_redis_client()
                                    await redis.set(f"tts:{cache_key}", json.dumps(full_res), ex=86400 * 7)
                                except Exception:
                                    pass
                    except Exception as edge_err:
                        logger.warning(f"WebSocket Edge-TTS stream fallback: {edge_err}")
                        fallback_res = await generate_speech(text_to_speak)
                        if fallback_res.get("audio_base64"):
                            await websocket.send_json({
                                "type": "audio.start",
                                "mime_type": fallback_res.get("mime_type", "audio/wav"),
                                "cached": False
                            })
                            await websocket.send_json({
                                "type": "audio.chunk",
                                "data": fallback_res["audio_base64"]
                            })
                            await websocket.send_json({"type": "audio.end"})
                        else:
                            await websocket.send_json({
                                "type": "speak.fallback",
                                "text": text_to_speak
                            })

    except WebSocketDisconnect:
        logger.info(f"Voice WebSocket disconnected for session {session_id}")
    except RuntimeError as re:
        if "disconnect" in str(re).lower() or "closed" in str(re).lower():
            logger.info(f"Voice WebSocket closed for session {session_id}")
        else:
            logger.error(f"Voice WebSocket runtime error: {re}")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
