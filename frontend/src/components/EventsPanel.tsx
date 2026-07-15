"use client";

import { useAlertStore } from "@/store/useAlertStore";

export function EventsPanel() {
  const events = useAlertStore((s) => s.events);
  const eventsLiveConnected = useAlertStore((s) => s.eventsLiveConnected);

  return (
    <section className="rounded-xl border border-safety-border bg-safety-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Recent Events</h2>
        <span
          className={`rounded-full px-2 py-0.5 text-xs ${
            eventsLiveConnected ? "bg-safety-ok/20 text-safety-ok" : "bg-gray-700 text-gray-400"
          }`}
        >
          {eventsLiveConnected ? "Live updates" : "Reconnecting…"}
        </span>
      </div>
      <ul className="max-h-[320px] space-y-2 overflow-y-auto text-sm">
        {events.length === 0 && (
          <li className="text-gray-400">Processed video chunks will appear here.</li>
        )}
        {events.map((ev) => (
          <li
            key={ev.id}
            className="rounded border border-safety-border px-3 py-2"
          >
            <div className="flex justify-between">
              <span>{ev.action_label ?? ev.event_type}</span>
              <span className="text-xs text-gray-400">
                {new Date(ev.occurred_at).toLocaleTimeString()}
              </span>
            </div>
            <p className="text-xs text-gray-500">
              Risk: {ev.risk_level ?? "n/a"} · Camera: {ev.camera_id?.slice(0, 8) ?? "—"}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
