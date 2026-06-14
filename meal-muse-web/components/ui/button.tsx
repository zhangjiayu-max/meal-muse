"use client";

import { forwardRef, type ButtonHTMLAttributes } from "react";
import { Loader2 } from "lucide-react";

type ButtonVariant =
  | "primary"
  | "secondary"
  | "ghost"
  | "danger"
  | "outline"
  | "success";

type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-green-500 text-white hover:bg-green-600 active:bg-green-700 focus:ring-green-500",
  secondary:
    "bg-gray-100 text-gray-700 hover:bg-gray-200 active:bg-gray-300 focus:ring-gray-400",
  ghost:
    "bg-transparent text-gray-600 hover:bg-gray-100 active:bg-gray-200 focus:ring-gray-400",
  danger:
    "bg-red-500 text-white hover:bg-red-600 active:bg-red-700 focus:ring-red-500",
  outline:
    "bg-transparent text-gray-700 border border-gray-200 hover:bg-gray-50 active:bg-gray-100 focus:ring-gray-400",
  success:
    "bg-green-50 text-green-700 hover:bg-green-100 active:bg-green-200 focus:ring-green-500",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs gap-1.5",
  md: "px-4 py-2 text-sm gap-2",
  lg: "px-5 py-2.5 text-base gap-2",
};

const iconSizeClasses: Record<ButtonSize, string> = {
  sm: "w-3.5 h-3.5",
  md: "w-4 h-4",
  lg: "w-5 h-5",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      icon,
      disabled,
      children,
      className = "",
      ...props
    },
    ref,
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={`
          inline-flex items-center justify-center font-medium rounded-xl
          transition-all duration-150
          focus:outline-none focus:ring-2 focus:ring-offset-1
          disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
          ${variantClasses[variant]}
          ${sizeClasses[size]}
          ${className}
        `.trim()}
        {...props}
      >
        {loading ? (
          <Loader2 className={`${iconSizeClasses[size]} animate-spin`} />
        ) : icon ? (
          <span className={iconSizeClasses[size]}>{icon}</span>
        ) : null}
        {children && <span>{children}</span>}
      </button>
    );
  },
);

Button.displayName = "Button";
