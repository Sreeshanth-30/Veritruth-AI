"use client";

import React from "react";
import Link from "next/link";
import { Shield, Github, Twitter, Mail } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-white/10 bg-dark-950">
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="grid gap-12 md:grid-cols-4">
          {/* Brand */}
          <div className="md:col-span-1">
            <Link href="/" className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-primary to-brand-secondary">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <span className="font-heading text-xl font-bold text-white">
                VeriTruth AI
              </span>
            </Link>
            <p className="mt-4 text-sm text-dark-300">
              Multi-layer AI fake news intelligence system designed for
              students, educators, and researchers.
            </p>
            <div className="mt-6 flex gap-4">
              <a href="#" className="text-dark-400 hover:text-brand-primary transition-colors">
                <Github className="h-5 w-5" />
              </a>
              <a href="#" className="text-dark-400 hover:text-brand-primary transition-colors">
                <Twitter className="h-5 w-5" />
              </a>
              <a href="#" className="text-dark-400 hover:text-brand-primary transition-colors">
                <Mail className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Product */}
          <div>
            <h3 className="font-heading text-sm font-semibold uppercase tracking-wider text-white">
              Product
            </h3>
            <ul className="mt-4 space-y-3">
              {["Features", "How It Works", "API Docs", "Browser Extension"].map(
                (item) => (
                  <li key={item}>
                    <a href="#" className="text-sm text-dark-300 hover:text-brand-primary transition-colors">
                      {item}
                    </a>
                  </li>
                )
              )}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="font-heading text-sm font-semibold uppercase tracking-wider text-white">
              Resources
            </h3>
            <ul className="mt-4 space-y-3">
              {[
                "Documentation",
                "Media Literacy Guide",
                "Research Papers",
                "Blog",
              ].map((item) => (
                <li key={item}>
                  <a href="#" className="text-sm text-dark-300 hover:text-brand-primary transition-colors">
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="font-heading text-sm font-semibold uppercase tracking-wider text-white">
              Legal
            </h3>
            <ul className="mt-4 space-y-3">
              {["Privacy Policy", "Terms of Service", "Cookie Policy"].map(
                (item) => (
                  <li key={item}>
                    <a href="#" className="text-sm text-dark-300 hover:text-brand-primary transition-colors">
                      {item}
                    </a>
                  </li>
                )
              )}
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-white/10 pt-8 md:flex-row">
          <p className="text-sm text-dark-400">
            &copy; {new Date().getFullYear()} VeriTruth AI. All rights reserved.
          </p>
          <p className="text-sm text-dark-500">
            🛡️ Empowering truth through artificial intelligence
          </p>
        </div>
      </div>
    </footer>
  );
}
