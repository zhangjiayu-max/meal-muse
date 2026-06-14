"use client";

import { useState } from "react";
import { AlertTriangle, Info, XCircle, CheckCircle, X } from "lucide-react";

type ErrorType = "error" | "warning" | "info" | "success";

interface ErrorMessageProps {
  type?: ErrorType;
  title?: string;
  message: string;
  dismissable?: boolean;
  className?: string;
  /** 操作按钮 */
  action?: React.ReactNode;
}

const config: Record<
  ErrorType,
  { icon: React.ElementType; bg: string; border: string; text: string; iconColor: string }
> = {
  error: {
    icon: XCircle,
    bg: "bg-red-50",
    border: "border-red-100",
    text: "text-red-800",
    iconColor: "text-red-500",
  },
  warning: {
    icon: AlertTriangle,
    bg: "bg-amber-50",
    border: "border-amber-100",
    text: "text-amber-800",
    iconColor: "text-amber-500",
  },
  info: {
    icon: Info,
    bg: "bg-blue-50",
    border: "border-blue-100",
    text: "text-blue-800",
    iconColor: "text-blue-500",
  },
  success: {
    icon: CheckCircle,
    bg: "bg-green-50",
    border: "border-green-100",
    text: "text-green-800",
    iconColor: "text-green-500",
  },
};

/** 行内错误/提示信息 */
export function ErrorMessage({
  type = "error",
  title,
  message,
  dismissable = false,
  className = "",
  action,
}: ErrorMessageProps) {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed) return null;

  const cfg = config[type];
  const Icon = cfg.icon;

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-xl border ${cfg.bg} ${cfg.border} ${className}`}
    >
      <Icon className={`w-5 h-5 mt-0.5 shrink-0 ${cfg.iconColor}`} />
      <div className="flex-1 min-w-0">
        {title && (
          <p className={`text-sm font-medium ${cfg.text}`}>{title}</p>
        )}
        <p className={`text-sm ${cfg.text} ${title ? "mt-0.5" : ""} opacity-90`}>
          {message}
        </p>
        {action && <div className="mt-2">{action}</div>}
      </div>
      {dismissable && (
        <button
          onClick={() => setDismissed(true)}
          className={`p-0.5 ${cfg.text} opacity-60 hover:opacity-100 transition-opacity`}
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

/** 内联表单错误（小字号，无图标） */
export function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="mt-1 text-xs text-red-500">{message}</p>;
}

/** 空状态占位 */
export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      {icon && <div className="mb-4 text-4xl">{icon}</div>}
      <h3 className="text-base font-semibold text-gray-900 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-gray-500 mb-4 text-center max-w-xs">
          {description}
        </p>
      )}
      {action && <div>{action}</div>}
    </div>
  );
}
