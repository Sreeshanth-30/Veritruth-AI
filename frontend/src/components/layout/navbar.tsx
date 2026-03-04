"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthStore } from "@/store/auth-store";
import {
  Shield,
  Menu,
  X,
  LogIn,
  UserPlus,
  LogOut,
  LayoutDashboard,
  Search,
  User,
} from "lucide-react";

export function Navbar() {
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [mounted, setMounted] = React.useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  React.useEffect(() => setMounted(true), []);

  // Use auth state only after hydration to avoid server/client mismatch
  const authed = mounted && isAuthenticated;

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/analyze", label: "Analyze" },
    ...(authed
      ? [{ href: "/dashboard", label: "Dashboard" }]
      : []),
    ...(authed && user?.role === "admin"
      ? [{ href: "/admin", label: "Admin" }]
      : []),
  ];

  return (
    <nav className="fixed top-0 z-50 w-full border-b border-white/10 bg-dark-950/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-primary to-brand-secondary">
            <Shield className="h-5 w-5 text-white" />
          </div>
          <span className="font-heading text-xl font-bold">
            <span className="gradient-text">Veri</span>
            <span className="text-white">Truth</span>
          </span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden items-center gap-8 md:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`text-sm font-medium transition-colors ${
                pathname === link.href
                  ? "text-brand-primary"
                  : "text-dark-200 hover:text-white"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Right side */}
        <div className="hidden items-center gap-4 md:flex">
          {!mounted ? (
            // Placeholder matching server render during hydration
            <div className="h-9 w-28" />
          ) : authed ? (
            <>
              <Link
                href="/dashboard"
                className="flex items-center gap-2 text-sm text-dark-200 hover:text-white"
              >
                <User className="h-4 w-4" />
                {user?.first_name}
              </Link>
              <button onClick={handleLogout} className="btn-secondary !py-2 !px-4 text-sm">
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="btn-secondary !py-2 !px-4 text-sm">
                <LogIn className="mr-2 h-4 w-4" />
                Login
              </Link>
              <Link href="/signup" className="btn-primary !py-2 !px-4 text-sm">
                <UserPlus className="mr-2 h-4 w-4" />
                Sign Up
              </Link>
            </>
          )}
        </div>

        {/* Mobile toggle */}
        <button
          className="md:hidden text-white"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-white/10 bg-dark-900 md:hidden"
          >
            <div className="flex flex-col gap-2 px-6 py-4">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className={`rounded-lg px-4 py-2 text-sm font-medium ${
                    pathname === link.href
                      ? "bg-brand-primary/10 text-brand-primary"
                      : "text-dark-200 hover:bg-white/5"
                  }`}
                >
                  {link.label}
                </Link>
              ))}
              <hr className="border-white/10" />
              {authed ? (
                <button
                  onClick={() => {
                    handleLogout();
                    setMobileOpen(false);
                  }}
                  className="rounded-lg px-4 py-2 text-left text-sm text-brand-danger hover:bg-white/5"
                >
                  Logout
                </button>
              ) : (
                <>
                  <Link
                    href="/login"
                    onClick={() => setMobileOpen(false)}
                    className="rounded-lg px-4 py-2 text-sm text-dark-200 hover:bg-white/5"
                  >
                    Login
                  </Link>
                  <Link
                    href="/signup"
                    onClick={() => setMobileOpen(false)}
                    className="rounded-lg bg-brand-primary/10 px-4 py-2 text-sm text-brand-primary"
                  >
                    Sign Up
                  </Link>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
