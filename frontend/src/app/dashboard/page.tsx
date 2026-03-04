"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";
import { useAnalysisStore } from "@/store/analysis-store";
import { cn, formatDate, formatPercentage, getRiskColor, getRiskBgColor } from "@/lib/utils";
import {
  BarChart3,
  TrendingUp,
  Shield,
  AlertTriangle,
  Search,
  Clock,
  ArrowRight,
  ChevronRight,
  Eye,
  Loader2,
} from "lucide-react";
import type { AnalysisListItem, DashboardStats } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const { user, fetchProfile, isAuthenticated } = useAuthStore();
  const { analyses, fetchList, totalCount, isLoading, error } = useAnalysisStore();

  useEffect(() => {
    // Redirect unauthenticated users to login
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    fetchProfile();
    fetchList(1, 10);
  }, [isAuthenticated, fetchProfile, fetchList, router]);

  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ["dashboard-stats"],
    queryFn: async () => {
      try {
        const { data } = await api.get("/admin/stats");
        return data;
      } catch {
        return null;
      }
    },
  });

  const statCards = [
    {
      label: "Total Analyses",
      value: stats?.total_analyses ?? totalCount,
      icon: BarChart3,
      color: "from-brand-primary to-brand-secondary",
    },
    {
      label: "Today's Analyses",
      value: stats?.analyses_today ?? user?.analysis_count_today ?? 0,
      icon: Clock,
      color: "from-brand-secondary to-purple-500",
    },
    {
      label: "Avg Fake Probability",
      value: stats?.average_fake_probability
        ? formatPercentage(stats.average_fake_probability)
        : "—",
      icon: AlertTriangle,
      color: "from-brand-warning to-orange-500",
    },
    {
      label: "High Risk %",
      value: stats?.high_risk_percentage
        ? formatPercentage(stats.high_risk_percentage)
        : "—",
      icon: Shield,
      color: "from-brand-danger to-pink-500",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-heading text-3xl font-bold text-white">
          Welcome back, {user?.first_name || "User"}
        </h1>
        <p className="mt-1 text-dark-300">
          Here&apos;s your analysis overview and recent activity.
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-card"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dark-300">{card.label}</p>
                <p className="mt-1 font-heading text-3xl font-bold text-white">
                  {card.value}
                </p>
              </div>
              <div
                className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${card.color} shadow-glow`}
              >
                <card.icon className="h-6 w-6 text-white" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="flex gap-4">
        <Link href="/analyze" className="btn-primary">
          <Search className="mr-2 h-4 w-4" />
          New Analysis
        </Link>
        <Link href="/dashboard/history" className="btn-secondary">
          <Clock className="mr-2 h-4 w-4" />
          View History
        </Link>
      </div>

      {/* Recent Analyses Table */}
      <div className="glass-card">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-lg font-semibold text-white">
            Recent Analyses
          </h2>
          <Link
            href="/dashboard/history"
            className="flex items-center gap-1 text-sm text-brand-primary hover:underline"
          >
            View All <ChevronRight className="h-4 w-4" />
          </Link>
        </div>

        {isLoading ? (
          <div className="mt-6 flex items-center justify-center py-12 text-dark-400">
            <Loader2 className="h-8 w-8 animate-spin text-brand-primary" />
            <span className="ml-3">Loading analyses…</span>
          </div>
        ) : error ? (
          <div className="mt-6 rounded-lg bg-brand-danger/10 border border-brand-danger/20 p-6 text-center">
            <AlertTriangle className="mx-auto h-8 w-8 text-brand-danger" />
            <p className="mt-3 text-sm text-brand-danger font-medium">{error}</p>
            <button
              onClick={() => fetchList(1, 10)}
              className="mt-4 btn-secondary !py-1.5 !px-4 text-xs"
            >
              Retry
            </button>
          </div>
        ) : analyses.length === 0 ? (
          <div className="mt-6 text-center text-dark-400 py-12">
            <Search className="mx-auto h-10 w-10 text-dark-500" />
            <p className="mt-4">No analyses yet.</p>
            <Link
              href="/analyze"
              className="mt-4 inline-flex items-center gap-2 text-sm text-brand-primary hover:underline"
            >
              Run your first analysis <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-white/10 text-dark-400">
                  <th className="pb-3 font-medium">Title / Source</th>
                  <th className="pb-3 font-medium">Type</th>
                  <th className="pb-3 font-medium">Risk</th>
                  <th className="pb-3 font-medium">Fake Prob.</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Date</th>
                  <th className="pb-3 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {analyses.slice(0, 10).map((a: AnalysisListItem) => (
                  <tr
                    key={a.id}
                    className="border-b border-white/5 hover:bg-white/5"
                  >
                    <td className="py-3 text-white">
                      {a.title || a.source_url || "Untitled"}
                    </td>
                    <td className="py-3 text-dark-300 uppercase text-xs">
                      {a.input_type}
                    </td>
                    <td className="py-3">
                      <span
                        className={cn(
                          "risk-badge",
                          getRiskBgColor(a.risk_level),
                          getRiskColor(a.risk_level)
                        )}
                      >
                        {a.risk_level}
                      </span>
                    </td>
                    <td className="py-3 font-mono text-white">
                      {formatPercentage(a.fake_probability)}
                    </td>
                    <td className="py-3">
                      <span
                        className={cn(
                          "text-xs font-medium",
                          a.status === "COMPLETED"
                            ? "text-brand-accent"
                            : a.status === "FAILED"
                            ? "text-brand-danger"
                            : "text-brand-warning"
                        )}
                      >
                        {a.status}
                      </span>
                    </td>
                    <td className="py-3 text-dark-400">
                      {formatDate(a.created_at)}
                    </td>
                    <td className="py-3">
                      <Link
                        href={`/analyze?id=${a.id}`}
                        className="text-brand-primary hover:underline text-xs"
                      >
                        <Eye className="h-4 w-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
