"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import api from "@/lib/api";
import { Scale, Activity, Heart, Droplets, Plus, TrendingDown, TrendingUp } from "lucide-react";

interface BodyMetric {
  metric_date: string;
  weight: number | null;
  body_fat_pct: number | null;
  muscle_mass: number | null;
  bmi: number | null;
  blood_pressure_sys: number | null;
  blood_pressure_dia: number | null;
  blood_sugar: number | null;
  heart_rate: number | null;
  sleep_hours: number | null;
  water_ml: number | null;
  steps: number | null;
}

export default function BodyPage() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<BodyMetric[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ weight: "", body_fat_pct: "", bmi: "", sleep_hours: "", water_ml: "", steps: "" });

  useEffect(() => {
    api.get("/body/metrics?days=30").then(({ data }) => setMetrics(data)).catch(() => {});
  }, []);

  const handleSubmit = async () => {
    try {
      const payload: Record<string, unknown> = {};
      if (form.weight) payload.weight = parseFloat(form.weight);
      if (form.body_fat_pct) payload.body_fat_pct = parseFloat(form.body_fat_pct);
      if (form.bmi) payload.bmi = parseFloat(form.bmi);
      if (form.sleep_hours) payload.sleep_hours = parseFloat(form.sleep_hours);
      if (form.water_ml) payload.water_ml = parseInt(form.water_ml);
      if (form.steps) payload.steps = parseInt(form.steps);
      await api.post("/body/metrics", payload);
      const { data } = await api.get("/body/metrics?days=30");
      setMetrics(data);
      setShowForm(false);
      setForm({ weight: "", body_fat_pct: "", bmi: "", sleep_hours: "", water_ml: "", steps: "" });
    } catch { alert("记录失败"); }
  };

  const latest = metrics[metrics.length - 1];
  const prev = metrics.length >= 2 ? metrics[metrics.length - 2] : null;
  const weightDiff = latest?.weight && prev?.weight ? latest.weight - prev.weight : null;

  return (
    <div className="flex flex-col  ">
      <header className="flex items-center justify-between">
        
        <h1 className="text-lg font-bold text-gray-900">身体数据</h1>
      </header>

      <main className="flex-1 px-4 py-4 space-y-4 pb-20">
        {/* Latest Summary */}
        {latest && (
          <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-blue-800">最新数据</h2>
              <span className="text-xs text-blue-500">{latest.metric_date}</span>
            </div>
            <div className="grid grid-cols-3 gap-3 text-center">
              {latest.weight && (
                <div>
                  <div className="flex items-center justify-center gap-1">
                    <p className="text-xl font-bold text-gray-900">{latest.weight}</p>
                    {weightDiff !== null && (
                      weightDiff > 0
                        ? <TrendingUp className="w-4 h-4 text-red-400" />
                        : <TrendingDown className="w-4 h-4 text-green-400" />
                    )}
                  </div>
                  <p className="text-xs text-gray-500">体重 kg</p>
                </div>
              )}
              {latest.body_fat_pct && (
                <div>
                  <p className="text-xl font-bold text-gray-900">{latest.body_fat_pct}%</p>
                  <p className="text-xs text-gray-500">体脂率</p>
                </div>
              )}
              {latest.bmi && (
                <div>
                  <p className="text-xl font-bold text-gray-900">{latest.bmi}</p>
                  <p className="text-xs text-gray-500">BMI</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Quick Stats */}
        {latest && (
          <div className="grid grid-cols-2 gap-3">
            {latest.sleep_hours && (
              <div className="bg-indigo-50 rounded-xl p-3 flex items-center gap-3">
                <Heart className="w-5 h-5 text-indigo-400" />
                <div>
                  <p className="text-lg font-bold text-gray-900">{latest.sleep_hours}h</p>
                  <p className="text-xs text-gray-500">睡眠</p>
                </div>
              </div>
            )}
            {latest.water_ml && (
              <div className="bg-cyan-50 rounded-xl p-3 flex items-center gap-3">
                <Droplets className="w-5 h-5 text-cyan-400" />
                <div>
                  <p className="text-lg font-bold text-gray-900">{latest.water_ml}ml</p>
                  <p className="text-xs text-gray-500">饮水</p>
                </div>
              </div>
            )}
            {latest.steps && (
              <div className="bg-orange-50 rounded-xl p-3 flex items-center gap-3">
                <Activity className="w-5 h-5 text-orange-400" />
                <div>
                  <p className="text-lg font-bold text-gray-900">{latest.steps.toLocaleString()}</p>
                  <p className="text-xs text-gray-500">步数</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Record Button */}
        <button onClick={() => setShowForm(true)}
          className="w-full py-3 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 transition-colors flex items-center justify-center gap-2">
          <Plus className="w-4 h-4" /> 记录数据
        </button>

        {/* Form */}
        {showForm && (
          <div className="border border-blue-200 rounded-xl p-4 bg-blue-50 space-y-3">
            <h3 className="font-semibold text-blue-800">记录身体数据</h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { key: "weight", label: "体重 (kg)", placeholder: "58.5" },
                { key: "body_fat_pct", label: "体脂率 (%)", placeholder: "25.3" },
                { key: "bmi", label: "BMI", placeholder: "21.5" },
                { key: "sleep_hours", label: "睡眠 (h)", placeholder: "7.5" },
                { key: "water_ml", label: "饮水 (ml)", placeholder: "2000" },
                { key: "steps", label: "步数", placeholder: "8000" },
              ].map((field) => (
                <div key={field.key}>
                  <label className="text-xs text-gray-600">{field.label}</label>
                  <input type="number" value={form[field.key as keyof typeof form]}
                    onChange={(e) => setForm({ ...form, [field.key]: e.target.value })}
                    placeholder={field.placeholder} step="0.1"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm mt-1" />
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowForm(false)} className="flex-1 py-2 text-gray-600 border border-gray-200 rounded-lg text-sm">取消</button>
              <button onClick={handleSubmit} className="flex-1 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium">保存</button>
            </div>
          </div>
        )}

        {/* Weight Trend */}
        {metrics.filter((m) => m.weight).length > 1 && (
          <div className="border border-gray-100 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">📈 体重趋势</h3>
            <div className="flex items-end gap-1 h-20">
              {metrics.filter((m) => m.weight).map((m, i) => {
                const weights = metrics.filter((x) => x.weight).map((x) => x.weight!);
                const min = Math.min(...weights);
                const max = Math.max(...weights);
                const range = max - min || 1;
                const height = ((m.weight! - min) / range) * 60 + 16;
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-[9px] text-gray-400">{m.weight}</span>
                    <div className="w-full bg-blue-400 rounded-t" style={{ height: `${height}px` }} />
                    <span className="text-[8px] text-gray-300">{m.metric_date.slice(5)}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* History */}
        {metrics.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-500 mb-2">历史记录</h3>
            <div className="space-y-1">
              {metrics.slice().reverse().slice(0, 10).map((m, i) => (
                <div key={i} className="flex items-center justify-between px-3 py-2 border border-gray-50 rounded-lg">
                  <span className="text-xs text-gray-500">{m.metric_date}</span>
                  <div className="flex gap-3 text-xs text-gray-600">
                    {m.weight && <span>{m.weight}kg</span>}
                    {m.body_fat_pct && <span>体脂{m.body_fat_pct}%</span>}
                    {m.sleep_hours && <span>睡{m.sleep_hours}h</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {!latest && metrics.length === 0 && (
          <div className="text-center py-10">
            <Scale className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">还没有身体数据</p>
            <p className="text-gray-400 text-xs mt-1">记录体重、体脂等数据，追踪变化趋势</p>
          </div>
        )}
      </main>
    </div>
  );
}
