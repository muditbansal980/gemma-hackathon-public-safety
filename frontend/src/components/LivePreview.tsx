"use client";

import { useEffect, useRef, useState } from "react";
import type { Detection } from "@/lib/api";
import { usePreviewSocket } from "@/hooks/usePreviewSocket";

type Props = {
  cameraId: string;
};

function DetectionChips({ detections }: { detections: Detection[] }) {
  if (detections.length === 0) {
    return <p className="text-xs text-gray-500">No objects detected in current frame.</p>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {detections.map((d, i) => (
        <span
          key={`${d.label}-${d.track_id ?? i}`}
          className={`rounded-full px-2 py-0.5 text-xs ${
            d.is_threat
              ? "bg-safety-danger/20 text-safety-danger"
              : "bg-gray-700 text-gray-300"
          }`}
        >
          {d.label}
          {d.track_id != null ? ` #${d.track_id}` : ""} · {Math.round(d.confidence * 100)}%
        </span>
      ))}
    </div>
  );
}

export function LivePreview({ cameraId }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [rawAvailable, setRawAvailable] = useState(true);
  const [rawError, setRawError] = useState<string | null>(null);
  const { frame, connected, detections } = usePreviewSocket(cameraId, true);

  useEffect(() => {
    let cancelled = false;

    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user" },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        setRawAvailable(true);
        setRawError(null);
      } catch (err) {
        setRawAvailable(false);
        setRawError(
          err instanceof Error
            ? err.message
            : "Camera unavailable — showing backend annotated stream only."
        );
      }
    }

    startCamera();
    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, [cameraId]);

  const annotatedSrc = frame ? `data:image/jpeg;base64,${frame.image}` : null;

  return (
    <div className="mt-4 rounded-lg border border-safety-border p-3">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-sm font-medium">Live preview</p>
        <span
          className={`rounded-full px-2 py-0.5 text-xs ${
            connected ? "bg-safety-ok/20 text-safety-ok" : "bg-gray-700 text-gray-400"
          }`}
        >
          {connected ? "YOLO stream connected" : "Waiting for annotated frames…"}
        </span>
      </div>

      <div
        className={`grid gap-3 ${
          rawAvailable ? "md:grid-cols-2" : "grid-cols-1"
        }`}
      >
        {rawAvailable && (
          <div>
            <p className="mb-1 text-xs text-gray-400">Browser mirror</p>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="aspect-video w-full rounded-lg bg-black object-cover"
            />
          </div>
        )}

        <div>
          <p className="mb-1 text-xs text-gray-400">YOLO annotated (backend)</p>
          {annotatedSrc ? (
            <img
              src={annotatedSrc}
              alt="Annotated live preview"
              className="aspect-video w-full rounded-lg bg-black object-cover"
            />
          ) : (
            <div className="flex aspect-video w-full items-center justify-center rounded-lg bg-black text-xs text-gray-500">
              Waiting for backend frames…
            </div>
          )}
        </div>
      </div>

      {!rawAvailable && rawError && (
        <p className="mt-2 text-xs text-safety-warn">{rawError}</p>
      )}

      <div className="mt-3">
        <p className="mb-1 text-xs text-gray-400">Detected objects</p>
        <DetectionChips detections={detections} />
      </div>
    </div>
  );
}
