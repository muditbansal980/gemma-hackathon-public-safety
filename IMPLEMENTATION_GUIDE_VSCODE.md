# Neuro-Symbolic Public Safety Monitor — VS Code Local Development Guide

This is a companion to the Kaggle guide, for developing and debugging the
pipeline on your own machine in VS Code before you ever touch a Kaggle
notebook. Local dev gives you three things Kaggle can't: a real debugger
with breakpoints, an interactive zone-polygon calibrator (needs a GUI
window), and a fast test loop that doesn't burn GPU quota.

---

## 1. Prerequisites

- **Python 3.10 or 3.11** (Gemma's `transformers`/`bitsandbytes` stack is
  tested against these; 3.12 works in most setups too but pin to 3.10/3.11
  if you hit dependency resolution issues).
- **VS Code** with these extensions (a prompt to install them will appear
  automatically when you open the project, via `.vscode/extensions.json`):
  - `ms-python.python` — core Python support
  - `ms-python.vscode-pylance` — type checking / IntelliSense
  - `ms-python.debugpy` — the debugger VS Code now uses for Python
  - `ms-python.black-formatter` — formatting on save
  - `charliermarsh.ruff` — fast linting
- **Git** (optional but recommended — the `.gitignore` in this project is
  already set up for you).
- **A CUDA-capable NVIDIA GPU** if you want to run Gemma locally at
  reasonable speed. CPU-only will technically run but generation will be
  very slow (see §6 for a CPU-friendly workaround).
- **Windows users**: `bitsandbytes` 4-bit quantization is far more reliable
  under **WSL2** than native Windows. If you're on Windows, install the
  "WSL" extension in VS Code, set up an Ubuntu WSL2 distro, and do
  everything below inside that WSL2 environment — VS Code's Remote-WSL
  integration makes this transparent (bottom-left green `><` button →
  "Connect to WSL").

---

## 2. Get the project into VS Code

```bash
# unzip the project you downloaded, then:
cd neuro_symbolic_public_safety
code .
```

VS Code will detect `.vscode/extensions.json` and offer to install the
recommended extensions — accept that prompt.

---

## 3. Create and select a virtual environment

From the VS Code integrated terminal (`` Ctrl+` ``):

```bash
python3 -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Then tell VS Code to use it:
`Ctrl+Shift+P` → **Python: Select Interpreter** → pick the one showing
`.venv` in its path. The bottom status bar should now read something like
`Python 3.11.x ('.venv': venv)`.

---

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

If you have an NVIDIA GPU, get the CUDA-matched PyTorch build instead of
the default CPU wheel — check
[pytorch.org/get-started/locally](https://pytorch.org) for the exact
command for your CUDA version, e.g.:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

Run before doing anything else, to confirm your GPU is visible:

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no GPU')"
```

If this prints `False`, either fix your CUDA/driver install or jump to §6
for the CPU-friendly path.

---

## 5. Hugging Face authentication (required for Gemma)

Gemma weights are gated. You must accept the license on the model page
before downloading:

1. Visit `https://huggingface.co/google/gemma-2-2b-it`, log in, accept the
   license.
2. Create an access token at `https://huggingface.co/settings/tokens`
   (read access is enough).
3. Copy `.env.example` to `.env` and paste your token in:

```bash
cp .env.example .env
```

```
HF_TOKEN=hf_your_real_token_here
```

`.env` is already in `.gitignore` — it will not get committed. The VS Code
debug configs in `.vscode/launch.json` already load it via `"envFile":
"${workspaceFolder}/.env"`. If you're running from a plain terminal instead
of the debugger, load it manually:

```bash
pip install python-dotenv   # if not already pulled in transitively
python -c "from dotenv import load_dotenv; load_dotenv()"
# or, simpler, just export it for the session:
export HF_TOKEN=hf_your_real_token_here      # macOS/Linux
$env:HF_TOKEN="hf_your_real_token_here"      # Windows PowerShell
```

`transformers` automatically picks up `HF_TOKEN` from the environment for
gated downloads — no code changes needed.

---

## 6. If you don't have a usable local GPU

You have two reasonable options:

- **Develop everything except the LLM call locally, run the LLM step on
  Kaggle.** The perception pipeline (`detector.py`) and the symbolic
  scorer (`symbolic_rules.py`) need no GPU at all and are the parts you'll
  actually spend most of your debugging time on — the zone calibrator,
  proximity-radius tuning, and severity-weight tuning are all CPU-only.
  Only swap to Kaggle for the final `GemmaReasoningEngine` runs.
- **Run Gemma on CPU locally for correctness testing** (slow, but fine for
  verifying the prompt/JSON-parsing logic works before a real GPU run):
  in `reasoning/gemma_engine.py`, temporarily drop the
  `quantization_config` argument and pass `device_map="cpu"` instead of
  `"auto"` — 4-bit `bitsandbytes` quantization needs CUDA, so this trades
  quantization for CPU compatibility. Expect single-digit tokens/sec.

---

## 7. Get a test video

Drop a short (30–90s) sample clip at `data/security_footage.mp4` — the
`data/` folder is already git-ignored so you won't accidentally commit a
large binary. `config.VIDEO_PATH` defaults to `"security_footage.mp4"`
(relative path), so either:

- place your file at the project root as `security_footage.mp4`, or
- point `config.VIDEO_PATH` at `data/security_footage.mp4` and update the
  `--video` arg in `.vscode/launch.json` to match (already set to
  `${workspaceFolder}/data/security_footage.mp4` by default).

---

## 8. Calibrate your zone polygon interactively

This is the single biggest advantage of local development over Kaggle:
Kaggle notebooks can't show you an interactive GUI window, so on Kaggle
you're stuck eyeballing pixel coordinates. Locally, use the included tool:

```bash
python tools/zone_calibrator.py --video data/security_footage.mp4 --zone-name Restricted_Zone_Alpha
```

A window opens on your first frame. Click to lay down polygon points
around the area you want to monitor, then press `s` to save — it prints a
ready-to-paste `np.array(...)` block. Copy that directly into
`config.ZONES` in `config.py`. Press `u` to undo a point, `r` to clear
everything, `q`/`Esc` to quit without saving.

You can also launch this from VS Code directly: open the Run and Debug
panel (`Ctrl+Shift+D`), pick **"Zone Calibrator (interactive)"** from the
dropdown, press `F5`.

---

## 9. Running the pipeline

**Option A — VS Code debugger (recommended while developing):**
Run and Debug panel → select **"Run Pipeline (main.py)"** → `F5`.
Set breakpoints anywhere (e.g. inside `detector.py`'s per-frame loop, or
`symbolic_rules.score_timeline`) and step through frame-by-frame — this is
the fastest way to understand why a particular event fired or didn't.

**Option B — plain terminal:**
```bash
python main.py --video data/security_footage.mp4 --output-dir output
```

Either way, outputs land in `output/`:
- `timeline.json` — raw perception metadata
- `severity.json` — deterministic symbolic score
- `forensic_report.md` — Gemma's grounded narrative (only generated if
  severity is above LOW — see `main.py`)

---

## 10. Fast iteration without touching the GPU at all

Most of your tuning time will go into `config.py` thresholds
(`LOITER_THRESHOLD_SECONDS`, `OBJECT_PROXIMITY_RADIUS_PX`,
`CROUCH_ASPECT_RATIO`, `SEVERITY_WEIGHTS`) and the zone polygon — none of
which need Gemma. Two ways to iterate fast:

1. **Re-run only the symbolic scorer against a saved timeline** — once
   you have a `timeline.json` from one perception run, you can re-score it
   instantly without re-running YOLO or touching the GPU:
   ```python
   from reasoning.symbolic_rules import score_timeline
   with open("output/timeline.json") as f:
       print(score_timeline(f.read()))
   ```
   Paste that into the VS Code **Python Interactive Window**
   (`Shift+Enter` on a selection, or right-click → "Run Selection/Line in
   Interactive Window") for instant feedback as you tweak weights.

2. **Run the test suite** after any change to `symbolic_rules.py`:
   ```bash
   pytest
   ```
   or use VS Code's **Testing** sidebar (flask icon) — tests are already
   wired up via `.vscode/settings.json`
   (`python.testing.pytestEnabled: true`). Click any test's green arrow to
   run just that one, or the beaker icon to run everything and see
   pass/fail inline in the gutter.

---

## 11. Debugging tips specific to this pipeline

- **Breakpoint in `detector.py`'s main loop** to inspect `boxes`,
  `track_ids`, and `class_indices` per frame if tracking looks wrong —
  the Debug Console lets you evaluate `model.names` to check class-index
  mapping matches what you expect.
- **Watch expression** `person_zones` inside the frame loop to confirm
  zone membership is being computed correctly before the object-to-person
  correlation pass runs.
- **`justMyCode: true`** in `launch.json` keeps the debugger from stepping
  into `ultralytics`/`transformers` internals — flip it to `false`
  temporarily if you need to trace into a library call.
- If `model.track()` throws a CUDA OOM error on your GPU, lower
  `FRAME_SKIP` is the wrong fix (that's for speed, not memory) — instead
  drop to `yolov8n.pt` if you're on a larger variant, or reduce video
  resolution before feeding it in.

---

## 12. Linting and formatting

`ruff` and `black` are in `.vscode/extensions.json` and wired to format on
save via `.vscode/settings.json`. To run them manually across the whole
project:

```bash
pip install ruff black
ruff check .
black .
```

---

## 13. Recap: local vs. Kaggle division of labor

| Task | Where |
|---|---|
| Zone polygon calibration (needs GUI) | **Local / VS Code only** |
| Tuning `SEVERITY_WEIGHTS` / thresholds | Local (fast, no GPU) |
| Unit-testing `symbolic_rules.py` | Local (fast, no GPU) |
| Debugging the YOLO tracking loop with breakpoints | Local |
| Full pipeline run with Gemma at real speed | Kaggle T4 (or a local GPU if you have one ≥8GB VRAM) |
| Final demo video recording | Either — Kaggle if your local GPU is weak |

Develop and tune everything locally, then push the finished `config.py`
values to your Kaggle notebook for the GPU-bound Gemma runs.
