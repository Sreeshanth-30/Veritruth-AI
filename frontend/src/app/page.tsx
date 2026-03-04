"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import {
  Shield,
  Brain,
  Search,
  BarChart3,
  Network,
  Zap,
  FileText,
  Globe,
  Upload,
  ChevronRight,
  CheckCircle2,
  Users,
  TrendingUp,
  Eye,
  Sparkles,
  Lock,
  ArrowRight,
} from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.6, ease: "easeOut" },
  }),
};

const features = [
  {
    icon: Brain,
    title: "AI Classification",
    description:
      "RoBERTa & DeBERTa transformer models classify content with 96%+ accuracy, enhanced by SHAP explainability.",
    color: "from-brand-primary to-blue-500",
  },
  {
    icon: Search,
    title: "Claim Extraction & Fact-Check",
    description:
      "spaCy NLP extracts verifiable claims, then a RAG pipeline cross-references against trusted fact-check databases.",
    color: "from-brand-secondary to-purple-500",
  },
  {
    icon: Eye,
    title: "Propaganda Detection",
    description:
      "Identifies 18 propaganda techniques (ad hominem, appeal to fear, loaded language, etc.) with sentence-level heatmaps.",
    color: "from-orange-500 to-brand-warning",
  },
  {
    icon: BarChart3,
    title: "Sentiment & Manipulation",
    description:
      "Multi-dimensional sentiment analysis detects emotional manipulation, fear-urgency combos, and outrage amplification.",
    color: "from-brand-accent to-green-500",
  },
  {
    icon: Network,
    title: "Knowledge Graph",
    description:
      "Neo4j-powered entity-relationship graph visualises claim connections, contradictions, and source relationships.",
    color: "from-brand-primary to-brand-accent",
  },
  {
    icon: Shield,
    title: "Source Credibility",
    description:
      "Multi-factor credibility scoring: domain reputation, historical accuracy, editorial standards, citation density.",
    color: "from-brand-danger to-pink-500",
  },
];

const howItWorks = [
  {
    step: 1,
    icon: FileText,
    title: "Submit Content",
    description: "Paste an article, enter a URL, or upload a PDF for analysis.",
  },
  {
    step: 2,
    icon: Brain,
    title: "AI Processes",
    description:
      "7-layer AI pipeline analyses content in parallel — classification, claims, facts, propaganda, sentiment, credibility, knowledge graph.",
  },
  {
    step: 3,
    icon: BarChart3,
    title: "Get Results",
    description:
      "Receive a comprehensive report with risk score, evidence, explanations, and an interactive knowledge graph.",
  },
];

const stats = [
  { value: "96%+", label: "Detection Accuracy" },
  { value: "7", label: "Analysis Layers" },
  { value: "18", label: "Propaganda Techniques" },
  { value: "<30s", label: "Full Analysis" },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-dark-950">
      <Navbar />

      {/* ── Hero Section ─────────────────────────────────── */}
      <section className="relative overflow-hidden pt-32 pb-20">
        {/* Background Effects */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/4 top-1/4 h-96 w-96 rounded-full bg-brand-primary/10 blur-[120px]" />
          <div className="absolute right-1/4 bottom-1/4 h-96 w-96 rounded-full bg-brand-secondary/10 blur-[120px]" />
        </div>

        <div className="relative mx-auto max-w-7xl px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center gap-2 rounded-full border border-brand-primary/30 bg-brand-primary/10 px-4 py-1.5 text-sm text-brand-primary">
              <Sparkles className="h-4 w-4" />
              AI-Powered Misinformation Detection
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mt-8 font-heading text-5xl font-bold leading-tight tracking-tight text-white sm:text-6xl lg:text-7xl"
          >
            Detect Fake News with{" "}
            <span className="gradient-text">Multi-Layer AI</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mx-auto mt-6 max-w-2xl text-lg text-dark-200"
          >
            VeriTruth AI analyses articles through 7 intelligence layers —
            classification, claim extraction, fact verification, propaganda
            detection, sentiment analysis, source credibility, and knowledge
            graphs — giving you the full picture.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
          >
            <Link href="/analyze" className="btn-primary text-lg">
              Start Analyzing
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
            <Link href="/signup" className="btn-secondary text-lg">
              Create Free Account
            </Link>
          </motion.div>

          {/* Stats row */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="mx-auto mt-16 grid max-w-3xl grid-cols-2 gap-8 sm:grid-cols-4"
          >
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="font-heading text-3xl font-bold gradient-text">
                  {stat.value}
                </div>
                <div className="mt-1 text-sm text-dark-300">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── Features Grid ────────────────────────────────── */}
      <section className="py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h2 className="section-title">
              6 Intelligence Layers,{" "}
              <span className="gradient-text">One Platform</span>
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-dark-300">
              Each article is processed through multiple AI models that work
              together to build a complete picture of content reliability.
            </p>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-50px" }}
                variants={fadeUp}
                className="glass-card-hover group"
              >
                <div
                  className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${feature.color}`}
                >
                  <feature.icon className="h-6 w-6 text-white" />
                </div>
                <h3 className="font-heading text-lg font-semibold text-white">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm text-dark-300">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ─────────────────────────────────── */}
      <section className="py-24 bg-dark-900/50">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h2 className="section-title">
              How It <span className="gradient-text">Works</span>
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-dark-300">
              Three simple steps to verify any news content.
            </p>
          </div>

          <div className="mt-16 grid gap-12 md:grid-cols-3">
            {howItWorks.map((item, i) => (
              <motion.div
                key={item.step}
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
                className="relative text-center"
              >
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-primary to-brand-secondary text-white shadow-glow">
                  <item.icon className="h-8 w-8" />
                </div>
                <div className="absolute -top-2 left-1/2 -translate-x-1/2 font-heading text-7xl font-bold text-white/5">
                  {item.step}
                </div>
                <h3 className="font-heading text-xl font-semibold text-white">
                  {item.title}
                </h3>
                <p className="mt-3 text-sm text-dark-300">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA Section ──────────────────────────────────── */}
      <section className="py-24">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="glass-card p-12"
          >
            <h2 className="font-heading text-3xl font-bold text-white sm:text-4xl">
              Ready to Fight <span className="gradient-text">Misinformation</span>?
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-dark-300">
              Join thousands of students and researchers using VeriTruth AI to
              verify news content and build media literacy skills.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link href="/signup" className="btn-primary text-lg">
                Get Started Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
              <Link href="/analyze" className="btn-secondary text-lg">
                Try Without Account
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
