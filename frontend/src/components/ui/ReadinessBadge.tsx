import React from "react";

interface ReadinessBadgeProps {
  classification: "STRONG_CANDIDATE" | "INTERVIEW_READY" | "NEEDS_PREPARATION" | "NOT_READY" | string;
  score?: number;
  className?: string;
}

export const ReadinessBadge: React.FC<ReadinessBadgeProps> = ({
  classification,
  score,
  className = "",
}) => {
  const configs: Record<string, { label: string; border: string; text: string; bg: string }> = {
    STRONG_CANDIDATE: {
      label: "STRONG CANDIDATE",
      border: "border-[#10b981]",
      text: "text-[#059669]",
      bg: "bg-[#d1fae5]",
    },
    INTERVIEW_READY: {
      label: "INTERVIEW READY",
      border: "border-pen",
      text: "text-pen",
      bg: "bg-[#dbeafe]",
    },
    NEEDS_PREPARATION: {
      label: "NEEDS PREPARATION",
      border: "border-[#f59e0b]",
      text: "text-[#d97706]",
      bg: "bg-[#fef3c7]",
    },
    NOT_READY: {
      label: "NOT READY",
      border: "border-marker",
      text: "text-marker",
      bg: "bg-[#fee2e2]",
    },
  };

  const current = configs[classification] || configs["NEEDS_PREPARATION"];

  return (
    <div
      className={`inline-flex flex-col items-center justify-center border-4 border-dashed rounded-full px-8 py-3 rotate-2 shadow-sketch ${current.border} ${current.bg} ${className}`}
    >
      <span className={`font-heading text-3xl font-bold tracking-wider uppercase ${current.text}`}>
        {current.label}
      </span>
      {score !== undefined && (
        <span className="font-body text-xl font-bold text-pencil mt-0.5">
          Readiness Score: {score} / 100
        </span>
      )}
    </div>
  );
};
