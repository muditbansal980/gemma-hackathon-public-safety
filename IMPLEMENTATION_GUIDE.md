# Neuro-Symbolic Public Safety Monitor — Implementation Guide

Improved architecture for the "AI for Public Safety" Kaggle track (Build with Gemma).
This document explains what changed from the original blueprint, why, and exactly
how to run it on Kaggle.

---

## 1. What changed vs. the original blueprint, and why

| Issue in original PDF | Fix in this version |
|---|---|
| Weapon detections were logged under the **object's own track ID**, not the person holding it — so a knife's YOLO track ID became `Subject_<id>` in the timeline, mislabeling the event. | `detector.py` now does a two-pass correlation per frame: track all people, track all flagged objects, then attribute each object to the **nearest person within a proximity radius** (`OBJECT_PROXIMITY_RADIUS_PX`). Unattributed sightings are logged honestly as `object_sighting_unattributed` instead of guessing. |
| Single hard-coded zone polygon. | `config.ZONES` is now a dict of named polygons — add as many restricted areas as the footage needs. |
| No dwell-time or loitering concept — only instantaneous entry/exit. | `SpatialTimelineLogger` tracks per-zone entry time and fires a `loitering` event once dwell time crosses `LOITER_THRESHOLD_SECONDS`, plus reports `dwell_seconds` on every exit. |
| "Crouching" was the only behavior signal; no motion/speed signal. | Added `BehaviorAnalyzer.is_running()` using bbox-center displacement between frames (px/sec). |
| Gemma was handed raw JSON and asked to freely decide "normal vs. abnormal" and "intent" with no grounding — a pure black box wearing a neuro-symbolic label. | Added `reasoning/symbolic_rules.py`: a deterministic, auditable point-scoring system that computes severity **before** Gemma ever runs. Gemma is prompted to explain and narrate that score, not invent its own. This is what actually makes the pipeline neuro-symbolic instead of "CV + an LLM." |
| No fallback if the LLM call fails, and it ran unconditionally. | `main.py` only invokes Gemma when the symbolic layer has flagged something above LOW, and catches generation errors to fall back to the symbolic report alone — cheaper on Kaggle's T4 quota and fails safe. |
| System prompt allowed the model to assert identity/demographics/intent with false certainty — a real liability for a "forensic-grade" tool. | New system prompt explicitly forbids identity/demographic claims, requires "consistent with" language instead of certainty for intent, and requires a "Recommended Human Review Action" section — the report is framed as decision support, not a verdict. |

---

## 2. Project layout

```
neuro_symbolic_public_safety/
├── config.py
├── main.py
├── requirements.txt
├── perception/
│   ├── __init__.py
│   ├── detector.py            # orchestrates YOLOv8 tracking loop
│   ├── tracker_utils.py       # zone entry/exit, dwell time, loitering
│   └── behavior_analyzer.py   # crouching / running geometry heuristics
└── reasoning/
    ├── __init__.py
    ├── symbolic_rules.py      # deterministic severity scorer (the "symbolic" layer)
    ├── prompts.py             # grounded system instruction + JSON schema
    └── gemma_engine.py        # quantized Gemma load + generation
```

---

## 3. Kaggle setup

### 3.1 Notebook environment
1. Create a new Kaggle Notebook, accelerator = **GPU T4 x1** (or x2 if available).
2. Under **Add-ons → Secrets**, add a secret named `HF_TOKEN` with a Hugging Face
   access token that has accepted the **Gemma license** on the model page
   (`google/gemma-2-2b-it`). Gemma weights are gated — the download will fail
   with a 403 until the license is accepted on huggingface.co.
3. Upload your test footage as a Kaggle Dataset (or use the notebook's own
   `/kaggle/input/` mount) and note the path.

### 3.2 First notebook cell — install + auth
```python
!pip install -q -r requirements.txt

import os
from kaggle_secrets import UserSecretsClient
os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
```

### 3.3 Second cell — bring in the project files
Upload this project as a Kaggle Dataset ("neuro-symbolic-public-safety") and
attach it to the notebook, or paste the files directly into
`/kaggle/working/` using `%%writefile` per file. Then:

```python
import sys
sys.path.append("/kaggle/working")
```

### 3.4 Point config at your footage
```python
import config
config.VIDEO_PATH = "/kaggle/input/<your-dataset>/security_footage.mp4"
```

### 3.5 Run it
```python
from main import run_pipeline
run_pipeline(video_path=config.VIDEO_PATH, output_dir="/kaggle/working/output")
```

Outputs land in `/kaggle/working/output/`:
- `timeline.json` — raw perception metadata (zero images, fully anonymous)
- `severity.json` — the deterministic symbolic score per subject
- `forensic_report.md` — Gemma's grounded narrative + trailing JSON block

---

## 4. Tuning for your demo footage

- **Zones**: `config.ZONES` polygons are in pixel coordinates of the source
  video's native resolution. Grab a single frame with OpenCV and use
  `matplotlib` to click-identify corner coordinates before hardcoding them.
- **`FRAME_SKIP`**: lower (1) for short, high-stakes clips where you want
  every frame; raise (3–5) for long clips to fit Kaggle's session time limit.
- **`LOITER_THRESHOLD_SECONDS`**: tune to your clip's timescale — 45s is
  reasonable for a multi-minute clip; drop to 5–10s for a 30-second demo
  reel so the behavior is actually visible to judges.
- **`OBJECT_PROXIMITY_RADIUS_PX`**: depends on your video's resolution and
  camera distance from the scene — measure a typical "held in hand" distance
  in a sample frame and set the radius a bit above it.
- **`SEVERITY_WEIGHTS` / `SEVERITY_THRESHOLDS`**: this is the whole "symbolic"
  policy layer — treat it like a config file security teams could actually
  tune per-deployment, and say so explicitly in your demo narration; it's a
  strong point for judges evaluating "reasoning transparency."

---

## 5. Important accuracy caveat: weapon detection

`THREAT_LABELS` uses YOLOv8's stock COCO classes (`knife`, `baseball bat`,
`scissors`) because that's what ships with `yolov8n.pt` and needs no extra
training — good for a hackathon timeline. Be transparent in your writeup
about the limitation: COCO's `knife` class was annotated almost entirely from
kitchen/dining photos, so **recall on a person brandishing a knife in a
security-camera framing will be materially lower than on a kitchen scene**.

If time allows, a stronger demo swaps in a small fine-tuned detector:
- Search Roboflow Universe or Kaggle Datasets for open weapon-detection
  datasets (several hundred to a few thousand labeled images are enough to
  fine-tune `yolov8n` for a few epochs).
- Keep the stock COCO model for `person` tracking (it's excellent) and only
  swap the weapon-detection head/model.
- Mention this tradeoff explicitly in your submission — judges evaluating a
  "forensic-grade" claim will value the honesty more than a silently
  overconfident system.

---

## 6. Responsible-use notes worth including in your submission

- The system is designed as **decision support for a human reviewer**, not
  an autonomous accusation engine — this is enforced both in the system
  prompt and in `main.py`'s human-review flag. Say this explicitly on your
  submission page; judges in public-safety tracks specifically look for it.
- No raw video, frames, or biometric embeddings are persisted anywhere —
  only anonymous track IDs and geometric/temporal metadata leave the
  perception module. This is real, verifiable in `detector.py` (`del frame`
  immediately after inference).
- False positives are expected at these confidence thresholds; document your
  test clip's actual precision/recall if you have time to hand-label a
  ground truth for the demo video — a small table beats a hand-wave.
- If you deploy this beyond a hackathon demo, note that public video
  surveillance is subject to local law (notice/signage requirements, data
  retention limits, biometric processing rules vary a lot by
  jurisdiction) — worth one slide even if out of scope for the code itself.

---

## 7. Extending further (if you have time before the deadline)

- **Multi-camera fusion**: run `process_video_feed` per camera, merge
  timelines by wall-clock timestamp before symbolic scoring.
- **Streaming instead of batch**: swap `cv2.VideoCapture(path)` for an RTSP
  URL and run the loop continuously with a rolling window fed to Gemma every
  N seconds instead of only at end-of-video.
- **Structured alerting**: `GemmaReasoningEngine.extract_json_block()` is
  already there to pull the `requires_human_review` flag back out
  programmatically — wire it to a Slack/webhook call for a live-demo "alert
  fires" moment, which reads very well in a hackathon video.
