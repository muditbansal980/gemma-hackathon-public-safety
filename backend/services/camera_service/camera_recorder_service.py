import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2

from backend.core.config import settings
from backend.services.redis_service.redis_service import enqueue_video_job

logger = logging.getLogger(__name__)


class CameraRecorderService:
    """Records webcam or RTSP streams in fixed-duration chunks and enqueues them."""

    def __init__(self) -> None:
        self._threads: dict[str, threading.Thread] = {}
        self._stop_flags: dict[str, threading.Event] = {}

    def is_recording(self, camera_id: str) -> bool:
        thread = self._threads.get(camera_id)
        return thread is not None and thread.is_alive()

    def list_active_recordings(self) -> list[str]:
        return [camera_id for camera_id, thread in self._threads.items() if thread.is_alive()]

    def start_recording(
        self,
        camera_id: str,
        source: str | int,
        *,
        chunk_seconds: int | None = None,
    ) -> None:
        if self.is_recording(camera_id):
            raise RuntimeError(f"Camera {camera_id} is already recording")

        stop_event = threading.Event()
        self._stop_flags[camera_id] = stop_event

        thread = threading.Thread(
            target=self._record_loop,
            args=(camera_id, source, chunk_seconds or settings.chunk_duration_seconds, stop_event),
            daemon=True,
            name=f"recorder-{camera_id}",
        )
        self._threads[camera_id] = thread
        thread.start()
        logger.info("Started recording for camera %s from source %s", camera_id, source)

    def stop_recording(self, camera_id: str) -> None:
        stop_event = self._stop_flags.get(camera_id)
        if stop_event:
            stop_event.set()
        thread = self._threads.get(camera_id)
        if thread and thread.is_alive():
            thread.join(timeout=5)
        self._threads.pop(camera_id, None)
        self._stop_flags.pop(camera_id, None)
        logger.info("Stopped recording for camera %s", camera_id)

    def _resolve_source(self, source: str | int) -> str | int:
        if isinstance(source, int):
            return source
        if source == "webcam":
            return settings.default_webcam_index
        return source

    def _record_loop(
        self,
        camera_id: str,
        source: str | int,
        chunk_seconds: int,
        stop_event: threading.Event,
    ) -> None:
        resolved = self._resolve_source(source)
        cap = cv2.VideoCapture(resolved)
        if not cap.isOpened():
            logger.error("Could not open video source %s for camera %s", resolved, camera_id)
            return

        fps = int(cap.get(cv2.CAP_PROP_FPS)) or settings.default_fps
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        frames_per_chunk = fps * chunk_seconds
        chunk_index = 0
        camera_dir = settings.recordings_dir / camera_id
        camera_dir.mkdir(parents=True, exist_ok=True)

        try:
            while not stop_event.is_set():
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                filename = camera_dir / f"chunk_{timestamp}_{chunk_index:04d}.mp4"
                writer = cv2.VideoWriter(
                    str(filename),
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    fps,
                    (width, height),
                )

                frames_written = 0
                while frames_written < frames_per_chunk and not stop_event.is_set():
                    success, frame = cap.read()
                    if not success:
                        logger.warning("Frame read failed for camera %s", camera_id)
                        break
                    writer.write(frame)
                    frames_written += 1

                writer.release()

                if frames_written == 0:
                    break

                enqueue_video_job(
                    {
                        "video_path": str(filename),
                        "camera_id": camera_id,
                        "chunk_index": chunk_index,
                        "frames": frames_written,
                        "fps": fps,
                    }
                )
                logger.info(
                    "Enqueued chunk %s for camera %s (%s frames)",
                    chunk_index,
                    camera_id,
                    frames_written,
                )
                chunk_index += 1
        finally:
            cap.release()


recorder_service = CameraRecorderService()
