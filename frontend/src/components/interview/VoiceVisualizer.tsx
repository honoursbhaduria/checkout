import React, { useEffect, useRef } from "react";
import { Mic, Volume2 } from "lucide-react";

interface VoiceVisualizerProps {
  isListening: boolean;
  isSpeaking: boolean;
  statusText?: string;
  audioStream?: MediaStream | null;
}

export const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({
  isListening,
  isSpeaking,
  statusText,
  audioStream,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<any>(null);

  // Setup Web Audio Analyser when real audioStream is provided
  useEffect(() => {
    if (!audioStream) {
      if (audioContextRef.current && audioContextRef.current.state !== "closed") {
        audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
      analyserRef.current = null;
      dataArrayRef.current = null;
      return;
    }

    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      const source = ctx.createMediaStreamSource(audioStream);
      source.connect(analyser);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      audioContextRef.current = ctx;
      analyserRef.current = analyser;
      dataArrayRef.current = dataArray;
    } catch (e) {
      console.warn("Audio analyser setup error:", e);
    }

    return () => {
      if (audioContextRef.current && audioContextRef.current.state !== "closed") {
        audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
    };
  }, [audioStream]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const width = canvas.width;
      const height = canvas.height;
      const mid = height / 2;

      let realVol = 0;
      if (analyserRef.current && dataArrayRef.current) {
        analyserRef.current.getByteFrequencyData(dataArrayRef.current);
        let sum = 0;
        for (let i = 0; i < dataArrayRef.current.length; i++) {
          sum += dataArrayRef.current[i];
        }
        realVol = sum / dataArrayRef.current.length;
      }

      ctx.beginPath();
      ctx.lineWidth = 3;
      ctx.strokeStyle = isSpeaking ? "#ff4d4d" : isListening ? "#2d5da1" : "#2d2d2d";
      ctx.lineCap = "round";

      // Scale amplitude by real volume if microphone is streaming
      const amplitude = isSpeaking
        ? 18
        : isListening
        ? realVol > 5
          ? Math.min(32, 8 + (realVol / 255) * 45)
          : 12
        : 3;

      const frequency = isSpeaking ? 0.08 : isListening ? 0.12 : 0.03;

      for (let x = 0; x < width; x += 3) {
        const y = mid + Math.sin(x * frequency + phase) * amplitude * Math.sin((x / width) * Math.PI);
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      phase += 0.12;
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [isListening, isSpeaking]);

  return (
    <div className="flex flex-col items-center justify-center p-2.5 sm:p-3 bg-white border-2 border-pencil rounded-lg md:rounded-wobbly shadow-sketchSm">
      <div className="flex items-center gap-2 mb-1">
        {isSpeaking ? (
          <Volume2 className="w-5 h-5 text-marker animate-pulse shrink-0" />
        ) : (
          <Mic className={`w-5 h-5 shrink-0 ${isListening ? "text-pen animate-bounce" : "text-pencil/50"}`} />
        )}
        <span className="font-heading text-base sm:text-lg font-bold text-center">
          {statusText ||
            (isSpeaking
              ? "AI Interviewer Speaking..."
              : isListening
              ? "Microphone Live • Listening..."
              : "Microphone Ready")}
        </span>
      </div>
      <canvas
        ref={canvasRef}
        width={320}
        height={50}
        className="w-full max-w-[320px] h-[50px]"
      />
    </div>
  );
};
