import React from "react";

interface WobblyButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "marker" | "pen";
  size?: "sm" | "md" | "lg";
}

export const WobblyButton: React.FC<WobblyButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  className = "",
  ...props
}) => {
  const sizeStyles = {
    sm: "px-2.5 sm:px-3 py-1 sm:py-1.5 text-sm sm:text-base min-h-[38px] inline-flex items-center justify-center",
    md: "px-3.5 sm:px-5 py-1.5 sm:py-2 text-base sm:text-xl min-h-[42px] inline-flex items-center justify-center",
    lg: "px-5 sm:px-8 py-2.5 sm:py-3 text-lg sm:text-2xl font-bold min-h-[48px] inline-flex items-center justify-center",
  };

  const variantStyles = {
    primary: "bg-white text-pencil hover:bg-marker hover:text-white",
    secondary: "bg-erased text-pencil hover:bg-pen hover:text-white",
    danger: "bg-marker text-white hover:bg-pencil",
    marker: "bg-marker text-white hover:bg-pencil",
    pen: "bg-pen text-white hover:bg-pencil",
  };

  return (
    <button
      className={`font-body border-[3px] border-pencil rounded-wobbly shadow-sketch
        transition-all duration-100 ease-in-out cursor-pointer
        hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_#2d2d2d]
        active:translate-x-[4px] active:translate-y-[4px] active:shadow-sketchActive
        disabled:opacity-50 disabled:cursor-not-allowed select-none
        ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};
