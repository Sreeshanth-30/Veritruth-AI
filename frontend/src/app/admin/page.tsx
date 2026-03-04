"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import api from "@/lib/api";
import { cn, formatDate } from "@/lib/utils";
import type { DashboardStats, AnalyticsData } from "@/lib/types";
import {
  Shield,
  Users,
  Database,
  TrendingUp,
  Search,
  RefreshCw,
  Plus,
  Edit,
  Trash2,
  ChevronDown,
  BarChart3,
  Globe,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from "lucide-react";
import toast from "react-hot-toast";

/* ---------- helpers ---------- */
function StatCard({
  icon: Icon,
  label,
  value,
  trend,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  trend?: string;
  color: string;
}) {
  return (
    <div className="glass-card flex items-start gap-4">
      <div className={cn("rounded-xl p-3", color)}>
        <Icon className="h-5 w-5 text-white" />
      </div>
      <div>
        <p className="text-sm text-dark-400">{label}</p>
        <p className="font-heading text-2xl font-bold text-white">{value}</p>
        {trend && <p className="text-xs text-brand-accent">{trend}</p>}
      </div>
    </div>
  );
}

/* ---------- Admin Page ---------- */
type Tab = "overview" | "users" | "sources" | "labels";

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const qc = useQueryClient();

  /* ---- data ---- */
  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>({
    queryKey: ["admin-stats"],
    queryFn: async () => (await api.get("/admin/stats")).data,
  });

  const { data: analytics } = useQuery<AnalyticsData>({
    queryKey: ["admin-analytics"],
    queryFn: async () => (await api.get("/admin/analytics")).data,
  });

  const { data: users, refetch: refetchUsers } = useQuery<any[]>({
    queryKey: ["admin-users"],
    queryFn: async () => (await api.get("/admin/users")).data,
    enabled: activeTab === "users",
  });

  const { data: sources, refetch: refetchSources } = useQuery<any[]>({
    queryKey: ["admin-sources"],
    queryFn: async () => (await api.get("/admin/sources")).data,
    enabled: activeTab === "sources",
  });

  const { data: labels, refetch: refetchLabels } = useQuery<any[]>({
    queryKey: ["admin-labels"],
    queryFn: async () => (await api.get("/admin/labels")).data,
    enabled: activeTab === "labels",
  });

  /* ---- mutations ---- */
  const deleteUser = useMutation({
    mutationFn: async (id: string) => api.delete(`/admin/users/${id}`),
    onSuccess: () => { toast.success("User removed"); qc.invalidateQueries({ queryKey: ["admin-users"] }); },
  });

  const deleteSource = useMutation({
    mutationFn: async (id: string) => api.delete(`/admin/sources/${id}`),
    onSuccess: () => { toast.success("Source removed"); qc.invalidateQueries({ queryKey: ["admin-sources"] }); },
  });

  /* ---- Source form ---- */
  const [showSourceForm, setShowSourceForm] = useState(false);
  const [sourceForm, setSourceForm] = useState({ domain: "", name: "", credibility_score: 0.5, bias_label: "center", category: "general" });

  const createSource = useMutation({
    mutationFn: async () => api.post("/admin/sources", sourceForm),
    onSuccess: () => {
      toast.success("Source added");
      setShowSourceForm(false);
      qc.invalidateQueries({ queryKey: ["admin-sources"] });
    },
  });

  /* ---- Approve label ---- */
  const approveLabel = useMutation({
    mutationFn: async (id: string) => api.post(`/admin/labels/${id}/approve`),
    onSuccess: () => { toast.success("Label approved"); qc.invalidateQueries({ queryKey: ["admin-labels"] }); },
  });

  const tabs: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: "overview", label: "Overview", icon: BarChart3 },
    { key: "users", label: "Users", icon: Users },
    { key: "sources", label: "Trusted Sources", icon: Globe },
    { key: "labels", label: "Training Labels", icon: Database },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold text-white">Admin Panel</h1>
        <p className="mt-1 text-dark-300">System management &amp; analytics</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-dark-700 pb-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={cn(
              "flex items-center gap-2 rounded-t-lg px-4 py-2 text-sm font-medium transition-colors",
              activeTab === t.key
                ? "bg-dark-800 text-white"
                : "text-dark-400 hover:text-white",
            )}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* ---- OVERVIEW TAB ---- */}
      {activeTab === "overview" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard icon={Users} label="Total Users" value={stats?.total_users ?? "–"} color="bg-brand-primary/20" />
            <StatCard icon={Database} label="Total Analyses" value={stats?.total_analyses ?? "–"} color="bg-brand-secondary/20" />
            <StatCard icon={TrendingUp} label="Avg. Fake Prob." value={stats?.average_fake_probability != null ? `${(stats.average_fake_probability * 100).toFixed(0)}%` : "–"} color="bg-brand-accent/20" />
            <StatCard icon={AlertTriangle} label="High Risk %" value={stats?.high_risk_percentage != null ? `${stats.high_risk_percentage.toFixed(1)}%` : "–"} color="bg-brand-danger/20" />
          </div>

          {/* Analytics */}
          {analytics && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* Risk Distribution */}
              <div className="glass-card">
                <h3 className="mb-4 font-heading text-lg font-semibold text-white">Risk Distribution</h3>
                <div className="space-y-3">
                  {Object.entries(analytics.risk_distribution).map(([label, count]) => {
                    const total = Object.values(analytics.risk_distribution).reduce((a, b) => a + b, 0);
                    const pct = total ? ((count / total) * 100).toFixed(1) : "0";
                    const color = label === "LOW" ? "#00e5a0" : label === "MEDIUM" ? "#ffb830" : label === "HIGH" ? "#ff8c42" : "#ff3a5c";
                    return (
                      <div key={label}>
                        <div className="flex justify-between text-sm text-dark-300">
                          <span className="capitalize">{label.toLowerCase()}</span>
                          <span>{count}</span>
                        </div>
                        <div className="mt-1 h-2 rounded-full bg-dark-700">
                          <div className="h-2 rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Top Risk Domains */}
              <div className="glass-card">
                <h3 className="mb-4 font-heading text-lg font-semibold text-white">Top Risk Domains</h3>
                <div className="space-y-2">
                  {(stats?.top_risk_domains ?? []).map((item, idx) => (
                    <div key={item.domain} className="flex items-center justify-between rounded-lg bg-dark-800/60 px-4 py-2">
                      <div className="flex items-center gap-3">
                        <span className="font-heading text-sm font-bold text-dark-400">#{idx + 1}</span>
                        <span className="text-sm text-white">{item.domain}</span>
                      </div>
                      <span className="text-xs text-dark-400">{item.fake_count} flagged</span>
                    </div>
                  ))}
                  {!stats?.top_risk_domains?.length && <p className="text-sm text-dark-500">No domain data yet.</p>}
                </div>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* ---- USERS TAB ---- */}
      {activeTab === "users" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card overflow-auto">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-heading text-lg font-semibold text-white">Registered Users</h3>
            <button onClick={() => refetchUsers()} className="btn-secondary !py-1 !px-3 text-sm flex items-center gap-1">
              <RefreshCw className="h-3 w-3" /> Refresh
            </button>
          </div>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-dark-700 text-dark-400">
                <th className="py-2 pr-4">Name</th>
                <th className="py-2 pr-4">Email</th>
                <th className="py-2 pr-4">Role</th>
                <th className="py-2 pr-4">Joined</th>
                <th className="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(users ?? []).map((u: any) => (
                <tr key={u.id} className="border-b border-dark-800 text-dark-200">
                  <td className="py-2 pr-4">{u.full_name}</td>
                  <td className="py-2 pr-4">{u.email}</td>
                  <td className="py-2 pr-4">
                    <span className="risk-badge bg-dark-700">{u.role}</span>
                  </td>
                  <td className="py-2 pr-4">{formatDate(u.created_at)}</td>
                  <td className="py-2">
                    <button
                      onClick={() => deleteUser.mutate(u.id)}
                      className="text-brand-danger hover:text-red-400"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {!users?.length && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-dark-500">No users found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </motion.div>
      )}

      {/* ---- SOURCES TAB ---- */}
      {activeTab === "sources" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-heading text-lg font-semibold text-white">Trusted Sources</h3>
            <button onClick={() => setShowSourceForm(!showSourceForm)} className="btn-primary !py-2 !px-4 text-sm flex items-center gap-2">
              <Plus className="h-4 w-4" /> Add Source
            </button>
          </div>

          <AnimatePresence>
            {showSourceForm && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="glass-card overflow-hidden">
                <h4 className="mb-3 font-heading text-base font-semibold text-white">New Trusted Source</h4>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <input className="input-field" placeholder="Domain (e.g. reuters.com)" value={sourceForm.domain} onChange={e => setSourceForm(p => ({ ...p, domain: e.target.value }))} />
                  <input className="input-field" placeholder="Display Name" value={sourceForm.name} onChange={e => setSourceForm(p => ({ ...p, name: e.target.value }))} />
                  <input className="input-field" type="number" min="0" max="1" step="0.05" placeholder="Credibility (0-1)" value={sourceForm.credibility_score} onChange={e => setSourceForm(p => ({ ...p, credibility_score: +e.target.value }))} />
                  <select className="input-field" value={sourceForm.bias_label} onChange={e => setSourceForm(p => ({ ...p, bias_label: e.target.value }))}>
                    <option value="left">Left</option>
                    <option value="center-left">Center-Left</option>
                    <option value="center">Center</option>
                    <option value="center-right">Center-Right</option>
                    <option value="right">Right</option>
                  </select>
                  <select className="input-field" value={sourceForm.category} onChange={e => setSourceForm(p => ({ ...p, category: e.target.value }))}>
                    <option value="general">General</option>
                    <option value="news">News</option>
                    <option value="academic">Academic</option>
                    <option value="government">Government</option>
                    <option value="satire">Satire</option>
                  </select>
                </div>
                <div className="mt-4 flex gap-2">
                  <button onClick={() => createSource.mutate()} className="btn-primary !py-2 !px-4 text-sm">Save</button>
                  <button onClick={() => setShowSourceForm(false)} className="btn-secondary !py-2 !px-4 text-sm">Cancel</button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="glass-card overflow-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-dark-700 text-dark-400">
                  <th className="py-2 pr-4">Domain</th>
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Credibility</th>
                  <th className="py-2 pr-4">Bias</th>
                  <th className="py-2 pr-4">Category</th>
                  <th className="py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {(sources ?? []).map((s: any) => (
                  <tr key={s.id} className="border-b border-dark-800 text-dark-200">
                    <td className="py-2 pr-4 font-medium text-white">{s.domain}</td>
                    <td className="py-2 pr-4">{s.name}</td>
                    <td className="py-2 pr-4">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-16 rounded-full bg-dark-700">
                          <div className="h-2 rounded-full bg-brand-accent" style={{ width: `${(s.credibility_score ?? 0) * 100}%` }} />
                        </div>
                        <span>{((s.credibility_score ?? 0) * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="py-2 pr-4 capitalize">{s.bias_label}</td>
                    <td className="py-2 pr-4 capitalize">{s.category}</td>
                    <td className="py-2">
                      <button onClick={() => deleteSource.mutate(s.id)} className="text-brand-danger hover:text-red-400">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
                {!sources?.length && (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-dark-500">No trusted sources configured.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* ---- LABELS TAB ---- */}
      {activeTab === "labels" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card overflow-auto">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-heading text-lg font-semibold text-white">Community Training Labels</h3>
            <button onClick={() => refetchLabels()} className="btn-secondary !py-1 !px-3 text-sm flex items-center gap-1">
              <RefreshCw className="h-3 w-3" /> Refresh
            </button>
          </div>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-dark-700 text-dark-400">
                <th className="py-2 pr-4">Content Hash</th>
                <th className="py-2 pr-4">User Label</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Submitted</th>
                <th className="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(labels ?? []).map((l: any) => (
                <tr key={l.id ?? l._id} className="border-b border-dark-800 text-dark-200">
                  <td className="py-2 pr-4 font-mono text-xs">{(l.content_hash ?? "").slice(0, 16)}…</td>
                  <td className="py-2 pr-4">
                    <span className={cn("risk-badge",
                      l.label === "real" ? "bg-green-900/40 text-green-400" :
                      l.label === "fake" ? "bg-red-900/40 text-red-400" :
                      "bg-yellow-900/40 text-yellow-400"
                    )}>
                      {l.label}
                    </span>
                  </td>
                  <td className="py-2 pr-4">
                    {l.approved ? (
                      <span className="flex items-center gap-1 text-brand-accent"><CheckCircle className="h-3 w-3" /> Approved</span>
                    ) : (
                      <span className="flex items-center gap-1 text-dark-400"><XCircle className="h-3 w-3" /> Pending</span>
                    )}
                  </td>
                  <td className="py-2 pr-4">{formatDate(l.created_at)}</td>
                  <td className="py-2">
                    {!l.approved && (
                      <button
                        onClick={() => approveLabel.mutate(l.id ?? l._id)}
                        className="text-brand-accent hover:text-green-300 text-xs font-medium"
                      >
                        Approve
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {!labels?.length && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-dark-500">No community labels submitted yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </motion.div>
      )}
    </div>
  );
}
