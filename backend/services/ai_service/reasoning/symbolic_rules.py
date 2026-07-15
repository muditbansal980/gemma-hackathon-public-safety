"""
reasoning/symbolic_rules.py

The "symbolic" half of the neuro-symbolic pipeline. Computes a deterministic,
auditable severity score directly from the structured event timeline -- no
neural network involved. This score is handed to Gemma as authoritative
grounding context so the LLM narrates and explains a decision that already
has a rule-based basis, rather than independently inventing a threat verdict
from free-form generation. This is also what lets the system fail safe:
if the LLM call errors out, `score_timeline` alone is enough to drive an
alert.
"""

import json
from collections import defaultdict

import config


def _level_for_score(score):
    thresholds = config.SEVERITY_THRESHOLDS
    level = "LOW"
    for name, cutoff in sorted(thresholds.items(), key=lambda kv: kv[1]):
        if score >= cutoff:
            level = name
    return level


def score_timeline(json_timeline: str) -> dict:
    """
    Returns:
    {
      "per_entity": {entity_id: {"score": int, "level": str, "reasons": [str]}},
      "overall_level": str,
      "flags": [entity_id, ...]   # entities at HIGH or CRITICAL
    }
    """
    events = json.loads(json_timeline)
    weights = config.SEVERITY_WEIGHTS
    per_entity = defaultdict(lambda: {"score": 0, "reasons": []})

    carrying_flagged_object = defaultdict(bool)

    for ev in events:
        entity = ev.get("entity_id")
        if entity is None:
            continue
        record = per_entity[entity]

        if ev.get("event") == "zone_entry":
            record["score"] += weights["zone_entry"]
            record["reasons"].append(f"Entered {ev.get('zone')} at {ev.get('timestamp')}")

        elif ev.get("event") == "loitering":
            record["score"] += weights["loitering"]
            record["reasons"].append(
                f"Loitered in {ev.get('zone')} for {ev.get('dwell_seconds')}s"
            )

        elif ev.get("action") == "object_carry":
            carrying_flagged_object[entity] = True
            record["score"] += weights["weapon_carry"]
            record["reasons"].append(f"Observed carrying flagged object: {ev.get('detail')}")

        elif ev.get("action") == "crouching":
            if carrying_flagged_object[entity]:
                record["score"] += weights["crouching_with_weapon"]
                record["reasons"].append("Crouched while carrying a flagged object")

        elif ev.get("action") == "running":
            record["score"] += weights["running_in_zone"]
            record["reasons"].append(f"Moved at elevated speed ({ev.get('detail')})")

    result = {"per_entity": {}, "flags": []}
    overall_max = 0
    for entity, record in per_entity.items():
        level = _level_for_score(record["score"])
        result["per_entity"][entity] = {
            "score": record["score"],
            "level": level,
            "reasons": record["reasons"],
        }
        overall_max = max(overall_max, record["score"])
        if level in ("HIGH", "CRITICAL"):
            result["flags"].append(entity)

    result["overall_level"] = _level_for_score(overall_max)
    return result
