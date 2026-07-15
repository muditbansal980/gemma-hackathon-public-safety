import logging
from typing import Any

import ai.config as ai_config
import cv2
import numpy as np
from ultralytics import YOLO

from backend.core.config import settings
from backend.websocket.preview_ws import preview_ws_manager

logger = logging.getLogger(__name__)


class LivePreviewService:
    """Runs YOLO on sampled recorder frames and broadcasts annotated JPEGs."""

    def __init__(self) -> None:
        self._model: YOLO | None = None

    def _get_model(self) -> YOLO:
        if self._model is None:
            self._model = YOLO(ai_config.YOLO_MODEL_NAME)
            logger.info("Loaded YOLO model for live preview")
        return self._model

    def process_frame(self, camera_id: str, frame: np.ndarray) -> None:
        try:
            model = self._get_model()
            results = model.track(
                frame,
                persist=True,
                verbose=False,
                conf=ai_config.CONFIDENCE_THRESHOLD,
            )
            annotated = results[0].plot()
            detections = self._extract_detections(results[0], model.names)
            ok, jpeg = cv2.imencode(
                ".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 75]
            )
            if not ok:
                return
            preview_ws_manager.schedule_broadcast(
                camera_id, jpeg.tobytes(), detections
            )
        except Exception:
            logger.exception("Live preview failed for camera %s", camera_id)

    @staticmethod
    def _extract_detections(result: Any, names: dict[int, str]) -> list[dict[str, Any]]:
        detections: list[dict[str, Any]] = []
        boxes = result.boxes
        if boxes is None:
            return detections

        box_ids = boxes.id
        box_cls = boxes.cls
        box_xyxy = boxes.xyxy
        box_conf = boxes.conf
        if box_cls is None or box_xyxy is None or box_conf is None:
            return detections

        track_ids = (
            [int(x) for x in box_ids.tolist()] if box_ids is not None else [None] * len(box_cls)
        )
        for tid, cidx, bbox, conf in zip(
            track_ids,
            [int(x) for x in box_cls.tolist()],
            box_xyxy.tolist(),
            [float(x) for x in box_conf.tolist()],
        ):
            label = names[cidx]
            detections.append(
                {
                    "track_id": tid,
                    "label": label,
                    "confidence": round(conf, 2),
                    "bbox": [round(v, 1) for v in bbox],
                    "is_threat": label in ai_config.THREAT_LABELS,
                }
            )
        return detections


live_preview_service = LivePreviewService()
