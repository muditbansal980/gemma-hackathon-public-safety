"use client";

import { useEffect } from "react";
import { eventsWebSocketUrl, type EventItem } from "@/lib/api";
import { useAlertStore } from "@/store/useAlertStore";

export function useEventSocket() {
  const prependEvent = useAlertStore((s) => s.prependEvent);
  const setEventsLiveConnected = useAlertStore((s) => s.setEventsLiveConnected);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      ws = new WebSocket(eventsWebSocketUrl());

      ws.onopen = () => setEventsLiveConnected(true);
      ws.onclose = () => {
        setEventsLiveConnected(false);
        retryTimer = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws?.close();
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as EventItem;
          prependEvent(payload);
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
  }, [prependEvent, setEventsLiveConnected]);
}
