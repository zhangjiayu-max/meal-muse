"use client";

import { useState, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, XCircle, AlertTriangle, Info, X } from "lucide-react";

interface ToastItem {
  id: number;
  type: "success" | "error" | "info" | "warning";
  message: string;
}

const CONFIG = {
  success: { icon: CheckCircle, bg: "bg-green-50", border: "border-green-200", text: "text-green-800", iconColor: "text-green-500" },
  error: { icon: XCircle, bg: "bg-red-50", border: "border-red-200", text: "text-red-800", iconColor: "text-red-500" },
  info: { icon: Info, bg: "bg-blue-50", border: "border-blue-200", text: "text-blue-800", iconColor: "text-blue-500" },
  warning: { icon: AlertTriangle, bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-800", iconColor: "text-amber-500" },
} as const;

let toastId = 0;
let addToastFn:
  | ((type: ToastItem["type"], message: string, duration?: number) => void)
  | null = null;

/**
 * 全局 Toast 调用
 * @example toast("success", "记录成功！")
 * @example toast("error", "网络错误，请重试")
 */
export function toast(type: ToastItem["type"], message: string, duration = 3000) {
  addToastFn?.(type, message, duration);
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (type: ToastItem["type"], message: string, duration = 3000) => {
      const id = ++toastId;
      setToasts((prev) => [...prev, { id, type, message }]);
      setTimeout(() => removeToast(id), duration);
    },
    [removeToast],
  );

  useEffect(() => {
    addToastFn = addToast;
    return () => {
      addToastFn = null;
    };
  }, [addToast]);

  if (typeof window === "undefined") return null;

  return createPortal(
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      <AnimatePresence initial={false}>
        {toasts.map((t) => {
          const cfg = CONFIG[t.type];
          const Icon = cfg.icon;
          return (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, x: 80, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 80, scale: 0.95 }}
              transition={{ type: "spring", damping: 20, stiffness: 300 }}
              className={`pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl border shadow-lg ${cfg.bg} ${cfg.border} ${cfg.text}`}
            >
              <Icon className={`w-5 h-5 mt-0.5 shrink-0 ${cfg.iconColor}`} />
              <p className="text-sm flex-1">{t.message}</p>
              <button
                onClick={() => removeToast(t.id)}
                className="p-0.5 opacity-50 hover:opacity-100 transition-opacity"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>,
    document.body,
  );
}
