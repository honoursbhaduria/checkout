import React from "react";

interface SpeechBubbleProps {
  children: React.ReactNode;
  speaker?: string;
  isAI?: boolean;
  className?: string;
}

export const SpeechBubble: React.FC<SpeechBubbleProps> = ({
  children,
  speaker = "AI Interviewer",
  isAI = true,
  className = "",
}) => {
  return (
    <div className={`relative ${className}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="font-heading text-lg font-bold text-pencil">
          {speaker}
        </span>
        {isAI && (
          <span className="text-xs bg-pen text-white px-2 py-0.5 rounded-full border border-pencil font-body uppercase">
            AI Engine
          </span>
        )}
      </div>
      <div
        className={`relative border-[3px] border-pencil rounded-wobblyMd p-5 shadow-sketch ${
          isAI ? "bg-white" : "bg-[#f5f0e6]"
        }`}
      >
        <div className="font-body text-xl text-pencil leading-relaxed">
          {children}
        </div>
      </div>
    </div>
  );
};
