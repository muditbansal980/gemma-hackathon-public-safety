"""
main.py

Pipeline orchestrator: Perception -> Symbolic Scoring -> Causal Reasoning.

Run with:
    python main.py --video security_footage.mp4 --output-dir output

The LLM call is only made when the deterministic symbolic scorer has
flagged at least one HIGH/CRITICAL subject, or overall_level isn't LOW.
This keeps the expensive Gemma inference off the hot path for ordinary
footage and gives the system a rule-based result even if the LLM call
fails or times out.
"""

import argparse
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import config
from perception.detector import process_video_feed
from reasoning.symbolic_rules import score_timeline
from reasoning.gemma_engine import GemmaReasoningEngine
from typing import Optional


def run_pipeline(video_path: Optional[str] = None, output_dir: str = "output"):
    os.makedirs(output_dir, exist_ok=True)

    print("[1/3] Running perception pipeline (YOLOv8 tracking)...")
    metadata_timeline = process_video_feed(video_path)
    if metadata_timeline in ("[]", "", None):
        print("No tracked entities found -- nothing to report.")
        return

    with open(os.path.join(output_dir, "timeline.json"), "w") as f:
        f.write(metadata_timeline)

    print("[2/3] Computing rule-based severity scores...")
    severity_report = score_timeline(metadata_timeline)
    with open(os.path.join(output_dir, "severity.json"), "w") as f:
        json.dump(severity_report, f, indent=2)
    print(f"    Overall severity: {severity_report['overall_level']}  "
          f"Flagged subjects: {severity_report['flags'] or 'none'}")

    if severity_report["overall_level"] == "LOW" and not severity_report["flags"]:
        print("No elevated-severity subjects detected -- skipping LLM narrative.")
        return

    print(f"[3/3] Generating causal reasoning report with {config.GEMMA_MODEL_NAME}...")
    try:
        engine = GemmaReasoningEngine()
        forensic_report = engine.analyze_timeline(metadata_timeline, severity_report)
    except Exception as exc:  # noqa: BLE001 -- pipeline must degrade gracefully
        print(f"    Gemma reasoning step failed ({exc}); falling back to symbolic report only.")
        forensic_report = (
            "### Automated LLM narrative unavailable.\n"
            f"Rule-based severity report:\n```json\n{json.dumps(severity_report, indent=2)}\n```"
        )

    with open(os.path.join(output_dir, "forensic_report.md"), "w") as f:
        f.write(forensic_report)

    print(forensic_report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Neuro-Symbolic Public Safety Monitor")
    parser.add_argument("--video", default=None,
                         help="Path to input video (defaults to config.VIDEO_PATH)")
    parser.add_argument("--output-dir", default="output",
                         help="Directory for JSON/markdown outputs")
    args = parser.parse_args()
    run_pipeline(args.video, args.output_dir)
