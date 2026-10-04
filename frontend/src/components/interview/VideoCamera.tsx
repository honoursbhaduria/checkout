import React, { useEffect, useRef, useState } from "react";
import { Camera, CameraOff, Video } from "lucide-react";
import { WobblyButton } from "../ui/WobblyButton";

interface VideoCameraProps {
  onStreamActive?: (active: boolean) => void;
}

export const VideoCamera: React.FC<VideoCameraProps> = ({ onStreamActive }) => {
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
        onStreamActive?.(true);
      }
    } catch (err: any) {
      console.warn("Camera access denied or unavailable:", err);
      setError("Webcam optional or not accessible.");
      setIsActive(false);
      onStreamActive?.(false);
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    setIsActive(false);
    onStreamActive?.(false);
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-full max-w-[280px] h-[190px] bg-[#f0ede6] border-2 border-pencil rounded-wobblyMd overflow-hidden shadow-sketchSm flex items-center justify-center">
        {isActive ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover transform -scale-x-100"
          />
        ) : (
          <div className="flex flex-col items-center justify-center p-4 text-center">
            <Video className="w-10 h-10 text-pencil/40 mb-2" />
            <p className="font-body text-base text-pencil/60">
              Video Camera Feed (Bonus Experience)
            </p>
            {error && <p className="font-body text-xs text-marker mt-1">{error}</p>}
          </div>
        )}

        {/* Live indicator badge */}
        {isActive && (
          <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-marker text-white px-2 py-0.5 rounded-full text-xs font-heading font-bold border border-pencil shadow-sm">
            <span className="w-2 h-2 rounded-full bg-white animate-ping" />
            REC
          </div>
        )}
      </div>

      <div className="mt-2">
        <WobblyButton
          size="sm"
          variant={isActive ? "secondary" : "primary"}
          onClick={isActive ? stopCamera : startCamera}
        >
          {isActive ? (
            <span className="flex items-center gap-1">
              <CameraOff className="w-4 h-4" /> Turn Off Video
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <Camera className="w-4 h-4" /> Enable Webcam
            </span>
          )}
        </WobblyButton>
      </div>
    </div>
  );
};
