/* ──────────────────────────────────────────────────────────── */
/*  VeriTruth AI — Zustand Analysis Store                      */
/* ──────────────────────────────────────────────────────────── */
import { create } from "zustand";
import api from "@/lib/api";
import type {
  AnalysisResult,
  AnalysisListItem,
  AnalysisProgress,
} from "@/lib/types";

interface AnalysisState {
  // Current analysis being viewed
  currentAnalysis: AnalysisResult | null;
  currentProgress: AnalysisProgress | null;
  // List of past analyses
  analyses: AnalysisListItem[];
  totalCount: number;
  // UI state
  isSubmitting: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  submitText: (text: string) => Promise<string>;
  submitUrl: (url: string) => Promise<string>;
  submitFile: (file: File) => Promise<string>;
  fetchResult: (id: string) => Promise<void>;
  fetchList: (page?: number, limit?: number) => Promise<void>;
  setProgress: (progress: AnalysisProgress) => void;
  clearCurrent: () => void;
  clearError: () => void;
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  currentAnalysis: null,
  currentProgress: null,
  analyses: [],
  totalCount: 0,
  isSubmitting: false,
  isLoading: false,
  error: null,

  submitText: async (text) => {
    set({ isSubmitting: true });
    try {
      const { data } = await api.post("/analysis/text", { text });
      return String(data.id ?? data.analysis_id);
    } finally {
      set({ isSubmitting: false });
    }
  },

  submitUrl: async (url) => {
    set({ isSubmitting: true });
    try {
      const { data } = await api.post("/analysis/url", { url });
      return String(data.id ?? data.analysis_id);
    } finally {
      set({ isSubmitting: false });
    }
  },

  submitFile: async (file) => {
    set({ isSubmitting: true });
    try {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post("/analysis/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return String(data.id ?? data.analysis_id);
    } finally {
      set({ isSubmitting: false });
    }
  },

  fetchResult: async (id) => {
    set({ isLoading: true });
    try {
      const { data } = await api.get<AnalysisResult>(`/analysis/${id}`);
      set({ currentAnalysis: data });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchList: async (page = 1, limit = 20) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.get("/analysis", {
        params: { page, page_size: limit },
      });
      set({ analyses: data.items ?? [], totalCount: data.total ?? 0 });
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to load analyses";
      set({ error: msg, analyses: [], totalCount: 0 });
    } finally {
      set({ isLoading: false });
    }
  },

  setProgress: (progress) => set({ currentProgress: progress }),
  clearCurrent: () => set({ currentAnalysis: null, currentProgress: null }),
  clearError: () => set({ error: null }),
}));
