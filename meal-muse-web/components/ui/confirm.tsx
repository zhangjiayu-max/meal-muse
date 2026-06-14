"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Info, HelpCircle } from "lucide-react";

interface ConfirmConfig {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: "danger" | "warning" | "info";
}

let confirmFn: ((config: ConfirmConfig) => Promise<boolean>) | null = null;

/**
 * 全局确认对话框函数 —— 替代 window.confirm
 *
 * @example
 * ```tsx
 * import { confirm } from "@/components/ui/confirm";
 *
 * const ok = await confirm({ title: "确定删除？", message: "此操作不可恢复", type: "danger" });
 * if (ok) { ... }
 * ```
 */
export function confirm(config: ConfirmConfig): Promise<boolean> {
  if (!confirmFn) {
    // Fallback: 如果组件还没挂载，用原生 confirm
    return Promise.resolve(window.confirm(`${config.title}\n${config.message}`));
  }
  return confirmFn(config);
}

const iconMap = {
  danger: { icon: AlertTriangle, bg: "bg-red-100", color: "text-red-500" },
  warning: { icon: AlertTriangle, bg: "bg-amber-100", color: "text-amber-500" },
  info: { icon: Info, bg: "bg-blue-100", color: "text-blue-500" },
};

export function ConfirmContainer() {
  const [state, setState] = useState<ConfirmConfig & { open: boolean }>({
    open: false,
    title: "",
    message: "",
  });
  const resolverRef = useRef<((value: boolean) => void) | null>(null);

  const show = useCallback(async (config: ConfirmConfig) => {
    return new Promise<boolean>((resolve) => {
      resolverRef.current = resolve;
      setState({ ...config, open: true });
    });
  }, []);

  useEffect(() => {
    confirmFn = show;
    return () => {
      confirmFn = null;
    };
  }, [show]);

  const handleConfirm = useCallback(() => {
    resolverRef.current?.(true);
    setState((prev) => ({ ...prev, open: false }));
  }, []);

  const handleCancel = useCallback(() => {
    resolverRef.current?.(false);
    setState((prev) => ({ ...prev, open: false }));
  }, []);

  // ESC 关闭
  useEffect(() => {
    if (!state.open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleCancel();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [state.open, handleCancel]);

  // 禁止背景滚动
  useEffect(() => {
    if (state.open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [state.open]);

  if (typeof window === "undefined") return null;

  const isDanger = state.type === "danger";
  const iconCfg = iconMap[state.type || "warning"];
  const Icon = iconCfg.icon;

  return createPortal(
    <AnimatePresence>
      {state.open && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={handleCancel}
          />

          {/* Panel */}
          <motion.div
            initial={{ opacity: 0, scale: 0.93, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.93, y: 10 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative w-full max-w-sm mx-4 bg-white rounded-2xl shadow-2xl overflow-hidden"
            role="alertdialog"
            aria-modal="true"
            aria-label={state.title}
          >
            <div className="px-6 pt-6 pb-2 text-center">
              <div
                className={`mx-auto w-12 h-12 rounded-full flex items-center justify-center mb-4 ${iconCfg.bg}`}
              >
                <Icon className={`w-6 h-6 ${iconCfg.color}`} />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {state.title}
              </h3>
              <p className="text-sm text-gray-500 leading-relaxed">
                {state.message}
              </p>
            </div>
            <div className="flex gap-3 px-6 pb-6 pt-4">
              <button
                onClick={handleCancel}
                className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors"
              >
                {state.cancelText || "取消"}
              </button>
              <button
                onClick={handleConfirm}
                className={`flex-1 px-4 py-2.5 text-sm font-medium text-white rounded-xl transition-colors ${
                  isDanger
                    ? "bg-red-500 hover:bg-red-600"
                    : "bg-green-500 hover:bg-green-600"
                }`}
              >
                {state.confirmText || "确定"}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body,
  );
}
