import React, { useEffect, useRef, useState } from "react";
import { Camera, CameraOff, Video } from "lucide-react";
import { IndustrialButton } from "../ui/IndustrialButton";
import { LedIndicator } from "../ui/LedIndicator";

export const IndustrialMonitor: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isActive, setIsActive] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const startCamera = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsActive(true);
      }
    } catch (err: any) {
      console.warn("Camera not available:", err);
      setError("CAMERA OFFLINE");
      setIsActive(false);
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((t) => t.stop());
      videoRef.current.srcObject = null;
    }
    setIsActive(false);
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  return (
    <div className="p-4 bg-chassis rounded-lg shadow-card border border-white/40">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-xs font-bold uppercase tracking-wider text-ink">
          OPTICAL SENSOR FEED
        </span>
        <LedIndicator
          status={isActive ? "green" : "amber"}
          label={isActive ? "LIVE_FEED" : "OFFLINE"}
        />
      </div>

      <div className="relative w-full h-[180px] bg-[#1e272e] rounded-md overflow-hidden shadow-recessed border border-[#1e272e] flex items-center justify-center">
        {isActive ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover transform -scale-x-100"
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-center p-3">
            <Video className="w-8 h-8 text-[#747d8c] mb-1.5" />
            <span className="font-mono text-xs text-[#a4b0be]">VIDEO SENSOR STANDBY</span>
            {error && <span className="font-mono text-[10px] text-safety mt-1">{error}</span>}
          </div>
        )}
        <div className="absolute inset-0 crt-scanlines pointer-events-none" />
      </div>

      <div className="mt-3 flex justify-end">
        <IndustrialButton
          size="sm"
          variant={isActive ? "dark" : "secondary"}
          onClick={isActive ? stopCamera : startCamera}
        >
          {isActive ? (
            <>
              <CameraOff className="w-3.5 h-3.5" /> DEACTIVATE FEED
            </>
          ) : (
            <>
              <Camera className="w-3.5 h-3.5" /> ACTIVATE SENSOR
            </>
          )}
        </IndustrialButton>
      </div>
    </div>
  );
};
