import { create } from "zustand";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  _hydrated: boolean;
  hydrate: () => void;
  login: (token: string, user: User) => void;
  logout: () => void;
  updateUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  _hydrated: false,

  hydrate: () => {
    if (get()._hydrated) return;
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("token");
    const user = localStorage.getItem("user");
    set({
      token,
      user: user ? JSON.parse(user) : null,
      isAuthenticated: !!token,
      _hydrated: true,
    });
  },

  login: (token, user) => {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
    set({ user, token, isAuthenticated: true, _hydrated: true });
  },

  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    set({ user: null, token: null, isAuthenticated: false });
  },

  updateUser: (user) => {
    localStorage.setItem("user", JSON.stringify(user));
    set({ user });
  },
}));
