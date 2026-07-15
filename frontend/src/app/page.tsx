"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AlertPanel } from "@/components/AlertPanel";
import { CameraPanel } from "@/components/CameraPanel";
import { EventsPanel } from "@/components/EventsPanel";
import { useAlertSocket } from "@/hooks/useAlertSocket";
import { useEventSocket } from "@/hooks/useEventSocket";
import { useAlertStore } from "@/store/useAlertStore";

export default function DashboardPage() {
  useAlertSocket();
  useEventSocket();
  const setAlerts = useAlertStore((s) => s.setAlerts);
  const setCameras = useAlertStore((s) => s.setCameras);
  const setEvents = useAlertStore((s) => s.setEvents);
  const [backendOnline, setBackendOnline] = useState(true);
  const [backendError, setBackendError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      await api.healthCheck();
      setBackendOnline(true);
      setBackendError(null);
      const [alerts, cameras, events] = await Promise.all([
        api.listAlerts(),
        api.listCameras(),
        api.listEvents(),
      ]);
      setAlerts(alerts);
      setCameras(cameras);
      setEvents(events);
    } catch (err) {
      setBackendOnline(false);
      setBackendError(
        err instanceof Error ? err.message : "Backend unreachable"
      );
    }
  }, [setAlerts, setCameras, setEvents]);

  useEffect(() => {
    load();
    const timer = setInterval(load, 15000);
    return () => clearInterval(timer);
  }, [load]);

  return (
    <main className="min-h-screen p-6">
      {!backendOnline && (
        <div className="mb-4 rounded-lg border border-safety-danger/50 bg-safety-danger/10 px-4 py-3 text-sm text-safety-danger">
          <p className="font-medium">Backend offline</p>
          <p className="mt-1 text-xs opacity-90">
            {backendError ?? "Start FastAPI on port 8000 and ensure Docker (Postgres + Redis) is running."}
          </p>
        </div>
      )}
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight">Public Safety Monitor</h1>
        <p className="text-sm text-gray-400">
          Webcam/RTSP → 1-min chunks → Redis worker → YOLO + Gemini → alerts
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <CameraPanel />
        <AlertPanel />
        <div className="lg:col-span-2">
          <EventsPanel />
        </div>
      </div>
    </main>
  );
}
