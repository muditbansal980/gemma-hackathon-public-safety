"use client";

import { useEffect } from "react";
import { alertsWebSocketUrl, type Alert } from "@/lib/api";
import { useAlertStore } from "@/store/useAlertStore";

export function useAlertSocket() {
  const prependAlert = useAlertStore((s) => s.prependAlert);
  const setLiveConnected = useAlertStore((s) => s.setLiveConnected);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      ws = new WebSocket(alertsWebSocketUrl());

      ws.onopen = () => setLiveConnected(true);
      ws.onclose = () => {
        setLiveConnected(false);
        retryTimer = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws?.close();
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as Alert;
          prependAlert(payload);
        } catch {
          /* ignore malformed payloads */
        }
      };
    };

    connect();
    return () => {
      clearTimeout(retryTimer);
      ws?.close();
    };
  }, [prependAlert, setLiveConnected]);
}
