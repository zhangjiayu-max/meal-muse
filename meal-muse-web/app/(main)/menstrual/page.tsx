"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import api from "@/lib/api";
import { Calendar, Droplets, Smile, Apple, AlertCircle } from "lucide-react";

interface CycleRecord {
  id: string;
  period_start: string;
  period_end: string | null;
  cycle_length: number | null;
  current_phase: string;
  phase_diet_tip: {
    phase_name: string;
    diet_focus: string;
    recommended: string[];
    avoid: string[];
    recommended_fruits: string[];
    avoid_fruits: string[];
  };
  symptoms: string[];
  mood: string | null;
}

const phaseColors: Record<string, { bg: string; text: string; border: string }> = {
  menstrual: { bg: "bg-red-50", text: "text-red-700", border: "border-red-200" },
  follicular: { bg: "bg-green-50", text: "text-green-700", border: "border-green-200" },
  ovulation: { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200" },
  luteal: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
};

const phaseIcons: Record<string, string> = {
  menstrual: "🔴", follicular: "🌱", ovulation: "🥚", luteal: "😌",
};

export default function MenstrualPage() {
  const router = useRouter();

  const [current, setCurrent] = useState<CycleRecord | null>(null);
  const [records, setRecords] = useState<CycleRecord[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formDate, setFormDate] = useState("");
  const [formEnd, setFormEnd] = useState("");
  const [symptoms, setSymptoms] = useState<string[]>([]);

  useEffect(() => {
    api.get("/menstrual/current").then(({ data }) => setCurrent(data)).catch(() => {});
    api.get("/menstrual/records").then(({ data }) => setRecords(data)).catch(() => {});
  }, []);

  const handleRecord = async () => {
    if (!formDate) return;
    try {
      await api.post("/menstrual/records", {
        period_start: formDate,
        period_end: formEnd || null,
        symptoms,
      });
      const { data: cur } = await api.get("/menstrual/current");
      setCurrent(cur);
      const { data: recs } = await api.get("/menstrual/records");
      setRecords(recs);
      setShowForm(false);
      setFormDate("");
      setFormEnd("");
      setSymptoms([]);
    } catch { alert("记录失败"); }
  };

  const symptomOptions = ["痛经", "腰酸", "情绪波动", "疲劳", "头痛", "腹胀", "失眠"];

  return (
    <div className="flex flex-col  ">
      <header className="flex items-center justify-between">
        
        <h1 className="text-lg font-bold text-gray-900">经期追踪</h1>
      </header>

      <main className="flex-1 px-4 py-4 space-y-4 pb-20">
        {/* Current Phase */}
        {current && (
          <div className={`${phaseColors[current.current_phase]?.bg || "bg-gray-50"} rounded-xl p-4 border ${phaseColors[current.current_phase]?.border || "border-gray-200"}`}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">{phaseIcons[current.current_phase]}</span>
              <div>
                <h2 className="font-bold text-gray-900">{current.phase_diet_tip.phase_name}</h2>
                <p className="text-xs text-gray-500">当前周期阶段</p>
              </div>
            </div>
            <p className={`text-sm ${phaseColors[current.current_phase]?.text || "text-gray-700"} mb-3`}>
              {current.phase_diet_tip.diet_focus}
            </p>

            <div className="space-y-2">
              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">🥗 推荐食物</p>
                <div className="flex flex-wrap gap-1">
                  {current.phase_diet_tip.recommended?.map((f) => (
                    <span key={f} className="text-xs bg-white/70 px-2 py-0.5 rounded-full text-gray-700">{f}</span>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">🍎 推荐水果</p>
                <div className="flex flex-wrap gap-1">
                  {current.phase_diet_tip.recommended_fruits?.map((f) => (
                    <span key={f} className="text-xs bg-white/70 px-2 py-0.5 rounded-full text-gray-700">{f}</span>
                  ))}
                </div>
              </div>
              {current.phase_diet_tip.avoid?.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">⚠️ 避免食物</p>
                  <div className="flex flex-wrap gap-1">
                    {current.phase_diet_tip.avoid?.map((f) => (
                      <span key={f} className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full">{f}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Record Button */}
        <button onClick={() => setShowForm(true)}
          className="w-full py-3 bg-pink-500 text-white rounded-xl font-medium hover:bg-pink-600 transition-colors flex items-center justify-center gap-2">
          <Droplets className="w-4 h-4" /> 记录经期
        </button>

        {/* Record Form */}
        {showForm && (
          <div className="border border-pink-200 rounded-xl p-4 space-y-3 bg-pink-50">
            <h3 className="font-semibold text-pink-800">记录经期</h3>
            <div>
              <label className="text-xs text-gray-600">开始日期</label>
              <input type="date" value={formDate} onChange={(e) => setFormDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm mt-1" />
            </div>
            <div>
              <label className="text-xs text-gray-600">结束日期（可选）</label>
              <input type="date" value={formEnd} onChange={(e) => setFormEnd(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm mt-1" />
            </div>
            <div>
              <label className="text-xs text-gray-600">症状</label>
              <div className="flex flex-wrap gap-1 mt-1">
                {symptomOptions.map((s) => (
                  <button key={s} onClick={() => setSymptoms(symptoms.includes(s) ? symptoms.filter((x) => x !== s) : [...symptoms, s])}
                    className={`text-xs px-2 py-1 rounded-full transition-colors ${symptoms.includes(s) ? "bg-pink-500 text-white" : "bg-white text-gray-600 border border-gray-200"}`}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowForm(false)} className="flex-1 py-2 text-gray-600 border border-gray-200 rounded-lg text-sm">取消</button>
              <button onClick={handleRecord} className="flex-1 py-2 bg-pink-500 text-white rounded-lg text-sm font-medium">保存</button>
            </div>
          </div>
        )}

        {/* History */}
        {records.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-500 mb-2">历史记录</h3>
            <div className="space-y-2">
              {records.map((r) => (
                <div key={r.id} className="flex items-center justify-between border border-gray-100 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{phaseIcons[r.current_phase]}</span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{r.period_start}</p>
                      <p className="text-xs text-gray-500">
                        {r.phase_diet_tip.phase_name}
                        {r.period_end && ` · ${r.period_end}`}
                      </p>
                    </div>
                  </div>
                  {r.symptoms.length > 0 && (
                    <div className="flex gap-1">
                      {r.symptoms.slice(0, 2).map((s) => (
                        <span key={s} className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">{s}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {!current && records.length === 0 && (
          <div className="text-center py-10">
            <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">还没有经期记录</p>
            <p className="text-gray-400 text-xs mt-1">记录后可获得周期饮食建议</p>
          </div>
        )}
      </main>
    </div>
  );
}
