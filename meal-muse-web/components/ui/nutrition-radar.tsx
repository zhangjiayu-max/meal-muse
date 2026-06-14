"use client";

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
} from "recharts";

interface NutritionRadarProps {
  scores: {
    protein_score: number;
    fat_score: number;
    carbs_score: number;
    fiber_score: number;
    calorie_score: number;
  };
}

const LABELS: Record<string, string> = {
  protein_score: "蛋白质",
  fat_score: "脂肪",
  carbs_score: "碳水",
  fiber_score: "纤维",
  calorie_score: "热量",
};

export function NutritionRadarChart({ scores }: NutritionRadarProps) {
  const data = Object.entries(scores)
    .filter(([key]) => key !== "calorie_score")
    .map(([key, value]) => ({
      subject: LABELS[key] || key,
      value: Math.min(value, 100),
    }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <RadarChart data={data} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fill: "#6b7280", fontSize: 11 }}
        />
        <Radar
          name="营养"
          dataKey="value"
          stroke="#8b5cf6"
          fill="#8b5cf6"
          fillOpacity={0.25}
          strokeWidth={2}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
