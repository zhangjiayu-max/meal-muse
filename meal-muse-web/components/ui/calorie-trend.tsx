"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface CalorieTrendProps {
  data: Array<{ date: string; calories: number }>;
  target: number;
}

export default function CalorieTrend({ data, target }: CalorieTrendProps) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="date"
          tick={{ fill: "#6b7280", fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: "#e5e7eb" }}
        />
        <YAxis
          tick={{ fill: "#6b7280", fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `${v}`}
        />
        <Tooltip
          contentStyle={{
            background: "#fff",
            border: "1px solid #e5e7eb",
            borderRadius: 8,
            fontSize: 12,
          }}
          formatter={(value) => [`${value} kcal`, "热量"]}
          labelFormatter={(label) => `日期: ${label}`}
        />
        <ReferenceLine
          y={target}
          stroke="#22c55e"
          strokeDasharray="6 4"
          label={{
            value: `目标 ${target} kcal`,
            position: "insideTopRight",
            fill: "#22c55e",
            fontSize: 11,
          }}
        />
        <Line
          type="monotone"
          dataKey="calories"
          stroke="#8b5cf6"
          strokeWidth={2}
          dot={{ r: 4, fill: "#8b5cf6", stroke: "#fff", strokeWidth: 2 }}
          activeDot={{ r: 6, fill: "#8b5cf6" }}
          name="热量"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
