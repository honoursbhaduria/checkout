import React from "react";

interface LedIndicatorProps {
  status: "green" | "red" | "amber";
  label?: string;
  pulse?: boolean;
}

export const LedIndicator: React.FC<LedIndicatorProps> = ({
  status,
  label,
  pulse = true,
}) => {
  const configs = {
    green: {
      bg: "bg-[#10b981]",
      shadow: "shadow-ledGreen",
      text: "text-[#059669]",
    },
    red: {
      bg: "bg-safety",
      shadow: "shadow-ledRed",
      text: "text-safety",
    },
    amber: {
      bg: "bg-[#f59e0b]",
      shadow: "shadow-ledAmber",
      text: "text-[#d97706]",
    },
  };

  const current = configs[status];

  return (
    <div className="inline-flex items-center gap-2">
      <span
        className={`w-2.5 h-2.5 rounded-full border border-white/40 ${current.bg} ${current.shadow} ${
          pulse ? "animate-pulse" : ""
        }`}
      />
      {label && (
        <span className="font-mono text-[11px] font-bold tracking-wider uppercase text-ink">
          {label}
        </span>
      )}
    </div>
  );
};
