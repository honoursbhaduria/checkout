import React from "react";

interface StickyNoteProps {
  title: string;
  points: string[];
  priority?: "high" | "medium" | "low";
  className?: string;
  tilt?: "-rotate-1" | "rotate-1" | "-rotate-2" | "rotate-2";
}

export const StickyNote: React.FC<StickyNoteProps> = ({
  title,
  points,
  priority = "high",
  className = "",
  tilt = "-rotate-1",
}) => {
  return (
    <div
      className={`bg-postit border-2 border-pencil rounded-wobblySm p-5 shadow-sketch ${tilt} hover:rotate-0 transition-transform duration-100 ${className}`}
    >
      <div className="flex justify-between items-center mb-2 border-b-2 border-dashed border-pencil/30 pb-1">
        <h4 className="font-heading text-xl font-bold text-pencil">{title}</h4>
        <span className="font-body text-xs bg-marker text-white px-2 py-0.5 rounded-full border border-pencil uppercase font-bold tracking-wider">
          {priority}
        </span>
      </div>
      <ul className="list-disc list-inside font-body text-lg text-pencil/90 space-y-1">
        {points.map((pt, i) => (
          <li key={i} className="leading-snug">{pt}</li>
        ))}
      </ul>
    </div>
  );
};
