import React from "react";

interface IndustrialCardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  hasScrews?: boolean;
  hasVents?: boolean;
  elevated?: boolean;
  className?: string;
}

export const IndustrialCard: React.FC<IndustrialCardProps> = ({
  children,
  title,
  subtitle,
  hasScrews = true,
  hasVents = true,
  elevated = false,
  className = "",
}) => {
  return (
    <div
      className={`relative bg-chassis rounded-lg p-4 sm:p-6 ${
        elevated ? "shadow-floating" : "shadow-card"
      } border border-white/40 transition-all duration-300 ${className}`}
    >
      {/* Corner Screws */}
      {hasScrews && (
        <>
          <div className="screw-tl" />
          <div className="screw-tr" />
          <div className="screw-bl" />
          <div className="screw-br" />
        </>
      )}

      {/* Header bar with title and vent slots */}
      {(title || hasVents) && (
        <div className="flex items-center justify-between mb-4 border-b border-[#a3b1c6]/30 pb-3">
          <div>
            {title && (
              <h3 className="font-mono text-xs md:text-sm font-bold uppercase tracking-wider text-ink">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="font-mono text-[11px] text-inkMuted uppercase tracking-tight">
                {subtitle}
              </p>
            )}
          </div>

          {hasVents && (
            <div className="flex items-center gap-1.5 ml-auto">
              <div className="vent-slot" />
              <div className="vent-slot" />
              <div className="vent-slot" />
            </div>
          )}
        </div>
      )}

      {children}
    </div>
  );
};
