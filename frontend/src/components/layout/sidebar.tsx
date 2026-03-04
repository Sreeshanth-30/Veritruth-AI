"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  BarChart3,
  Network,
  ShieldCheck,
  Settings,
  HelpCircle,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

const sidebarLinks = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/analyze", label: "Analyze", icon: Search },
  { href: "/dashboard/history", label: "History", icon: BarChart3 },
  { href: "/dashboard/knowledge-graph", label: "Knowledge Graph", icon: Network },
];

const adminLinks = [
  { href: "/admin", label: "Admin Panel", icon: ShieldCheck },
  { href: "/admin/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [collapsed, setCollapsed] = React.useState(false);
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => setMounted(true), []);

  const isAdmin = mounted && user?.role === "admin";

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-white/10 bg-dark-900/95 backdrop-blur-xl transition-all duration-300",
        collapsed ? "w-20" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 border-b border-white/10 px-6 py-5">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-primary to-brand-secondary">
          <ShieldCheck className="h-5 w-5 text-white" />
        </div>
        {!collapsed && (
          <span className="font-heading text-lg font-bold text-white">VeriTruth</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-4 py-6">
        <div className="space-y-1">
          {sidebarLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  isActive ? "sidebar-link-active" : "sidebar-link",
                  collapsed && "justify-center px-2"
                )}
                title={collapsed ? link.label : undefined}
              >
                <link.icon className="h-5 w-5 shrink-0" />
                {!collapsed && <span>{link.label}</span>}
              </Link>
            );
          })}
        </div>

        {isAdmin && (
          <>
            <div className="my-6 border-t border-white/10" />
            <p
              className={cn(
                "mb-2 px-4 text-xs font-semibold uppercase tracking-wider text-dark-400",
                collapsed && "text-center"
              )}
            >
              {collapsed ? "•" : "Admin"}
            </p>
            <div className="space-y-1">
              {adminLinks.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={cn(
                      isActive ? "sidebar-link-active" : "sidebar-link",
                      collapsed && "justify-center px-2"
                    )}
                    title={collapsed ? link.label : undefined}
                  >
                    <link.icon className="h-5 w-5 shrink-0" />
                    {!collapsed && <span>{link.label}</span>}
                  </Link>
                );
              })}
            </div>
          </>
        )}
      </nav>

      {/* Bottom */}
      <div className="border-t border-white/10 px-4 py-4">
        <button
          onClick={handleLogout}
          className={cn(
            "sidebar-link w-full text-brand-danger hover:bg-brand-danger/10",
            collapsed && "justify-center px-2"
          )}
        >
          <LogOut className="h-5 w-5 shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-white/10 bg-dark-800 text-dark-300 hover:text-white"
      >
        {collapsed ? (
          <ChevronRight className="h-3 w-3" />
        ) : (
          <ChevronLeft className="h-3 w-3" />
        )}
      </button>
    </aside>
  );
}
