"use client";

import React, { useState, useRef } from "react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { useAnalysisStore } from "@/store/analysis-store";
import {
  FileText,
  Globe,
  Upload,
  Send,
  Loader2,
  AlertCircle,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getErrorMessage } from "@/lib/api";

type InputMode = "text" | "url" | "file";

interface InputPanelProps {
  onSubmit: (analysisId: string) => void;
}

export function AnalysisInputPanel({ onSubmit }: InputPanelProps) {
  const [mode, setMode] = useState<InputMode>("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const { submitText, submitUrl, submitFile, isSubmitting } = useAnalysisStore();

  const handleSubmit = async () => {
    try {
      let id: string;
      if (mode === "text") {
        if (text.trim().length < 50) {
          toast.error("Please enter at least 50 characters of text.");
          return;
        }
        id = await submitText(text);
      } else if (mode === "url") {
        if (!url.startsWith("http")) {
          toast.error("Please enter a valid URL starting with http:// or https://");
          return;
        }
        id = await submitUrl(url);
      } else {
        if (!file) {
          toast.error("Please select a file to upload.");
          return;
        }
        id = await submitFile(file);
      }
      onSubmit(id);
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Failed to submit analysis"));
    }
  };

  const tabs = [
    { key: "text" as const, label: "Paste Text", icon: FileText },
    { key: "url" as const, label: "Enter URL", icon: Globe },
    { key: "file" as const, label: "Upload File", icon: Upload },
  ];

  return (
    <div className="mx-auto max-w-4xl">
      <div className="text-center">
        <h1 className="font-heading text-4xl font-bold text-white">
          Analyze <span className="gradient-text">Content</span>
        </h1>
        <p className="mt-3 text-dark-300">
          Submit an article, URL, or document to detect misinformation through
          7 AI-powered analysis layers.
        </p>
      </div>

      <div className="glass-card mt-8">
        {/* Tabs */}
        <div className="flex gap-2 rounded-xl bg-dark-800 p-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setMode(tab.key)}
              className={cn(
                "flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-all",
                mode === tab.key
                  ? "bg-gradient-to-r from-brand-primary to-brand-secondary text-white shadow-glow"
                  : "text-dark-300 hover:text-white"
              )}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Input Area */}
        <div className="mt-6">
          {mode === "text" && (
            <div>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste the article text here for analysis…"
                className="input-field min-h-[250px] resize-y font-mono text-sm"
                maxLength={50000}
              />
              <div className="mt-2 flex items-center justify-between text-xs text-dark-400">
                <span>Minimum 50 characters required</span>
                <span>{text.length.toLocaleString()} / 50,000</span>
              </div>
            </div>
          )}

          {mode === "url" && (
            <div>
              <div className="relative">
                <Globe className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-dark-400" />
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/article-to-analyze"
                  className="input-field pl-12"
                />
              </div>
              <p className="mt-2 text-xs text-dark-400">
                Enter the full URL of the news article you want to verify.
              </p>
            </div>
          )}

          {mode === "file" && (
            <div>
              <input
                ref={fileRef}
                type="file"
                accept=".pdf,.txt,.doc,.docx"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="hidden"
              />
              <button
                onClick={() => fileRef.current?.click()}
                className="flex w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-white/10 bg-white/5 px-6 py-16 transition-colors hover:border-brand-primary/30"
              >
                <Upload className="h-10 w-10 text-dark-400" />
                <p className="mt-4 text-sm text-dark-200">
                  Click to upload or drag & drop
                </p>
                <p className="mt-1 text-xs text-dark-400">
                  PDF, TXT, DOC, DOCX — Max 10MB
                </p>
              </button>
              {file && (
                <div className="mt-4 flex items-center justify-between rounded-lg bg-dark-800 px-4 py-3">
                  <div className="flex items-center gap-3 text-sm text-white">
                    <FileText className="h-4 w-4 text-brand-primary" />
                    {file.name}
                    <span className="text-dark-400">
                      ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </span>
                  </div>
                  <button onClick={() => setFile(null)} className="text-dark-400 hover:text-white">
                    <X className="h-4 w-4" />
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Submit */}
        <div className="mt-6">
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="btn-primary w-full text-lg"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Submitting…
              </>
            ) : (
              <>
                <Send className="mr-2 h-5 w-5" />
                Analyze Now
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
