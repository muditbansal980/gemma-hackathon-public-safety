"use client";

import { useEffect, useState } from "react";
import { previewWebSocketUrl, type Detection, type PreviewFrame } from "@/lib/api";

export function usePreviewSocket(cameraId: string | null, enabled: boolean) {
  const [frame, setFrame] = useState<PreviewFrame | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!cameraId || !enabled) {
      setFrame(null);
      setConnected(false);
      return;
    }

    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      ws = new WebSocket(previewWebSocketUrl(cameraId));

      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        retryTimer = setTimeout(connect, 2000);
      };
      ws.onerror = () => ws?.close();
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as PreviewFrame;
          if (payload.type === "frame") {
            setFrame(payload);
          }
        } catch {
          /* ignore malformed payloads */
        }
      };
    };

    connect();
    return () => {
      clearTimeout(retryTimer);
      ws?.close();
      setConnected(false);
    };
  }, [cameraId, enabled]);

  return { frame, connected, detections: (frame?.detections ?? []) as Detection[] };
}
