import json
import logging
from typing import Any

from ai.perspection.detector import process_video_feed
from backend.services.ai_service.gemma_service import GemmaReasoningEngine
from backend.services.ai_service.reasoning.symbolic_rules import score_timeline

logger = logging.getLogger(__name__)

_gemma_engine: GemmaReasoningEngine | None = None


def _get_gemma_engine() -> GemmaReasoningEngine:
    global _gemma_engine
    if _gemma_engine is None:
        _gemma_engine = GemmaReasoningEngine()
    return _gemma_engine


def _map_severity(level: str) -> str:
    mapping = {
        "LOW": "low",
        "MEDIUM": "medium",
        "HIGH": "high",
        "CRITICAL": "high",
    }
    return mapping.get(level.upper(), "low")


def run_pipeline(video_path: str) -> dict[str, Any]:
    """Run YOLO perception → symbolic scoring → optional Gemma narrative."""
    timeline_json = process_video_feed(video_path)

    if not timeline_json or timeline_json in ("[]", ""):
        return {
            "timeline": [],
            "severity_report": {"overall_level": "LOW", "flags": [], "per_entity": {}},
            "forensic_report": None,
            "risk_level": "low",
        }

    severity_report = score_timeline(timeline_json)
    overall = severity_report.get("overall_level", "LOW")
    risk_level = _map_severity(overall)

    forensic_report = None
    if overall != "LOW" or severity_report.get("flags"):
        try:
            engine = _get_gemma_engine()
            forensic_report = engine.analyze_timeline(timeline_json, severity_report)
        except Exception as exc:
            logger.warning("Gemma reasoning failed: %s", exc)
            forensic_report = (
                "Automated LLM narrative unavailable. "
                f"Rule-based severity: {json.dumps(severity_report, indent=2)}"
            )

    return {
        "timeline": json.loads(timeline_json),
        "severity_report": severity_report,
        "forensic_report": forensic_report,
        "risk_level": risk_level,
    }
