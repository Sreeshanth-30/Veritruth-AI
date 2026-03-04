/* ──────────────────────────────────────────────────────────── */
/*  VeriTruth AI — WebSocket Hook for Real-Time Progress       */
/* ──────────────────────────────────────────────────────────── */
import { useEffect, useRef, useCallback } from "react";
import type { AnalysisProgress } from "@/lib/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1";

export function useAnalysisWebSocket(
  analysisId: string | null,
  onProgress: (progress: AnalysisProgress) => void,
  onComplete?: () => void
) {
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!analysisId) return;

    const ws = new WebSocket(`${WS_URL}/ws/analysis/${analysisId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`[WS] Connected to analysis ${analysisId}`);
    };

    ws.onmessage = (event) => {
      try {
        const data: AnalysisProgress = JSON.parse(event.data);
        onProgress(data);
        if (data.stage === "done" && onComplete) {
          onComplete();
        }
      } catch (err) {
        console.error("[WS] Parse error:", err);
      }
    };

    ws.onerror = (err) => {
      console.error("[WS] Error:", err);
    };

    ws.onclose = () => {
      console.log("[WS] Disconnected");
    };

    return ws;
  }, [analysisId, onProgress, onComplete]);

  useEffect(() => {
    const ws = connect();
    return () => {
      ws?.close();
    };
  }, [connect]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  return { disconnect };
}
