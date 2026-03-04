/* ──────────────────────────────────────────────────────────── */
/*  VeriTruth AI — Zustand Auth Store                          */
/* ──────────────────────────────────────────────────────────── */
import { create } from "zustand";
import Cookies from "js-cookie";
import api from "@/lib/api";
import type { User, AuthResponse, LoginRequest, SignupRequest } from "@/lib/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (creds: LoginRequest) => Promise<void>;
  signup: (data: SignupRequest) => Promise<void>;
  googleLogin: (code: string) => Promise<void>;
  logout: () => void;
  fetchProfile: () => Promise<void>;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!Cookies.get("access_token"),
  isLoading: false,

  login: async (creds) => {
    set({ isLoading: true });
    try {
      const { data } = await api.post<AuthResponse>("/auth/login", creds);
      Cookies.set("access_token", data.tokens.access_token, { sameSite: "Strict" });
      Cookies.set("refresh_token", data.tokens.refresh_token, { sameSite: "Strict" });
      set({ user: data.user, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  signup: async (data) => {
    set({ isLoading: true });
    try {
      const { data: res } = await api.post<AuthResponse>("/auth/signup", data);
      Cookies.set("access_token", res.tokens.access_token, { sameSite: "Strict" });
      Cookies.set("refresh_token", res.tokens.refresh_token, { sameSite: "Strict" });
      set({ user: res.user, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  googleLogin: async (code) => {
    set({ isLoading: true });
    try {
      const { data } = await api.post<AuthResponse>("/auth/google", { code });
      Cookies.set("access_token", data.tokens.access_token, { sameSite: "Strict" });
      Cookies.set("refresh_token", data.tokens.refresh_token, { sameSite: "Strict" });
      set({ user: data.user, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  logout: () => {
    Cookies.remove("access_token");
    Cookies.remove("refresh_token");
    set({ user: null, isAuthenticated: false });
  },

  fetchProfile: async () => {
    try {
      const { data } = await api.get<User>("/auth/me");
      set({ user: data, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
    }
  },

  setUser: (user) => set({ user }),
}));
