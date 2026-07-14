"""
perception/behavior_analyzer.py

Deterministic, geometry-based behavior heuristics. These run entirely on
bounding-box math -- no neural inference -- so they are cheap, auditable,
and form part of the "symbolic" evidence layer that grounds the LLM's
narrative in the reasoning engine.
"""


class BehaviorAnalyzer:
    def __init__(self, crouch_aspect_ratio=1.3, running_speed_px_per_sec=250):
        self.crouch_aspect_ratio = crouch_aspect_ratio
        self.running_speed_px_per_sec = running_speed_px_per_sec

    def is_crouching(self, bbox):
        x_min, y_min, x_max, y_max = bbox
        width = x_max - x_min
        height = max(y_max - y_min, 1e-6)
        return (width / height) >= self.crouch_aspect_ratio

    def is_running(self, speed_px_per_sec):
        return speed_px_per_sec is not None and speed_px_per_sec >= self.running_speed_px_per_sec
