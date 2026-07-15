"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { LivePreview } from "@/components/LivePreview";
import { useAlertStore } from "@/store/useAlertStore";

export function CameraPanel() {
  const cameras = useAlertStore((s) => s.cameras);
  const setCameras = useAlertStore((s) => s.setCameras);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [recording, setRecording] = useState<Record<string, boolean>>({});
  const [newName, setNewName] = useState("Laptop Webcam");
  const [newLocation, setNewLocation] = useState("Dev Lab");
  const [source, setSource] = useState("webcam");
  const [error, setError] = useState<string | null>(null);

  const activeRecordingId =
    Object.entries(recording).find(([, isOn]) => isOn)?.[0] ?? null;

  const syncRecordingState = useCallback(async () => {
    try {
      const { camera_ids } = await api.listActiveRecordings();
      const active = Object.fromEntries(camera_ids.map((id) => [id, true]));
      setRecording(active);
    } catch {
      /* backend may be offline on first paint */
    }
  }, []);

  async function refreshCameras() {
    try {
      setError(null);
      const list = await api.listCameras();
      setCameras(list);
      await syncRecordingState();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load cameras");
    }
  }

  useEffect(() => {
    refreshCameras().catch(console.error);
    const timer = setInterval(() => {
      syncRecordingState().catch(console.error);
    }, 10000);
    return () => clearInterval(timer);
  }, [syncRecordingState]);

  async function createCamera() {
    try {
      setError(null);
      await api.createCamera({
        name: newName,
        location: newLocation,
        zone: "Restricted_Zone_Alpha",
        rtsp_url: source === "webcam" ? "webcam" : source,
      });
      await refreshCameras();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to register camera");
    }
  }

  async function toggleRecording(cameraId: string, cameraSource: string | null) {
    setBusyId(cameraId);
    try {
      setError(null);
      if (recording[cameraId]) {
        await api.stopRecording(cameraId);
        setRecording((r) => ({ ...r, [cameraId]: false }));
      } else {
        const resolvedSource =
          cameraSource && cameraSource !== "webcam" ? cameraSource : source;
        await api.startRecording(cameraId, resolvedSource);
        setRecording((r) => ({ ...r, [cameraId]: true }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Recording request failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="rounded-xl border border-safety-border bg-safety-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Cameras</h2>
        <button
          onClick={() => refreshCameras().catch(console.error)}
          className="rounded-lg bg-safety-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-600"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-safety-danger/40 bg-safety-danger/10 px-3 py-2 text-xs text-safety-danger">
          {error}
        </div>
      )}

      <div className="mb-4 grid gap-2 rounded-lg border border-safety-border p-3 text-sm">
        <input
          className="rounded bg-safety-bg px-3 py-2"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Camera name"
        />
        <input
          className="rounded bg-safety-bg px-3 py-2"
          value={newLocation}
          onChange={(e) => setNewLocation(e.target.value)}
          placeholder="Location"
        />
        <input
          className="rounded bg-safety-bg px-3 py-2"
          value={source}
          onChange={(e) => setSource(e.target.value)}
          placeholder='Source: "webcam" or RTSP URL'
        />
        <button
          onClick={() => createCamera().catch(console.error)}
          className="rounded-lg border border-safety-border px-3 py-2 hover:bg-safety-bg"
        >
          Register camera
        </button>
      </div>

      <ul className="space-y-3">
        {cameras.length === 0 && (
          <li className="text-sm text-gray-400">No cameras registered yet.</li>
        )}
        {cameras.map((cam) => (
          <li
            key={cam.id}
            className="flex items-center justify-between rounded-lg border border-safety-border px-4 py-3"
          >
            <div>
              <p className="font-medium">{cam.name}</p>
              <p className="text-xs text-gray-400">
                {cam.location} · {cam.rtsp_url ?? "webcam"}
                {recording[cam.id] && (
                  <span className="ml-2 text-safety-danger">● Recording</span>
                )}
              </p>
            </div>
            <button
              disabled={busyId === cam.id}
              onClick={() => toggleRecording(cam.id, cam.rtsp_url).catch(console.error)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                recording[cam.id]
                  ? "bg-safety-danger text-white"
                  : "bg-safety-ok text-white"
              }`}
            >
              {recording[cam.id] ? "Stop" : "Record"}
            </button>
          </li>
        ))}
      </ul>

      {activeRecordingId && <LivePreview cameraId={activeRecordingId} />}
    </section>
  );
}
