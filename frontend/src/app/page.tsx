"use client";

import { useCallback, useEffect } from "react";
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

  const load = useCallback(async () => {
    const [alerts, cameras, events] = await Promise.all([
      api.listAlerts(),
      api.listCameras(),
      api.listEvents(),
    ]);
    setAlerts(alerts);
    setCameras(cameras);
    setEvents(events);
  }, [setAlerts, setCameras, setEvents]);

  useEffect(() => {
    load().catch(console.error);
  }, [load]);

  return (
    <main className="min-h-screen p-6">
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight">Public Safety Monitor</h1>
        <p className="text-sm text-gray-400">
          Webcam/RTSP → 1-min chunks → Redis worker → YOLO + Gemma → alerts
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
