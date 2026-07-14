"""
Central configuration for the Neuro-Symbolic Public Safety Monitoring pipeline.
Every tunable parameter lives here so perception and reasoning code never
hard-codes thresholds.
"""

import numpy as np

# ---------------------------------------------------------------------------
# Model selection
# ---------------------------------------------------------------------------
YOLO_MODEL_NAME = "yolov8n.pt"  # swap to yolov8s.pt for higher accuracy
GEMMA_MODEL_NAME = "google/gemma-2-2b-it"  # use gemma-2-9b-it if VRAM allows (>16GB)

# ---------------------------------------------------------------------------
# Video source
# ---------------------------------------------------------------------------
VIDEO_PATH = "data/security_footage.mp4"
FRAME_SKIP = 2  # process every Nth frame
CONFIDENCE_THRESHOLD = 0.45  # discard low-confidence detections

# ---------------------------------------------------------------------------
# Zones — supports multiple named restricted areas instead of a single polygon
# ---------------------------------------------------------------------------
ZONES = {
    "Restricted_Zone_Alpha": np.array(
        [[107, 106], [120, 205], [296, 204], [239, 134], [177, 70]], dtype=np.int32
    ),
    # Add more zones as needed, e.g.:
    # "Loading_Dock_Bravo": np.array(
    #     [[600, 200], [900, 200], [900, 480], [600, 480]], dtype=np.int32
    # ),
}

# ---------------------------------------------------------------------------
# Threat taxonomy — COCO-detectable classes only (see README accuracy caveat)
# ---------------------------------------------------------------------------
THREAT_LABELS = ["knife", "baseball bat", "scissors"]

# ---------------------------------------------------------------------------
# Behavior heuristics (pure geometry — no neural inference)
# ---------------------------------------------------------------------------
CROUCH_ASPECT_RATIO = 1.3  # bbox width/height above which posture reads as crouched
RUNNING_SPEED_PX_PER_SEC = 250  # bbox-center displacement threshold for "running"
LOITER_THRESHOLD_SECONDS = 20  # dwell time in a zone before a loitering event fires
OBJECT_PROXIMITY_RADIUS_PX = (
    120  # max distance to attribute a weapon sighting to a person
)
ZONE_DEBOUNCE_SECONDS = (
    0.3  # min hold time before a boundary crossing is confirmed (filters edge jitter)
)

# ---------------------------------------------------------------------------
# Symbolic severity scoring (see reasoning/symbolic_rules.py)
# ---------------------------------------------------------------------------
SEVERITY_WEIGHTS = {
    "zone_entry": 1,
    "weapon_carry": 4,
    "loitering": 2,
    "crouching_with_weapon": 3,
    "running_in_zone": 2,
}

# Cumulative-score cutoffs; a score is mapped to the highest level it clears.
SEVERITY_THRESHOLDS = {
    "LOW": 0,
    "MEDIUM": 3,
    "HIGH": 6,
    "CRITICAL": 9,
}
