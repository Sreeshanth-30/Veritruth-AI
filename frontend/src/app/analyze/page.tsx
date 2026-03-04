"use client";

import React, { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { useAnalysisStore } from "@/store/analysis-store";
import { useAnalysisWebSocket } from "@/hooks/use-websocket";
import { AnalysisInputPanel } from "@/components/analysis/input-panel";
import { AnalysisProgressPanel } from "@/components/analysis/progress-panel";
import { AnalysisResultsPanel } from "@/components/analysis/results-panel";
import type { AnalysisProgress } from "@/lib/types";

type AnalysisView = "input" | "processing" | "results";

export default function AnalyzePage() {
  const [view, setView] = useState<AnalysisView>("input");
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [progress, setProgress] = useState<AnalysisProgress | null>(null);

  const { fetchResult, currentAnalysis } = useAnalysisStore();

  const handleProgress = useCallback((p: AnalysisProgress) => {
    setProgress(p);
  }, []);

  const handleComplete = useCallback(() => {
    if (analysisId) {
      fetchResult(analysisId).then(() => setView("results"));
    }
  }, [analysisId, fetchResult]);

  useAnalysisWebSocket(
    view === "processing" ? analysisId : null,
    handleProgress,
    handleComplete
  );

  const handleSubmit = (id: string) => {
    setAnalysisId(id);
    setView("processing");
    // Fallback polling in case WebSocket fails
    const poll = setInterval(async () => {
      try {
        await fetchResult(id);
        const analysis = useAnalysisStore.getState().currentAnalysis;
        if (analysis?.status === "COMPLETED" || analysis?.status === "FAILED") {
          clearInterval(poll);
          setView("results");
        }
      } catch {}
    }, 3000);
    // Cleanup after 10 min
    setTimeout(() => clearInterval(poll), 600_000);
  };

  const handleReset = () => {
    setView("input");
    setAnalysisId(null);
    setProgress(null);
    useAnalysisStore.getState().clearCurrent();
  };

  return (
    <div className="min-h-screen bg-dark-950">
      <Navbar />
      <main className="mx-auto max-w-7xl px-6 pt-28 pb-20">
        <AnimatePresence mode="wait">
          {view === "input" && (
            <motion.div
              key="input"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <AnalysisInputPanel onSubmit={handleSubmit} />
            </motion.div>
          )}

          {view === "processing" && (
            <motion.div
              key="processing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <AnalysisProgressPanel progress={progress} />
            </motion.div>
          )}

          {view === "results" && currentAnalysis && (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <AnalysisResultsPanel
                analysis={currentAnalysis}
                onNewAnalysis={handleReset}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
      <Footer />
    </div>
  );
}
