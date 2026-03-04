"use client";

import React from "react";
import { Sidebar } from "@/components/layout/sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-dark-950">
      <Sidebar />
      <main className="ml-64 min-h-screen p-8 transition-all duration-300">
        {children}
      </main>
    </div>
  );
}
