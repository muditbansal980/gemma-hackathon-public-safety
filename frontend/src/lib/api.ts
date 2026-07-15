const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export type Camera = {
  id: string;
  name: string;
  location: string;
  zone: string | null;
  rtsp_url: string | null;
  is_active: boolean;
};

export type Alert = {
  id: string;
  camera_id: string;
  risk_level: "low" | "medium" | "high";
  action_type: string;
  title: string;
  description: string | null;
  status: "pending" | "confirmed" | "dismissed";
  created_at: string;
};

export type EventItem = {
  id: string;
  camera_id: string | null;
  event_type: string;
  action_label: string | null;
  risk_level: string | null;
  occurred_at: string;
  metadata: Record<string, unknown>;
};

export type Detection = {
  track_id: number | null;
  label: string;
  confidence: number;
  bbox: [number, number, number, number];
  is_threat: boolean;
};

export type PreviewFrame = {
  type: "frame";
  camera_id: string;
  image: string;
  detections: Detection[];
  timestamp: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new Error(
      `Backend unreachable at ${API_BASE}. Start FastAPI on port 8000.`
    );
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

export const api = {
  healthCheck: () =>
    request<{ status: string; database: string }>("/health"),
  listCameras: () => request<Camera[]>("/api/v1/cameras/"),
  createCamera: (body: {
    name: string;
    location: string;
    zone?: string;
    rtsp_url?: string;
  }) => request<Camera>("/api/v1/cameras/", { method: "POST", body: JSON.stringify(body) }),
  startRecording: (cameraId: string, source = "webcam") =>
    request<{ is_recording: boolean; message: string }>(
      `/api/v1/recording/${cameraId}/start`,
      { method: "POST", body: JSON.stringify({ source }) }
    ),
  stopRecording: (cameraId: string) =>
    request<{ is_recording: boolean; message: string }>(
      `/api/v1/recording/${cameraId}/stop`,
      { method: "POST" }
    ),
  recordingStatus: (cameraId: string) =>
    request<{ is_recording: boolean; message: string }>(
      `/api/v1/recording/${cameraId}/status`
    ),
  listActiveRecordings: () =>
    request<{ camera_ids: string[] }>("/api/v1/recording/active"),
  listAlerts: () => request<Alert[]>("/api/v1/alerts/"),
  listEvents: () => request<EventItem[]>("/api/v1/events/"),
  updateAlertStatus: (alertId: string, status: Alert["status"]) =>
    request<Alert>(`/api/v1/alerts/${alertId}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
};

export function alertsWebSocketUrl(): string {
  return `${WS_BASE}/ws/alerts`;
}

export function eventsWebSocketUrl(): string {
  return `${WS_BASE}/ws/events`;
}

export function previewWebSocketUrl(cameraId: string): string {
  return `${WS_BASE}/ws/preview/${cameraId}`;
}
