"use client";

import { api, type Alert } from "@/lib/api";
import { useAlertStore } from "@/store/useAlertStore";

const riskColors: Record<Alert["risk_level"], string> = {
  low: "text-safety-ok",
  medium: "text-safety-warn",
  high: "text-safety-danger",
};

export function AlertPanel() {
  const alerts = useAlertStore((s) => s.alerts);
  const liveConnected = useAlertStore((s) => s.liveConnected);
  const updateAlert = useAlertStore((s) => s.updateAlert);

  async function setStatus(alert: Alert, status: Alert["status"]) {
    const updated = await api.updateAlertStatus(alert.id, status);
    updateAlert(updated);
  }

  return (
    <section className="rounded-xl border border-safety-border bg-safety-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Live Alerts</h2>
        <span
          className={`rounded-full px-2 py-0.5 text-xs ${
            liveConnected ? "bg-safety-ok/20 text-safety-ok" : "bg-gray-700 text-gray-400"
          }`}
        >
          {liveConnected ? "WebSocket connected" : "Reconnecting…"}
        </span>
      </div>

      <ul className="max-h-[420px] space-y-3 overflow-y-auto">
        {alerts.length === 0 && (
          <li className="text-sm text-gray-400">No alerts yet. Start recording to process video.</li>
        )}
        {alerts.map((alert) => (
          <li
            key={alert.id}
            className="rounded-lg border border-safety-border p-4"
          >
            <div className="mb-1 flex items-center justify-between gap-2">
              <p className="font-medium">{alert.title}</p>
              <span className={`text-xs uppercase ${riskColors[alert.risk_level]}`}>
                {alert.risk_level}
              </span>
            </div>
            <p className="mb-2 line-clamp-3 text-xs text-gray-400">
              {alert.description ?? "No description"}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setStatus(alert, "confirmed")}
                className="rounded bg-safety-ok/20 px-2 py-1 text-xs text-safety-ok"
              >
                Confirm
              </button>
              <button
                onClick={() => setStatus(alert, "dismissed")}
                className="rounded bg-gray-700 px-2 py-1 text-xs"
              >
                Dismiss
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
