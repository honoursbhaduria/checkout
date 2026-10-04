import React from "react";

interface StickyNoteProps {
  title: string;
  points: string[];
  priority?: "high" | "medium" | "low";
  className?: string;
  tilt?: "-rotate-1" | "rotate-1" | "-rotate-2" | "rotate-2";
}

const tiltClasses: Record<string, string> = {
  "-rotate-1": "rotate-0 md:-rotate-1",
  "rotate-1": "rotate-0 md:rotate-1",
  "-rotate-2": "rotate-0 md:-rotate-2",
  "rotate-2": "rotate-0 md:rotate-2",
};

export const StickyNote: React.FC<StickyNoteProps> = ({
  title,
  points,
  priority = "high",
  className = "",
  tilt = "-rotate-1",
}) => {
  const rotationClass = tiltClasses[tilt] || "rotate-0";

  return (
    <div
      className={`bg-postit border-2 border-pencil rounded-lg md:rounded-wobblySm p-4 sm:p-5 shadow-sketch ${rotationClass} hover:rotate-0 transition-transform duration-100 ${className}`}
    >
      <div className="flex justify-between items-center mb-2 border-b-2 border-dashed border-pencil/30 pb-1 gap-2">
        <h4 className="font-heading text-lg sm:text-xl font-bold text-pencil">{title}</h4>
        <span className="font-body text-xs bg-marker text-white px-2 py-0.5 rounded-full border border-pencil uppercase font-bold tracking-wider shrink-0">
          {priority}
        </span>
      </div>
      <ul className="list-disc list-inside font-body text-base sm:text-lg text-pencil/90 space-y-1">
        {points.map((pt, i) => (
          <li key={i} className="leading-snug">{pt}</li>
        ))}
      </ul>
    </div>
  );
};
