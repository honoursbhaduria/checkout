import React from "react";

interface IndustrialButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "dark" | "outline";
  size?: "sm" | "md" | "lg";
}

export const IndustrialButton: React.FC<IndustrialButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  className = "",
  ...props
}) => {
  const sizeStyles = {
    sm: "px-3 py-1.5 text-xs font-mono tracking-wider",
    md: "px-5 py-2.5 text-sm font-mono tracking-wider",
    lg: "px-7 py-3.5 text-base font-mono tracking-wider",
  };

  const variantStyles = {
    primary:
      "bg-safety text-white font-bold uppercase shadow-safety active:shadow-safetyPressed active:translate-y-[2px] border border-white/20",
    secondary:
      "bg-chassis text-ink font-bold uppercase shadow-floating active:shadow-pressed active:translate-y-[2px] hover:text-safety border border-white/60",
    dark:
      "bg-[#2d3436] text-[#f0f2f5] font-bold uppercase shadow-sharp active:translate-y-[2px] border border-white/10 hover:border-safety",
    outline:
      "bg-transparent text-inkMuted font-mono uppercase hover:text-safety hover:bg-recessed/50 active:translate-y-[2px]",
  };

  return (
    <button
      className={`rounded-md mechanical-transition cursor-pointer select-none inline-flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};
