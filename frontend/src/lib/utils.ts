import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));
}

export function formatPercentage(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function getRiskColor(risk: string): string {
  switch (risk?.toUpperCase()) {
    case "LOW":
      return "text-brand-accent";
    case "MEDIUM":
      return "text-brand-warning";
    case "HIGH":
      return "text-orange-400";
    case "CRITICAL":
      return "text-brand-danger";
    default:
      return "text-dark-300";
  }
}

export function getRiskBgColor(risk: string): string {
  switch (risk?.toUpperCase()) {
    case "LOW":
      return "bg-brand-accent/20";
    case "MEDIUM":
      return "bg-brand-warning/20";
    case "HIGH":
      return "bg-orange-500/20";
    case "CRITICAL":
      return "bg-brand-danger/20";
    default:
      return "bg-dark-600/20";
  }
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + "…";
}

export function getScoreLabel(score: number): string {
  if (score >= 0.8) return "Very High";
  if (score >= 0.6) return "High";
  if (score >= 0.4) return "Moderate";
  if (score >= 0.2) return "Low";
  return "Very Low";
}
