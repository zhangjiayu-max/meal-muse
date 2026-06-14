"use client";

import { motion } from "framer-motion";
import { Shokling } from "./shokling";
import type { ShoklingMood } from "./evolution";

interface ShoklingBubbleProps {
  mood?: ShoklingMood;
  emoji?: string;
  message: string;
  /** bubble 位置：left = 食灵在左，right = 食灵在右 */
  side?: "left" | "right";
  size?: "sm" | "md" | "lg";
  className?: string;
  /** 是否显示入场动画 */
  animate?: boolean;
  /** 点击食灵 */
  onShoklingClick?: () => void;
}

export function ShoklingBubble({
  mood = "happy",
  emoji,
  message,
  side = "left",
  size = "md",
  className = "",
  animate = true,
  onShoklingClick,
}: ShoklingBubbleProps) {
  const content = (
    <div
      className={`flex items-start gap-3 ${side === "right" ? "flex-row-reverse" : ""} ${className}`}
    >
      <Shokling mood={mood} emoji={emoji} size={size} onClick={onShoklingClick} />
      <div
        className={`
          relative flex-1 px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap
          ${side === "left" ? "bg-gray-100 text-gray-800 rounded-tl-sm" : "bg-green-500 text-white rounded-tr-sm"}
        `}
      >
        {message}
      </div>
    </div>
  );

  if (animate) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {content}
      </motion.div>
    );
  }

  return content;
}
