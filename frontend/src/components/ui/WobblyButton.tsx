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
    sm: "px-3 py-1 text-base",
    md: "px-5 py-2 text-xl",
    lg: "px-8 py-3 text-2xl font-bold",
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
