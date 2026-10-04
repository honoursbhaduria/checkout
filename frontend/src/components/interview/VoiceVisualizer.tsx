import React, { useEffect, useRef } from "react";
import { Mic, Volume2 } from "lucide-react";

interface VoiceVisualizerProps {
  isListening: boolean;
  isSpeaking: boolean;
  statusText?: string;
}

export const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({
  isListening,
  isSpeaking,
  statusText,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

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

      ctx.beginPath();
      ctx.lineWidth = 3;
      ctx.strokeStyle = isSpeaking ? "#ff4d4d" : isListening ? "#2d5da1" : "#2d2d2d";
      ctx.lineCap = "round";

      const amplitude = isSpeaking ? 18 : isListening ? 24 : 4;
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
    <div className="flex flex-col items-center justify-center p-3 bg-white border-2 border-pencil rounded-wobbly shadow-sketchSm">
      <div className="flex items-center gap-2 mb-1">
        {isSpeaking ? (
          <Volume2 className="w-5 h-5 text-marker animate-pulse" />
        ) : (
          <Mic className={`w-5 h-5 ${isListening ? "text-pen animate-bounce" : "text-pencil/50"}`} />
        )}
        <span className="font-heading text-lg font-bold">
          {statusText || (isSpeaking ? "AI Interviewer Speaking..." : isListening ? "Listening to Your Answer..." : "Microphone Ready")}
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
