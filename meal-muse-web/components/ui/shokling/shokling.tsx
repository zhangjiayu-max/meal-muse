"use client";

import { type ShoklingMood, MOOD_EMOJI, MOOD_LABEL } from "./evolution";

interface ShoklingProps {
  mood?: ShoklingMood;
  emoji?: string; // 进化形态 emoji，覆盖 mood
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
  /** 点击回调 */
  onClick?: () => void;
}

const sizeMap = {
  sm: { container: "w-8 h-8 text-lg", label: "text-[10px]" },
  md: { container: "w-12 h-12 text-2xl", label: "text-xs" },
  lg: { container: "w-16 h-16 text-4xl", label: "text-sm" },
};

export function Shokling({
  mood = "happy",
  emoji,
  size = "md",
  showLabel = false,
  className = "",
  onClick,
}: ShoklingProps) {
  const sz = sizeMap[size];
  const displayEmoji = emoji || MOOD_EMOJI[mood];

  return (
    <div
      className={`flex flex-col items-center gap-1 ${onClick ? "cursor-pointer" : ""} ${className}`}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div
        className={`
          ${sz.container} rounded-full flex items-center justify-center
          transition-all duration-300 select-none
          ${mood === "happy" ? "bg-green-100" : ""}
          ${mood === "celebrate" ? "bg-yellow-100 scale-110" : ""}
          ${mood === "thinking" ? "bg-blue-100" : ""}
          ${mood === "sleepy" ? "bg-indigo-100" : ""}
          ${mood === "embarrassed" ? "bg-red-100" : ""}
          ${mood === "fire" ? "bg-orange-100" : ""}
          ${mood === "sad" ? "bg-gray-100" : ""}
          ${mood === "evolve" ? "bg-purple-100 animate-pulse" : ""}
        `}
      >
        {displayEmoji}
      </div>
      {showLabel && (
        <span className={`${sz.label} text-gray-400`}>
          {MOOD_LABEL[mood]}
        </span>
      )}
    </div>
  );
}
