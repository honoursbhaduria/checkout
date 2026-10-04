import React, { useEffect, useRef } from "react";
import { LedIndicator } from "../ui/LedIndicator";

interface OscilloscopeWaveProps {
  isListening: boolean;
  isSpeaking: boolean;
  label?: string;
}

export const OscilloscopeWave: React.FC<OscilloscopeWaveProps> = ({
  isListening,
  isSpeaking,
  label = "AUDIO SPECTRUM",
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let phase = 0;

    const render = () => {
      ctx.fillStyle = "#1e272e";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Grid background lines
      ctx.strokeStyle = "rgba(46, 213, 115, 0.15)";
      ctx.lineWidth = 1;
      for (let x = 0; x < canvas.width; x += 20) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += 15) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      // Signal wave
      ctx.beginPath();
      ctx.lineWidth = 2;
      ctx.strokeStyle = isSpeaking ? "#ff4757" : isListening ? "#2ed573" : "#747d8c";
      ctx.shadowColor = isSpeaking ? "rgba(255, 71, 87, 0.8)" : isListening ? "rgba(46, 213, 115, 0.8)" : "transparent";
      ctx.shadowBlur = 8;

      const mid = canvas.height / 2;
      const amp = isSpeaking ? 16 : isListening ? 22 : 3;
      const freq = isSpeaking ? 0.08 : isListening ? 0.14 : 0.04;

      for (let x = 0; x < canvas.width; x += 2) {
        const y = mid + Math.sin(x * freq + phase) * amp * Math.cos((x / canvas.width) * Math.PI);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      phase += 0.12;
      animId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animId);
  }, [isListening, isSpeaking]);

  return (
    <div className="p-4 bg-chassis rounded-lg shadow-card border border-white/40">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-xs font-bold uppercase tracking-wider text-ink">
          {label}
        </span>
        <LedIndicator
          status={isSpeaking ? "red" : isListening ? "green" : "amber"}
          label={isSpeaking ? "TRANSMITTING" : isListening ? "RECEIVING" : "STANDBY"}
        />
      </div>
      <div className="relative rounded-md overflow-hidden shadow-recessed border border-[#1e272e]">
        <canvas ref={canvasRef} width={380} height={70} className="w-full h-[70px]" />
        <div className="absolute inset-0 crt-scanlines pointer-events-none" />
      </div>
    </div>
  );
};
