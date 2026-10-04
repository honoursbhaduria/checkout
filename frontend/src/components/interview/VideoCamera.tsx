import React, { useEffect, useRef, useState } from "react";
import { Camera, CameraOff, Sparkles, Video } from "lucide-react";
import { WobblyButton } from "../ui/WobblyButton";

interface VideoCameraProps {
  onStreamActive?: (active: boolean) => void;
}

export const VideoCamera: React.FC<VideoCameraProps> = ({ onStreamActive }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const simAnimRef = useRef<number | null>(null);

  const [isActive, setIsActive] = useState<boolean>(false);
  const [feedMode, setFeedMode] = useState<"live" | "simulated" | "off">("off");
  const [error, setError] = useState<string | null>(null);

  // Stop any ongoing video stream and canvas animation
  const stopCamera = () => {
    if (simAnimRef.current) {
      cancelAnimationFrame(simAnimRef.current);
      simAnimRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsActive(false);
    setFeedMode("off");
    onStreamActive?.(false);
  };

  // Start real webcam stream
  const startRealWebcam = async () => {
    stopCamera();
    setError(null);

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Camera API not supported in this browser. Try 'Simulate Video'.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
        audio: false,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
      }

      setIsActive(true);
      setFeedMode("live");
      onStreamActive?.(true);
    } catch (err: any) {
      console.warn("Real webcam error:", err);
      const isDenied = err.name === "NotAllowedError" || err.name === "PermissionDeniedError";
      const isNotFound = err.name === "NotFoundError" || err.name === "DevicesNotFoundError";

      if (isDenied) {
        setError("Camera permission denied. Click 'Simulate Video' to preview without hardware access.");
      } else if (isNotFound) {
        setError("No physical webcam detected. Click 'Simulate Video' for animated simulation.");
      } else {
        setError("Webcam error. Falling back to simulated video feed.");
      }
      // Start simulated video automatically so the candidate sees an active feed
      startSimulatedFeed();
    }
  };

  // Start simulated test video feed on canvas
  const startSimulatedFeed = () => {
    stopCamera();
    setError(null);

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let frame = 0;

    const render = () => {
      frame++;
      const w = canvas.width;
      const h = canvas.height;

      // Background paper sketch gradient
      ctx.fillStyle = "#faf8f5";
      ctx.fillRect(0, 0, w, h);

      // Grid guidelines
      ctx.strokeStyle = "#e8e4dc";
      ctx.lineWidth = 1;
      for (let x = 0; x < w; x += 20) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += 20) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Candidate silhouette with subtle breathing movement
      const breathe = Math.sin(frame * 0.05) * 4;
      const eyeBlink = frame % 90 < 5;

      // Head
      ctx.fillStyle = "#2d2d2d";
      ctx.strokeStyle = "#2d2d2d";
      ctx.lineWidth = 3;

      // Shoulders
      ctx.beginPath();
      ctx.ellipse(w / 2, h + 30 + breathe, 90, 70, 0, 0, Math.PI * 2);
      ctx.fill();

      // Neck
      ctx.fillRect(w / 2 - 16, h / 2 + 10 + breathe, 32, 40);

      // Head outline
      ctx.fillStyle = "#f5ebd7";
      ctx.beginPath();
      ctx.ellipse(w / 2, h / 2 - 20 + breathe, 45, 55, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      // Hair
      ctx.fillStyle = "#2d2d2d";
      ctx.beginPath();
      ctx.arc(w / 2, h / 2 - 40 + breathe, 46, Math.PI, 0);
      ctx.fill();

      // Eyes
      ctx.fillStyle = "#2d2d2d";
      if (eyeBlink) {
        ctx.fillRect(w / 2 - 22, h / 2 - 22 + breathe, 14, 2);
        ctx.fillRect(w / 2 + 8, h / 2 - 22 + breathe, 14, 2);
      } else {
        ctx.beginPath();
        ctx.arc(w / 2 - 15, h / 2 - 22 + breathe, 4, 0, Math.PI * 2);
        ctx.arc(w / 2 + 15, h / 2 - 22 + breathe, 4, 0, Math.PI * 2);
        ctx.fill();
      }

      // Smile
      ctx.beginPath();
      ctx.arc(w / 2, h / 2 - 5 + breathe, 16, 0.2, Math.PI - 0.2);
      ctx.stroke();

      // Watermark / Name
      ctx.fillStyle = "#2d2d2d";
      ctx.font = "bold 13px 'Patrick Hand', sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Honours Bhadauria (Live Simulation)", w / 2, h - 14);

      simAnimRef.current = requestAnimationFrame(render);
    };

    render();

    try {
      const simStream = canvas.captureStream(30);
      streamRef.current = simStream;

      if (videoRef.current) {
        videoRef.current.srcObject = simStream;
        videoRef.current.play().catch(() => {});
      }

      setIsActive(true);
      setFeedMode("simulated");
      onStreamActive?.(true);
    } catch (e) {
      console.warn("Canvas stream capture failed:", e);
      setIsActive(true);
      setFeedMode("simulated");
    }
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-full max-w-[280px] h-[190px] bg-[#f0ede6] border-2 border-pencil rounded-xl md:rounded-wobblyMd overflow-hidden shadow-sketchSm flex items-center justify-center">
        {/* Hidden canvas for video generation */}
        <canvas ref={canvasRef} width={280} height={190} className="hidden" />

        {/* Video element ALWAYS mounted to avoid null ref lifecycle race */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`w-full h-full object-cover transform -scale-x-100 ${
            isActive ? "block" : "hidden"
          }`}
        />

        {/* Standby placeholder when inactive */}
        {!isActive && (
          <div className="flex flex-col items-center justify-center p-4 text-center">
            <Video className="w-10 h-10 text-pencil/40 mb-2" />
            <p className="font-heading text-lg font-bold text-pencil">
              Video Camera Feed
            </p>
            <p className="font-body text-xs text-pencil/60 mt-0.5">
              Click 'Enable Webcam' or 'Simulate Video' below
            </p>
            {error && (
              <p className="font-body text-xs text-marker mt-1.5 px-2 bg-red-50 rounded border border-marker/20">
                {error}
              </p>
            )}
          </div>
        )}

        {/* Live indicator badge */}
        {isActive && (
          <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-marker text-white px-2 py-0.5 rounded-full text-xs font-heading font-bold border border-pencil shadow-sm">
            <span className="w-2 h-2 rounded-full bg-white animate-ping" />
            {feedMode === "live" ? "LIVE REC" : "SIM REC"}
          </div>
        )}

        {/* Feed mode pill */}
        {isActive && (
          <div className="absolute bottom-2 left-2 bg-white/90 backdrop-blur-sm border border-pencil px-2 py-0.5 rounded text-[11px] font-heading text-pencil">
            {feedMode === "live" ? "📹 HD Webcam" : "✨ AI Simulated Feed"}
          </div>
        )}
      </div>

      {/* Control Buttons */}
      <div className="flex flex-wrap items-center justify-center gap-2 mt-2.5">
        {isActive ? (
          <WobblyButton size="sm" variant="danger" onClick={stopCamera}>
            <span className="flex items-center gap-1">
              <CameraOff className="w-4 h-4" /> Turn Off Video
            </span>
          </WobblyButton>
        ) : (
          <>
            <WobblyButton size="sm" variant="primary" onClick={startRealWebcam}>
              <span className="flex items-center gap-1">
                <Camera className="w-4 h-4" /> Enable Webcam
              </span>
            </WobblyButton>

            <WobblyButton size="sm" variant="secondary" onClick={startSimulatedFeed} title="Preview simulated camera feed">
              <span className="flex items-center gap-1">
                <Sparkles className="w-4 h-4 text-marker" /> Simulate Video
              </span>
            </WobblyButton>
          </>
        )}
      </div>
    </div>
  );
};
