"""Central ML pipeline configuration."""

import numpy as np

YOLO_MODEL_NAME = "yolov8n.pt"
GEMMA_MODEL_NAME = "google/gemma-2-2b-it"

VIDEO_PATH = "data/recordings/security_footage.mp4"  # fallback for standalone scripts only
FRAME_SKIP = 2
CONFIDENCE_THRESHOLD = 0.45

ZONES = {
    "Restricted_Zone_Alpha": np.array(
        [[107, 106], [120, 205], [296, 204], [239, 134], [177, 70]], dtype=np.int32
    ),
}

THREAT_LABELS = ["knife", "baseball bat", "scissors"]

CROUCH_ASPECT_RATIO = 1.3
RUNNING_SPEED_PX_PER_SEC = 250
LOITER_THRESHOLD_SECONDS = 20
OBJECT_PROXIMITY_RADIUS_PX = 120
ZONE_DEBOUNCE_SECONDS = 0.3

SEVERITY_WEIGHTS = {
    "zone_entry": 1,
    "weapon_carry": 4,
    "loitering": 2,
    "crouching_with_weapon": 3,
    "running_in_zone": 2,
}

SEVERITY_THRESHOLDS = {
    "LOW": 0,
    "MEDIUM": 3,
    "HIGH": 6,
    "CRITICAL": 9,
}
