import { create } from "zustand";
import api from "@/lib/api";
import type { DietRecord, DailyDietSummary } from "@/types";

interface DietState {
  todaySummary: DailyDietSummary | null;
  records: DietRecord[];
  loading: boolean;
  fetchToday: () => Promise<void>;
  fetchRecords: (date?: string) => Promise<void>;
  addRecord: (mealType: string, foodText: string) => Promise<DietRecord>;
  updateRecord: (id: string, data: { food_text?: string; meal_type?: string }) => Promise<DietRecord>;
  deleteRecord: (id: string) => Promise<void>;
}

export const useDietStore = create<DietState>((set) => ({
  todaySummary: null,
  records: [],
  loading: false,

  fetchToday: async () => {
    set({ loading: true });
    try {
      const { data } = await api.get<DailyDietSummary>("/diet/today");
      set({ todaySummary: data, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  fetchRecords: async (date?: string) => {
    set({ loading: true });
    try {
      const params = date ? { record_date: date } : {};
      const { data } = await api.get<DietRecord[]>("/diet/records", { params });
      set({ records: data, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  addRecord: async (mealType, foodText) => {
    const { data } = await api.post<DietRecord>("/diet/records", {
      meal_type: mealType,
      food_text: foodText,
    });
    return data;
  },

  updateRecord: async (id, data) => {
    const { data: updated } = await api.put<DietRecord>(`/diet/records/${id}`, data);
    return updated;
  },

  deleteRecord: async (id) => {
    await api.delete(`/diet/records/${id}`);
  },
}));
