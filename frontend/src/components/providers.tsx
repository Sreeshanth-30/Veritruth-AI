"use client";

import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      refetchOnWindowFocus: false,
      retry: 2,
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: "#1e1e3a",
            color: "#d1d1e0",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "12px",
          },
          success: {
            iconTheme: { primary: "#00e5a0", secondary: "#1e1e3a" },
          },
          error: {
            iconTheme: { primary: "#ff3a5c", secondary: "#1e1e3a" },
          },
        }}
      />
    </QueryClientProvider>
  );
}
