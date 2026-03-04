"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { useAuthStore } from "@/store/auth-store";
import { getErrorMessage } from "@/lib/api";
import {
  Shield,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Loader2,
  ArrowRight,
  User,
  Building2,
} from "lucide-react";
import type { UserRole } from "@/lib/types";

const roles: { value: UserRole; label: string }[] = [
  { value: "student", label: "Student" },
  { value: "educator", label: "Educator" },
  { value: "researcher", label: "Researcher" },
  { value: "journalist", label: "Journalist" },
];

export default function SignupPage() {
  const router = useRouter();
  const { signup, isLoading } = useAuthStore();

  const [form, setForm] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    first_name: "",
    last_name: "",
    role: "student" as UserRole,
    institution: "",
  });
  const [showPw, setShowPw] = useState(false);

  const update = (key: string, val: string) =>
    setForm((f) => ({ ...f, [key]: val }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (form.password.length < 12) {
      toast.error("Password must be at least 12 characters");
      return;
    }
    if (form.password !== form.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    try {
      await signup({
        email: form.email,
        password: form.password,
        first_name: form.first_name,
        last_name: form.last_name,
        role: form.role,
        institution: form.institution || undefined,
      });
      toast.success("Account created! Welcome to VeriTruth AI.");
      router.push("/dashboard");
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Signup failed"));
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-dark-950 px-6 py-12">
      {/* Background effects */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/4 top-1/4 h-80 w-80 rounded-full bg-brand-secondary/10 blur-[100px]" />
        <div className="absolute right-1/4 bottom-1/4 h-80 w-80 rounded-full bg-brand-primary/10 blur-[100px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative w-full max-w-md"
      >
        {/* Logo */}
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-brand-primary to-brand-secondary shadow-glow">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <span className="font-heading text-2xl font-bold">
              <span className="gradient-text">Veri</span>
              <span className="text-white">Truth</span>
            </span>
          </Link>
        </div>

        <div className="glass-card">
          <h1 className="text-center font-heading text-2xl font-bold text-white">
            Create Account
          </h1>
          <p className="mt-2 text-center text-sm text-dark-300">
            Join VeriTruth AI and start detecting misinformation
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            {/* Name row */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-dark-200">
                  First Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-400" />
                  <input
                    value={form.first_name}
                    onChange={(e) => update("first_name", e.target.value)}
                    placeholder="John"
                    required
                    className="input-field pl-10 !py-2.5 text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-dark-200">
                  Last Name
                </label>
                <input
                  value={form.last_name}
                  onChange={(e) => update("last_name", e.target.value)}
                  placeholder="Doe"
                  required
                  className="input-field !py-2.5 text-sm"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="mb-1 block text-xs font-medium text-dark-200">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-400" />
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => update("email", e.target.value)}
                  placeholder="you@university.edu"
                  required
                  className="input-field pl-10 !py-2.5 text-sm"
                />
              </div>
            </div>

            {/* Role */}
            <div>
              <label className="mb-1 block text-xs font-medium text-dark-200">
                I am a…
              </label>
              <div className="grid grid-cols-4 gap-2">
                {roles.map((r) => (
                  <button
                    key={r.value}
                    type="button"
                    onClick={() => update("role", r.value)}
                    className={`rounded-lg px-3 py-2 text-xs font-medium transition-all ${
                      form.role === r.value
                        ? "bg-brand-primary/20 text-brand-primary border border-brand-primary/30"
                        : "bg-dark-800 text-dark-300 border border-transparent hover:border-white/10"
                    }`}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Institution */}
            <div>
              <label className="mb-1 block text-xs font-medium text-dark-200">
                Institution (optional)
              </label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-400" />
                <input
                  value={form.institution}
                  onChange={(e) => update("institution", e.target.value)}
                  placeholder="University of …"
                  className="input-field pl-10 !py-2.5 text-sm"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="mb-1 block text-xs font-medium text-dark-200">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-400" />
                <input
                  type={showPw ? "text" : "password"}
                  value={form.password}
                  onChange={(e) => update("password", e.target.value)}
                  placeholder="Min 8 characters"
                  required
                  minLength={8}
                  className="input-field pl-10 pr-10 !py-2.5 text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400 hover:text-white"
                >
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="mb-1 block text-xs font-medium text-dark-200">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-400" />
                <input
                  type="password"
                  value={form.confirmPassword}
                  onChange={(e) => update("confirmPassword", e.target.value)}
                  placeholder="Re-enter password"
                  required
                  className="input-field pl-10 !py-2.5 text-sm"
                />
              </div>
            </div>

            {/* Terms */}
            <label className="flex items-start gap-2 text-xs text-dark-300">
              <input
                type="checkbox"
                required
                className="mt-0.5 h-4 w-4 rounded border-dark-600 bg-dark-800"
              />
              <span>
                I agree to the{" "}
                <a href="#" className="text-brand-primary hover:underline">
                  Terms of Service
                </a>{" "}
                and{" "}
                <a href="#" className="text-brand-primary hover:underline">
                  Privacy Policy
                </a>
              </span>
            </label>

            {/* Submit */}
            <button type="submit" disabled={isLoading} className="btn-primary w-full">
              {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Create Account
              <ArrowRight className="ml-2 h-4 w-4" />
            </button>
          </form>

          {/* Login link */}
          <p className="mt-6 text-center text-sm text-dark-300">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-brand-primary hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
