import React from "react";

interface IndustrialInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  badge?: string;
}

export const IndustrialInput: React.FC<IndustrialInputProps> = ({
  label,
  badge,
  className = "",
  ...props
}) => {
  return (
    <div className="w-full">
      {label && (
        <div className="flex items-center justify-between mb-1.5">
          <label className="font-mono text-xs font-bold uppercase tracking-wider text-ink">
            {label}
          </label>
          {badge && (
            <span className="font-mono text-[10px] text-inkMuted uppercase tracking-tight">
              {badge}
            </span>
          )}
        </div>
      )}
      <input
        className={`w-full font-mono text-sm px-4 py-2.5 bg-chassis text-ink rounded-md shadow-recessed
          border-none outline-none focus:ring-2 focus:ring-safety/40 transition-all placeholder:text-inkMuted/50 ${className}`}
        {...props}
      />
    </div>
  );
};

interface IndustrialTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  badge?: string;
}

export const IndustrialTextarea: React.FC<IndustrialTextareaProps> = ({
  label,
  badge,
  className = "",
  ...props
}) => {
  return (
    <div className="w-full">
      {label && (
        <div className="flex items-center justify-between mb-1.5">
          <label className="font-mono text-xs font-bold uppercase tracking-wider text-ink">
            {label}
          </label>
          {badge && (
            <span className="font-mono text-[10px] text-inkMuted uppercase tracking-tight">
              {badge}
            </span>
          )}
        </div>
      )}
      <textarea
        className={`w-full font-mono text-sm px-4 py-3 bg-chassis text-ink rounded-md shadow-recessed
          border-none outline-none focus:ring-2 focus:ring-safety/40 transition-all placeholder:text-inkMuted/50 resize-y leading-relaxed no-scrollbar ${className}`}
        {...props}
      />
    </div>
  );
};
