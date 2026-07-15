"""
perception/tracker_utils.py

Maintains a chronological, privacy-preserving event timeline for every
tracked entity. Only geometric and temporal metadata is stored here --
no image data and no biometric embeddings ever touch this module.

Debouncing: a raw zone crossing is only confirmed as a real zone_entry /
zone_exit once it has held for `debounce_seconds`. Without this, a person
standing near a polygon edge produces rapid-fire flicker (exit/re-entry
pairs a fraction of a second apart) purely from per-frame detection jitter,
which pollutes both the timeline and the downstream severity score.
"""

import cv2
import json
from datetime import datetime, timedelta


class SpatialTimelineLogger:
    def __init__(
        self,
        zones: dict,
        loiter_threshold_seconds: float = 45,
        debounce_seconds: float = 0.3,
    ):
        """
        zones: dict mapping zone_name -> np.ndarray polygon (int32, Nx2)
        loiter_threshold_seconds: dwell time in a zone before a loitering
            event is emitted.
        debounce_seconds: how long a raw boundary crossing must hold before
            it is confirmed as a real zone_entry/zone_exit event.
        """
        self.zones = zones
        self.loiter_threshold_seconds = loiter_threshold_seconds
        self.debounce_seconds = debounce_seconds
        self.tracked_entities = {}
        self.event_log = []
        self.start_sim_time = datetime.now()

    def get_timestamp(self, frame_idx, fps):
        elapsed_seconds = frame_idx / fps
        current_time = self.start_sim_time + timedelta(seconds=elapsed_seconds)
        return current_time.strftime("%H:%M:%S"), elapsed_seconds

    @staticmethod
    def bottom_center(bbox):
        x_min, y_min, x_max, y_max = bbox
        return (int((x_min + x_max) / 2), int(y_max))

    def _zones_containing(self, point):
        return [
            name
            for name, poly in self.zones.items()
            if cv2.pointPolygonTest(poly, point, False) >= 0
        ]

    def _get_entity(self, track_id):
        if track_id not in self.tracked_entities:
            self.tracked_entities[track_id] = {
                "confirmed_zones": set(),
                "zone_entry_elapsed": {},
                "pending_zone_state": {},
                "loitered_zones": set(),
                "last_center": None,
                "last_elapsed": None,
            }
        return self.tracked_entities[track_id]

    def update_position(self, track_id, bbox, timestamp, elapsed_seconds):
        """
        Call once per person-class detection per frame.
        Returns the set of zone names the entity is CONFIRMED to occupy.
        """
        entity = self._get_entity(track_id)
        point = self.bottom_center(bbox)
        raw_zones = set(self._zones_containing(point))
        confirmed_zones = entity["confirmed_zones"]
        pending = entity["pending_zone_state"]

        for zone in self.zones:
            raw_inside = zone in raw_zones
            is_confirmed = zone in confirmed_zones

            if raw_inside == is_confirmed:
                pending.pop(zone, None)
                continue

            target_state = "enter" if raw_inside else "exit"
            existing = pending.get(zone)

            if existing is None or existing[0] != target_state:
                pending[zone] = (target_state, elapsed_seconds)
                continue

            _, since = existing
            if elapsed_seconds - since < self.debounce_seconds:
                continue

            if target_state == "enter":
                confirmed_zones.add(zone)
                entity["zone_entry_elapsed"][zone] = elapsed_seconds
                self.event_log.append(
                    {
                        "timestamp": timestamp,
                        "entity_id": f"Subject_{track_id}",
                        "event": "zone_entry",
                        "zone": zone,
                    }
                )
            else:
                confirmed_zones.discard(zone)
                entry_t = entity["zone_entry_elapsed"].pop(zone, elapsed_seconds)
                self.event_log.append(
                    {
                        "timestamp": timestamp,
                        "entity_id": f"Subject_{track_id}",
                        "event": "zone_exit",
                        "zone": zone,
                        "dwell_seconds": round(elapsed_seconds - entry_t, 1),
                    }
                )
                entity["loitered_zones"].discard(zone)
            pending.pop(zone, None)

        for zone in confirmed_zones:
            entry_t = entity["zone_entry_elapsed"].get(zone)
            if entry_t is None:
                continue
            dwell = elapsed_seconds - entry_t
            if (
                dwell >= self.loiter_threshold_seconds
                and zone not in entity["loitered_zones"]
            ):
                entity["loitered_zones"].add(zone)
                self.event_log.append(
                    {
                        "timestamp": timestamp,
                        "entity_id": f"Subject_{track_id}",
                        "event": "loitering",
                        "zone": zone,
                        "dwell_seconds": round(dwell, 1),
                    }
                )

        entity["last_center"] = point
        entity["last_elapsed"] = elapsed_seconds
        return set(confirmed_zones)

    def compute_speed(self, track_id, bbox, elapsed_seconds):
        """Returns bbox-center displacement in px/sec since the last frame, or None."""
        entity = self._get_entity(track_id)
        point = self.bottom_center(bbox)
        if entity["last_center"] is None or entity["last_elapsed"] is None:
            return None
        dt = elapsed_seconds - entity["last_elapsed"]
        if dt <= 0:
            return None
        dx = point[0] - entity["last_center"][0]
        dy = point[1] - entity["last_center"][1]
        distance = (dx**2 + dy**2) ** 0.5
        return distance / dt

    def log_action(self, track_id, action, detail, timestamp, zone=None):
        self.event_log.append(
            {
                "timestamp": timestamp,
                "entity_id": f"Subject_{track_id}",
                "action": action,
                "detail": detail,
                "zone": zone,
            }
        )

    def export_timeline(self):
        return json.dumps(self.event_log, indent=2)
