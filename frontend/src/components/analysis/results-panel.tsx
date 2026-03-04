"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Shield,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  TrendingUp,
  Eye,
  BarChart3,
  Network,
  Search,
  ArrowLeft,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Info,
} from "lucide-react";
import { cn, formatPercentage, getRiskColor, getRiskBgColor, formatDate } from "@/lib/utils";
import type { AnalysisResult, ClaimVerification, PropagandaTechnique } from "@/lib/types";

// ── Chart (simple bar) ───────────────────────────────────────
function ScoreBar({
  label,
  value,
  color = "from-brand-primary to-brand-secondary",
  invert = false,
}: {
  label: string;
  value: number;
  color?: string;
  invert?: boolean;
}) {
  const displayVal = invert ? 1 - value : value;
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-dark-200">{label}</span>
        <span className="font-mono font-semibold text-white">
          {formatPercentage(value)}
        </span>
      </div>
      <div className="mt-1.5 h-2.5 overflow-hidden rounded-full bg-dark-800">
        <motion.div
          className={`h-full rounded-full bg-gradient-to-r ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${Math.round(displayVal * 100)}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

// ── Verdict badge ────────────────────────────────────────────
function VerdictBadge({ verdict }: { verdict: string }) {
  const config: Record<string, { bg: string; text: string; icon: typeof CheckCircle2 }> = {
    SUPPORTED: { bg: "bg-brand-accent/20", text: "text-brand-accent", icon: CheckCircle2 },
    REFUTED: { bg: "bg-brand-danger/20", text: "text-brand-danger", icon: XCircle },
    PARTIALLY_SUPPORTED: { bg: "bg-brand-warning/20", text: "text-brand-warning", icon: AlertTriangle },
    UNVERIFIABLE: { bg: "bg-dark-600/30", text: "text-dark-300", icon: Info },
  };
  const c = config[verdict] || config.UNVERIFIABLE;
  return (
    <span className={cn("risk-badge", c.bg, c.text)}>
      <c.icon className="mr-1 h-3 w-3" />
      {verdict.replace("_", " ")}
    </span>
  );
}

// ── Main component ───────────────────────────────────────────
interface ResultsPanelProps {
  analysis: AnalysisResult;
  onNewAnalysis: () => void;
}

export function AnalysisResultsPanel({ analysis, onNewAnalysis }: ResultsPanelProps) {
  const [activeTab, setActiveTab] = useState<
    "overview" | "claims" | "propaganda" | "sentiment" | "explainability"
  >("overview");

  const riskClass =
    analysis.risk_level === "LOW"
      ? "risk-low"
      : analysis.risk_level === "MEDIUM"
      ? "risk-medium"
      : analysis.risk_level === "HIGH"
      ? "risk-high"
      : "risk-critical";

  const tabs = [
    { key: "overview" as const, label: "Overview", icon: BarChart3 },
    { key: "claims" as const, label: "Claims", icon: Search },
    { key: "propaganda" as const, label: "Propaganda", icon: Eye },
    { key: "sentiment" as const, label: "Sentiment", icon: TrendingUp },
    { key: "explainability" as const, label: "Explain", icon: Info },
  ];

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <button
            onClick={onNewAnalysis}
            className="mb-4 flex items-center gap-2 text-sm text-dark-300 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
            New Analysis
          </button>
          <h1 className="font-heading text-3xl font-bold text-white">
            Analysis Results
          </h1>
          {analysis.title && (
            <p className="mt-1 text-dark-300">{analysis.title}</p>
          )}
          <p className="mt-1 text-xs text-dark-400">
            {formatDate(analysis.created_at)}
            {analysis.source_url && (
              <>
                {" — "}
                <a
                  href={analysis.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-primary hover:underline"
                >
                  Source <ExternalLink className="inline h-3 w-3" />
                </a>
              </>
            )}
          </p>
        </div>
        <div className={cn(riskClass, "text-lg")}>{analysis.risk_level} RISK</div>
      </div>

      {/* Score Cards */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <ScoreCard
          label="Fake Probability"
          value={analysis.fake_probability}
          icon={AlertTriangle}
          color={
            analysis.fake_probability > 0.6
              ? "text-brand-danger"
              : analysis.fake_probability > 0.35
              ? "text-brand-warning"
              : "text-brand-accent"
          }
        />
        <ScoreCard
          label="Credibility"
          value={analysis.credibility_score}
          icon={Shield}
          color={
            analysis.credibility_score > 0.6
              ? "text-brand-accent"
              : "text-brand-warning"
          }
        />
        <ScoreCard
          label="Propaganda"
          value={analysis.propaganda_score}
          icon={Eye}
          color={
            analysis.propaganda_score > 0.5
              ? "text-brand-danger"
              : "text-dark-200"
          }
        />
        <ScoreCard
          label="Confidence"
          value={analysis.confidence_score}
          icon={CheckCircle2}
          color="text-brand-primary"
        />
      </div>

      {/* Tabs */}
      <div className="mt-8 flex gap-2 overflow-x-auto rounded-xl bg-dark-800 p-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              "flex items-center gap-2 whitespace-nowrap rounded-lg px-4 py-2.5 text-sm font-medium transition-all",
              activeTab === tab.key
                ? "bg-gradient-to-r from-brand-primary to-brand-secondary text-white"
                : "text-dark-300 hover:text-white"
            )}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === "overview" && <OverviewTab analysis={analysis} />}
        {activeTab === "claims" && <ClaimsTab analysis={analysis} />}
        {activeTab === "propaganda" && <PropagandaTab analysis={analysis} />}
        {activeTab === "sentiment" && <SentimentTab analysis={analysis} />}
        {activeTab === "explainability" && <ExplainTab analysis={analysis} />}
      </div>
    </div>
  );
}

// ── Score Card ───────────────────────────────────────────────
function ScoreCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number;
  icon: typeof Shield;
  color: string;
}) {
  return (
    <div className="glass-card text-center">
      <Icon className={cn("mx-auto h-6 w-6", color)} />
      <div className={cn("mt-2 font-heading text-3xl font-bold", color)}>
        {formatPercentage(value)}
      </div>
      <div className="mt-1 text-sm text-dark-300">{label}</div>
    </div>
  );
}

// ── Overview Tab ─────────────────────────────────────────────
function OverviewTab({ analysis }: { analysis: AnalysisResult }) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Score Breakdown */}
      <div className="glass-card space-y-5">
        <h3 className="font-heading text-lg font-semibold text-white">
          Score Breakdown
        </h3>
        <ScoreBar
          label="Fake Probability"
          value={analysis.fake_probability}
          color="from-brand-accent to-brand-danger"
        />
        <ScoreBar
          label="Credibility"
          value={analysis.credibility_score}
          color="from-brand-primary to-brand-accent"
        />
        <ScoreBar
          label="Propaganda Level"
          value={analysis.propaganda_score}
          color="from-brand-warning to-brand-danger"
        />
        <ScoreBar
          label="Bias Score"
          value={analysis.bias_score}
          color="from-brand-secondary to-brand-danger"
        />
        <ScoreBar
          label="AI Confidence"
          value={analysis.confidence_score}
          color="from-brand-primary to-brand-secondary"
        />
      </div>

      {/* Quick Stats */}
      <div className="glass-card space-y-4">
        <h3 className="font-heading text-lg font-semibold text-white">
          Summary
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <StatBox label="Claims Found" value={analysis.claim_count} />
          <StatBox
            label="Verified True"
            value={analysis.verified_true_count}
            color="text-brand-accent"
          />
          <StatBox
            label="Verified False"
            value={analysis.verified_false_count}
            color="text-brand-danger"
          />
          <StatBox
            label="Propaganda Techniques"
            value={analysis.propaganda_techniques?.length ?? 0}
          />
        </div>

        {/* Evidence Sources */}
        {analysis.evidence_references?.length > 0 && (
          <div className="mt-4">
            <h4 className="text-sm font-semibold text-dark-200">
              Evidence Sources
            </h4>
            <ul className="mt-2 space-y-2">
              {analysis.evidence_references.slice(0, 5).map((ref, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-dark-300"
                >
                  <ExternalLink className="mt-0.5 h-3 w-3 shrink-0 text-brand-primary" />
                  <a
                    href={ref.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-brand-primary hover:underline"
                  >
                    {ref.title || ref.publisher}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function StatBox({
  label,
  value,
  color = "text-white",
}: {
  label: string;
  value: number;
  color?: string;
}) {
  return (
    <div className="rounded-lg bg-dark-800 p-4 text-center">
      <div className={cn("font-heading text-2xl font-bold", color)}>{value}</div>
      <div className="mt-1 text-xs text-dark-400">{label}</div>
    </div>
  );
}

// ── Claims Tab ───────────────────────────────────────────────
function ClaimsTab({ analysis }: { analysis: AnalysisResult }) {
  const claims = analysis.fact_verification_results ?? analysis.detected_claims ?? [];

  if (!claims.length) {
    return (
      <div className="glass-card text-center text-dark-300 py-12">
        No claims were extracted from this content.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {claims.map((claim: ClaimVerification, i: number) => (
        <div key={i} className="glass-card">
          <div className="flex items-start justify-between gap-4">
            <p className="text-sm text-white">{claim.claim_text}</p>
            <VerdictBadge verdict={claim.verdict} />
          </div>
          {claim.evidence && (
            <p className="mt-3 text-sm text-dark-300">{claim.evidence}</p>
          )}
          {claim.sources?.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {claim.sources.map((src, j) => (
                <a
                  key={j}
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 rounded-full bg-dark-800 px-3 py-1 text-xs text-dark-200 hover:text-brand-primary"
                >
                  <ExternalLink className="h-3 w-3" />
                  {src.publisher || "Source"}
                </a>
              ))}
            </div>
          )}
          <div className="mt-2 text-xs text-dark-400">
            Confidence: {formatPercentage(claim.confidence)}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Propaganda Tab ───────────────────────────────────────────
function PropagandaTab({ analysis }: { analysis: AnalysisResult }) {
  const techniques = analysis.propaganda_techniques ?? [];

  if (!techniques.length) {
    return (
      <div className="glass-card text-center text-dark-300 py-12">
        No propaganda techniques detected.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="glass-card">
        <h3 className="font-heading text-lg font-semibold text-white">
          Detected Propaganda Techniques
        </h3>
        <p className="mt-1 text-sm text-dark-300">
          Overall propaganda score:{" "}
          <span className="font-semibold text-brand-warning">
            {formatPercentage(analysis.propaganda_score)}
          </span>
        </p>
      </div>
      {techniques.map((tech: PropagandaTechnique, i: number) => (
        <div key={i} className="glass-card">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-white">{tech.technique}</h4>
            <span className="text-sm font-mono text-brand-warning">
              {formatPercentage(tech.confidence)}
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-dark-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-brand-warning to-brand-danger"
              style={{ width: `${Math.round(tech.confidence * 100)}%` }}
            />
          </div>
          {tech.instances?.length > 0 && (
            <div className="mt-3 space-y-2">
              {tech.instances.slice(0, 3).map((inst, j) => (
                <p
                  key={j}
                  className="rounded-lg bg-dark-800 px-3 py-2 text-sm italic text-dark-200"
                >
                  &ldquo;{inst}&rdquo;
                </p>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Sentiment Tab ────────────────────────────────────────────
function SentimentTab({ analysis }: { analysis: AnalysisResult }) {
  const sentiment = analysis.sentiment_breakdown;
  if (!sentiment) {
    return (
      <div className="glass-card text-center text-dark-300 py-12">
        Sentiment data unavailable.
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="glass-card space-y-5">
        <h3 className="font-heading text-lg font-semibold text-white">
          Sentiment Analysis
        </h3>
        <div className="flex items-center gap-4">
          <div className="text-3xl font-bold gradient-text">
            {sentiment.overall_sentiment}
          </div>
          <div className="text-sm text-dark-300">
            Score: {formatPercentage(sentiment.sentiment_score)}
          </div>
        </div>
        <ScoreBar
          label="Manipulation Score"
          value={sentiment.manipulation_score}
          color="from-brand-warning to-brand-danger"
        />
      </div>

      <div className="glass-card">
        <h3 className="font-heading text-lg font-semibold text-white">
          Emotion Breakdown
        </h3>
        <div className="mt-4 space-y-3">
          {sentiment.emotions &&
            Object.entries(sentiment.emotions).map(([emotion, score]) => (
              <ScoreBar
                key={emotion}
                label={emotion.charAt(0).toUpperCase() + emotion.slice(1)}
                value={score as number}
                color="from-brand-primary to-brand-secondary"
              />
            ))}
        </div>
      </div>

      {sentiment.manipulation_flags?.length > 0 && (
        <div className="glass-card lg:col-span-2">
          <h3 className="font-heading text-lg font-semibold text-brand-danger">
            Manipulation Flags
          </h3>
          <ul className="mt-3 space-y-2">
            {sentiment.manipulation_flags.map((flag, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-dark-200">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-brand-danger" />
                {flag}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ── Explainability Tab ───────────────────────────────────────
function ExplainTab({ analysis }: { analysis: AnalysisResult }) {
  const data = analysis.explainability_data;
  if (!data?.tokens?.length) {
    return (
      <div className="glass-card text-center text-dark-300 py-12">
        Explainability data unavailable.
      </div>
    );
  }

  const maxShap = Math.max(...data.tokens.map((t) => Math.abs(t.shap_value)));

  return (
    <div className="space-y-6">
      <div className="glass-card">
        <h3 className="font-heading text-lg font-semibold text-white">
          Token-Level Explainability (SHAP)
        </h3>
        <p className="mt-1 text-sm text-dark-300">
          Highlighted tokens show which words contributed most to the AI&apos;s
          fake-news classification. Red = fake signal, green = credible signal.
        </p>
        <div className="mt-4 flex flex-wrap gap-1">
          {data.tokens.slice(0, 200).map((tok, i) => {
            const normalised =
              maxShap > 0 ? tok.shap_value / maxShap : 0;
            const bg =
              normalised > 0.1
                ? `rgba(255,58,92,${Math.min(normalised, 0.8)})`
                : normalised < -0.1
                ? `rgba(0,229,160,${Math.min(Math.abs(normalised), 0.8)})`
                : "transparent";
            return (
              <span
                key={i}
                className="rounded px-1 py-0.5 text-sm text-white"
                style={{ backgroundColor: bg }}
                title={`SHAP: ${tok.shap_value.toFixed(4)}`}
              >
                {tok.token}
              </span>
            );
          })}
        </div>
      </div>

      {/* Suspicious passages */}
      {analysis.suspicious_passages?.length > 0 && (
        <div className="glass-card">
          <h3 className="font-heading text-lg font-semibold text-brand-warning">
            Suspicious Passages
          </h3>
          <div className="mt-4 space-y-3">
            {analysis.suspicious_passages.map((p, i) => (
              <div
                key={i}
                className="rounded-lg border border-brand-warning/20 bg-brand-warning/5 p-4"
              >
                <p className="text-sm text-white">&ldquo;{p.text}&rdquo;</p>
                <p className="mt-2 text-xs text-dark-400">{p.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
