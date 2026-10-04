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
async def transcribe_audio_file(file: UploadFile = File(...)):
    engine = ai_router.get_stt_provider()
    audio_bytes = await file.read()
    transcript = await engine.transcribe_audio(audio_bytes)
    return APIResponse(data={"transcript": transcript})


@router.post("/synthesize")
async def synthesize_text_rest(data: SynthesizeRequest):
    return APIResponse(data={"status": "ready", "text": data.text, "mode": "client_speech_synthesis"})


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
