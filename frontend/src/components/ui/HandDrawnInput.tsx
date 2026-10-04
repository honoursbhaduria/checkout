import React from "react";

interface HandDrawnInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const HandDrawnInput: React.FC<HandDrawnInputProps> = ({
  label,
  error,
  className = "",
  ...props
}) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block font-heading text-xl text-pencil mb-1">
          {label}
        </label>
      )}
      <input
        className={`w-full font-body text-xl px-4 py-2 bg-white text-pencil border-2 border-pencil rounded-wobbly shadow-sketchSm
          outline-none focus:border-pen focus:ring-2 focus:ring-pen/20 transition-all placeholder:text-pencil/40 ${className}`}
        {...props}
      />
      {error && (
        <p className="font-body text-base text-marker mt-1">{error}</p>
      )}
    </div>
  );
};

interface HandDrawnTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const HandDrawnTextarea: React.FC<HandDrawnTextareaProps> = ({
  label,
  error,
  className = "",
  ...props
}) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block font-heading text-xl text-pencil mb-1">
          {label}
        </label>
      )}
      <textarea
        className={`w-full font-body text-xl px-4 py-3 bg-white text-pencil border-2 border-pencil rounded-wobblyMd shadow-sketchSm
          outline-none focus:border-pen focus:ring-2 focus:ring-pen/20 transition-all placeholder:text-pencil/40 resize-y no-scrollbar ${className}`}
        {...props}
      />
      {error && (
        <p className="font-body text-base text-marker mt-1">{error}</p>
      )}
    </div>
  );
};
