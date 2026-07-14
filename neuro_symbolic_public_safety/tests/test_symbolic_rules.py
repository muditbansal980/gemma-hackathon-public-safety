"""
tests/test_symbolic_rules.py

Run with `pytest` from the project root, or via VS Code's Test Explorer
(enabled by .vscode/settings.json). No GPU, video, or model download needed
-- this only exercises the deterministic scoring logic.
"""

import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reasoning.symbolic_rules import score_timeline


def _timeline(events):
    return json.dumps(events)


def test_empty_timeline_returns_low():
    result = score_timeline(_timeline([]))
    assert result["overall_level"] == "LOW"
    assert result["flags"] == []


def test_zone_entry_alone_stays_low():
    events = [
        {"timestamp": "00:00:01", "entity_id": "Subject_1",
         "event": "zone_entry", "zone": "Restricted_Zone_Alpha"},
    ]
    result = score_timeline(_timeline(events))
    assert result["per_entity"]["Subject_1"]["score"] == 1
    assert result["overall_level"] == "LOW"


def test_weapon_carry_plus_crouch_escalates_to_high():
    events = [
        {"timestamp": "00:00:01", "entity_id": "Subject_1",
         "event": "zone_entry", "zone": "Restricted_Zone_Alpha"},
        {"timestamp": "00:00:02", "entity_id": "Subject_1",
         "action": "object_carry", "detail": "knife", "zone": "Restricted_Zone_Alpha"},
        {"timestamp": "00:00:03", "entity_id": "Subject_1",
         "action": "crouching", "detail": "posture_geometry", "zone": "Restricted_Zone_Alpha"},
    ]
    result = score_timeline(_timeline(events))
    entity = result["per_entity"]["Subject_1"]
    # zone_entry(1) + weapon_carry(4) + crouching_with_weapon(3) = 8 -> HIGH
    assert entity["score"] == 8
    assert entity["level"] == "HIGH"
    assert "Subject_1" in result["flags"]


def test_loitering_event_is_scored():
    events = [
        {"timestamp": "00:00:01", "entity_id": "Subject_2",
         "event": "zone_entry", "zone": "Restricted_Zone_Alpha"},
        {"timestamp": "00:00:50", "entity_id": "Subject_2",
         "event": "loitering", "zone": "Restricted_Zone_Alpha", "dwell_seconds": 49.0},
    ]
    result = score_timeline(_timeline(events))
    assert result["per_entity"]["Subject_2"]["score"] == 3  # 1 + 2


def test_unattributed_object_sighting_does_not_inflate_person_score():
    events = [
        {"timestamp": "00:00:01", "entity_id": "Subject_3",
         "event": "zone_entry", "zone": "Restricted_Zone_Alpha"},
        {"timestamp": "00:00:02", "entity_id": "Subject_99",
         "action": "object_sighting_unattributed", "detail": "knife", "zone": None},
    ]
    result = score_timeline(_timeline(events))
    assert result["per_entity"]["Subject_3"]["score"] == 1
    assert "Subject_99" not in result["per_entity"] or result["per_entity"]["Subject_99"]["score"] == 0
