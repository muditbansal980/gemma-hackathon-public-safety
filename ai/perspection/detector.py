"""
perception/detector.py

Phase 1 orchestrator: reads the video, runs YOLOv8 tracking, and feeds every
detection through the zone logger + behavior analyzer. The raw frame array
is discarded the instant it has been processed by the model -- nothing
visual survives past this function, only geometric/temporal metadata.

Fix vs. the original blueprint: weapon/object detections carry their OWN
YOLO track ID (separate from any person's track ID), so logging them under
that ID mislabels the event as belonging to "Subject_<object_id>" instead
of the person holding the object. This version explicitly correlates each
flagged object with the nearest person bounding box within a proximity
radius before logging a "carry" event, and leaves unattributed sightings
clearly marked as such rather than guessing.
"""

import cv2
from ultralytics import YOLO
from typing import Optional
import ai.config as config
from ai.perspection.tracker_utils import SpatialTimelineLogger
from ai.perspection.behaviour_analyzer import BehaviorAnalyzer


def _center(bbox):
    x_min, y_min, x_max, y_max = bbox
    return ((x_min + x_max) / 2, (y_min + y_max) / 2)


def _distance(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def process_video_feed(video_path: Optional[str] = None):
    video_path = video_path or config.VIDEO_PATH
    model = YOLO(config.YOLO_MODEL_NAME)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video source: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    logger = SpatialTimelineLogger(
        config.ZONES, config.LOITER_THRESHOLD_SECONDS, config.ZONE_DEBOUNCE_SECONDS
    )
    behavior = BehaviorAnalyzer(
        config.CROUCH_ASPECT_RATIO, config.RUNNING_SPEED_PX_PER_SEC
    )

    frame_idx = 0
    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            frame_idx += 1
            if frame_idx % config.FRAME_SKIP != 0:
                continue

            results = model.track(
                frame, persist=True, verbose=False, conf=config.CONFIDENCE_THRESHOLD
            )
            del frame  # discarded immediately; only metadata is used below

            timestamp, elapsed = logger.get_timestamp(frame_idx, fps)
            boxes = results[0].boxes
            if boxes is None:
                continue

            box_ids = boxes.id
            box_cls = boxes.cls
            box_xyxy = boxes.xyxy
            if box_ids is None or box_cls is None or box_xyxy is None:
                continue

            track_ids = [int(x) for x in box_ids.tolist()]
            class_indices = [int(x) for x in box_cls.tolist()]
            xyxy_coords = box_xyxy.tolist()

            people, objects = [], []
            for tid, cidx, bbox in zip(track_ids, class_indices, xyxy_coords):
                label = model.names[cidx]
                if label == "person":
                    people.append((tid, bbox))
                elif label in config.THREAT_LABELS:
                    objects.append((tid, label, bbox))

            # Pass 1: per-person zone state + posture/motion heuristics
            person_zones = {}
            for tid, bbox in people:
                zones = logger.update_position(tid, bbox, timestamp, elapsed)
                person_zones[tid] = zones
                speed = logger.compute_speed(tid, bbox, elapsed)

                if zones and behavior.is_crouching(bbox):
                    logger.log_action(
                        tid,
                        "crouching",
                        "posture_geometry",
                        timestamp,
                        zone=next(iter(zones)),
                    )
                if zones and behavior.is_running(speed):
                    logger.log_action(
                        tid,
                        "running",
                        f"{speed:.0f}px/s",
                        timestamp,
                        zone=next(iter(zones)),
                    )

            # Pass 2: correlate flagged objects with the nearest person
            for obj_tid, label, obj_bbox in objects:
                obj_center = _center(obj_bbox)
                nearest_person, nearest_dist = None, None
                for tid, bbox in people:
                    d = _distance(obj_center, _center(bbox))
                    if nearest_dist is None or d < nearest_dist:
                        nearest_person, nearest_dist = tid, d

                if (
                    nearest_person is not None
                    and nearest_dist is not None
                    and nearest_dist <= config.OBJECT_PROXIMITY_RADIUS_PX
                ):
                    zone = next(iter(person_zones.get(nearest_person, [])), None)
                    logger.log_action(
                        nearest_person, "object_carry", label, timestamp, zone=zone
                    )
                else:
                    # No person close enough to attribute confidently.
                    logger.log_action(
                        obj_tid, "object_sighting_unattributed", label, timestamp
                    )
    finally:
        cap.release()

    return logger.export_timeline()
