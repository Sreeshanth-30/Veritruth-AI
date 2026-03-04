"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAnalysisStore } from "@/store/analysis-store";
import { cn, formatDate, formatPercentage, getRiskColor, getRiskBgColor } from "@/lib/utils";
import { Eye, Search, ChevronLeft, ChevronRight } from "lucide-react";
import type { AnalysisListItem } from "@/lib/types";

export default function HistoryPage() {
  const { analyses, fetchList, totalCount, isLoading } = useAnalysisStore();
  const [page, setPage] = useState(1);
  const limit = 20;
  const totalPages = Math.ceil(totalCount / limit);

  useEffect(() => {
    fetchList(page, limit);
  }, [fetchList, page]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold text-white">
          Analysis History
        </h1>
        <p className="mt-1 text-dark-300">
          {totalCount} total analyses
        </p>
      </div>

      <div className="glass-card">
        {isLoading ? (
          <div className="py-12 text-center text-dark-400">Loading…</div>
        ) : analyses.length === 0 ? (
          <div className="py-12 text-center text-dark-400">
            No analyses found.
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-dark-400">
                    <th className="pb-3 font-medium">Title</th>
                    <th className="pb-3 font-medium">Type</th>
                    <th className="pb-3 font-medium">Risk</th>
                    <th className="pb-3 font-medium">Fake</th>
                    <th className="pb-3 font-medium">Credibility</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Date</th>
                    <th className="pb-3 font-medium" />
                  </tr>
                </thead>
                <tbody>
                  {analyses.map((a: AnalysisListItem) => (
                    <tr
                      key={a.id}
                      className="border-b border-white/5 hover:bg-white/5"
                    >
                      <td className="py-3 text-white max-w-xs truncate">
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
                      <td className="py-3 font-mono text-dark-300">-</td>
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
                      <td className="py-3 text-dark-400 text-xs">
                        {formatDate(a.created_at)}
                      </td>
                      <td className="py-3">
                        <Link
                          href={`/analyze?id=${a.id}`}
                          className="text-brand-primary hover:underline"
                        >
                          <Eye className="h-4 w-4" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="mt-6 flex items-center justify-between">
              <p className="text-sm text-dark-400">
                Showing {(page - 1) * limit + 1} –{" "}
                {Math.min(page * limit, totalCount)} of {totalCount}
              </p>
              <div className="flex gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="btn-secondary !px-3 !py-2 disabled:opacity-30"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="btn-secondary !px-3 !py-2 disabled:opacity-30"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
