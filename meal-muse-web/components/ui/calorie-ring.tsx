"use client";

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

interface CalorieRingProps {
  consumed: number;
  target: number;
  size?: number;
}

const COLORS = ["#22c55e", "#e5e7eb"]; // 已完成 vs 剩余

export function CalorieRing({ consumed, target, size = 120 }: CalorieRingProps) {
  const remaining = Math.max(target - consumed, 0);
  const data = [
    { name: "已摄入", value: consumed },
    { name: "剩余", value: remaining },
  ];

  const innerRadius = size * 0.33;
  const outerRadius = size * 0.46;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            startAngle={90}
            endAngle={-270}
            dataKey="value"
            strokeWidth={0}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span className="text-xl font-bold text-gray-900">{consumed}</span>
        <span className="text-[10px] text-gray-400">/ {target} kcal</span>
      </div>
    </div>
  );
}
