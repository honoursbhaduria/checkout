import React from "react";

interface WobblyCardProps {
  children: React.ReactNode;
  decoration?: "tape" | "tack" | "none";
  className?: string;
  tilt?: "-rotate-1" | "rotate-1" | "-rotate-2" | "rotate-2" | "none";
  borderStyle?: "solid" | "dashed";
}

const tiltClasses: Record<string, string> = {
  "-rotate-1": "rotate-0 md:-rotate-1",
  "rotate-1": "rotate-0 md:rotate-1",
  "-rotate-2": "rotate-0 md:-rotate-2",
  "rotate-2": "rotate-0 md:rotate-2",
  "none": "rotate-0",
};

export const WobblyCard: React.FC<WobblyCardProps> = ({
  children,
  decoration = "none",
  className = "",
  tilt = "none",
  borderStyle = "solid",
}) => {
  const rotationClass = tiltClasses[tilt] || "rotate-0";

  return (
    <div
      className={`relative bg-white border-[3px] border-pencil rounded-xl md:rounded-wobblyMd shadow-sketch p-4 sm:p-6 transition-transform duration-100 ${
        borderStyle === "dashed" ? "border-dashed" : "border-solid"
      } ${rotationClass} ${className}`}
    >
      {decoration === "tape" && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-28 h-6 tape-strip rotate-0 md:rotate-1 z-10" />
      )}
      {decoration === "tack" && (
        <div className="absolute -top-2 left-1/2 -translate-x-1/2 thumbtack-pin z-10" />
      )}
      {children}
    </div>
  );
};
