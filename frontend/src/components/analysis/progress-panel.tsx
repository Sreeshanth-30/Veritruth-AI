"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  Brain,
  Search,
  CheckCircle2,
  Eye,
  BarChart3,
  Sparkles,
  Shield,
  Network,
  Loader2,
} from "lucide-react";
import type { AnalysisProgress } from "@/lib/types";
import { cn } from "@/lib/utils";

const stages = [
  { key: "classification", label: "AI Classification", icon: Brain },
  { key: "claims", label: "Claim Extraction", icon: Search },
  { key: "fact_check", label: "Fact Verification", icon: CheckCircle2 },
  { key: "propaganda", label: "Propaganda Detection", icon: Eye },
  { key: "sentiment", label: "Sentiment Analysis", icon: BarChart3 },
  { key: "explainability", label: "SHAP Explanations", icon: Sparkles },
  { key: "credibility", label: "Credibility Scoring", icon: Shield },
  { key: "knowledge_graph", label: "Knowledge Graph", icon: Network },
];

interface ProgressPanelProps {
  progress: AnalysisProgress | null;
}

export function AnalysisProgressPanel({ progress }: ProgressPanelProps) {
  const currentStageIndex = stages.findIndex(
    (s) => s.key === progress?.stage
  );
  const pct = progress?.progress ?? 0;

  return (
    <div className="mx-auto max-w-3xl text-center">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="mb-8"
      >
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-brand-primary to-brand-secondary shadow-glow-lg">
          <Brain className="h-10 w-10 animate-pulse text-white" />
        </div>
      </motion.div>

      <h2 className="font-heading text-3xl font-bold text-white">
        Analyzing Content…
      </h2>
      <p className="mt-2 text-dark-300">
        {progress?.detail || "Initializing AI pipeline…"}
      </p>

      {/* Progress bar */}
      <div className="mx-auto mt-8 max-w-lg">
        <div className="h-3 overflow-hidden rounded-full bg-dark-800">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-brand-primary to-brand-secondary"
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
        <p className="mt-2 text-sm font-medium text-brand-primary">{pct}%</p>
      </div>

      {/* Stage indicators */}
      <div className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {stages.map((stage, i) => {
          const isCompleted = i < currentStageIndex;
          const isCurrent = i === currentStageIndex;

          return (
            <div
              key={stage.key}
              className={cn(
                "glass-card flex items-center gap-3 !p-4 text-left transition-all",
                isCompleted && "border-brand-accent/30",
                isCurrent && "border-brand-primary/30 shadow-glow"
              )}
            >
              <div
                className={cn(
                  "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
                  isCompleted && "bg-brand-accent/20 text-brand-accent",
                  isCurrent &&
                    "bg-brand-primary/20 text-brand-primary",
                  !isCompleted && !isCurrent && "bg-dark-700 text-dark-400"
                )}
              >
                {isCurrent ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : isCompleted ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : (
                  <stage.icon className="h-4 w-4" />
                )}
              </div>
              <span
                className={cn(
                  "text-sm font-medium",
                  isCompleted && "text-brand-accent",
                  isCurrent && "text-white",
                  !isCompleted && !isCurrent && "text-dark-400"
                )}
              >
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
