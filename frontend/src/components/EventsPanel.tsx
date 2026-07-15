"use client";

import { useState } from "react";
import { useAlertStore } from "@/store/useAlertStore";

function severityFromMetadata(metadata: Record<string, unknown>): string | null {
  const report = metadata.severity_report as { overall_level?: string } | undefined;
  return report?.overall_level ?? null;
}

function forensicFromMetadata(metadata: Record<string, unknown>): string | null {
  const report = metadata.forensic_report;
  return typeof report === "string" ? report : null;
}

export function EventsPanel() {
  const events = useAlertStore((s) => s.events);
  const eventsLiveConnected = useAlertStore((s) => s.eventsLiveConnected);
  const [expandedId, setExpandedId] = useState<string | null>(null);

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
        {events.map((ev) => {
          const severity = severityFromMetadata(ev.metadata);
          const forensic = forensicFromMetadata(ev.metadata);
          const expanded = expandedId === ev.id;
          return (
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
                Severity: {severity ?? ev.risk_level ?? "n/a"} · Camera:{" "}
                {ev.camera_id?.slice(0, 8) ?? "—"}
              </p>
              {forensic && (
                <>
                  <button
                    onClick={() => setExpandedId(expanded ? null : ev.id)}
                    className="mt-1 text-xs text-safety-accent hover:underline"
                  >
                    {expanded ? "Hide analysis" : "View Gemini analysis"}
                  </button>
                  {expanded && (
                    <p className="mt-2 whitespace-pre-wrap text-xs text-gray-400">
                      {forensic}
                    </p>
                  )}
                </>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
