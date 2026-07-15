# Public Safety Monitoring System

End-to-end pipeline for hackathon demo: record video from webcam or RTSP, process in 1-minute chunks via a Redis-backed worker (YOLOv8 + symbolic rules + Gemini API), persist events/alerts to PostgreSQL, and push live alerts to a Next.js dashboard over WebSocket.

## Architecture

```
Webcam / RTSP
    ↓  (OpenCV, 60s chunks + live YOLO preview)
FastAPI Backend
    ├─ LPUSH video_queue → Redis
    ├─ WS /ws/preview/{camera_id} → annotated frames to dashboard
    └─ WS /ws/alerts + /ws/events
         ↓
worker/ (separate process)
    BRPOP video_queue
    YOLO → Symbolic Rules → Gemini API (if HIGH/CRITICAL)
         ↓
    PostgreSQL (events, alerts)
         ↓
    Next.js Dashboard (live preview + alerts + events)
```

## Quick start (Windows)

### 1. Infrastructure

```powershell
cp .env.example .env
# Edit .env and set GEMINI_API_KEY from https://aistudio.google.com/apikey
docker compose up -d
```

### 2. Backend (Terminal 2)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python scripts/setup/init_db.py
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Video worker (Terminal 3 — separate from backend)

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r worker/requirements.txt
.\scripts\setup\run_worker.ps1
```

### 4. Frontend (Terminal 4)

```powershell
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000 — register a camera, click **Record**, and you should see:

- **Left panel:** browser webcam mirror (`getUserMedia`)
- **Right panel:** backend YOLO-annotated frames with bounding boxes
- **Alerts panel:** Gemini forensic narrative when severity is elevated

## Quick start (Linux / macOS)

```bash
cp .env.example .env
docker compose up -d

python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
python scripts/setup/init_db.py
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# separate terminal
pip install -r worker/requirements.txt
./scripts/setup/run_worker.sh

# separate terminal
cd frontend && cp .env.local.example .env.local && npm install && npm run dev
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Failed to fetch` / red "Backend offline" banner | Start FastAPI on port 8000 and ensure Docker (Postgres + Redis) is running |
| No annotated preview frames | Backend must be recording; YOLO loads on first frame (~5s) |
| Browser mirror unavailable | Windows may block dual camera access — annotated backend stream still works |
| No Gemini narrative in alerts | Set `GEMINI_API_KEY` in root `.env` and restart the worker |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| CRUD | `/api/v1/cameras/` | Camera management |
| POST | `/api/v1/recording/{id}/start` | Start recording |
| POST | `/api/v1/recording/{id}/stop` | Stop recording |
| GET | `/api/v1/alerts/` | List alerts |
| GET | `/api/v1/recording/active` | List cameras currently recording |
| GET | `/api/v1/events/` | List detection events |
| WS | `/ws/alerts` | Live alert stream |
| WS | `/ws/events` | Live event stream (processed chunks) |
| WS | `/ws/preview/{camera_id}` | Live YOLO-annotated preview frames |

## Project layout

```
backend/          FastAPI API server + live preview + recording
worker/           Separate Redis consumer (YOLO + Gemini pipeline)
ai/               Perception models (YOLO detector, symbolic rules)
frontend/         Next.js + Tailwind dashboard
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model for severity narratives |
| `PREVIEW_FRAME_SKIP` | `3` | Run live YOLO every Nth recorded frame |
| `CHUNK_DURATION_SECONDS` | `60` | Video chunk size for Redis queue |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend → backend URL |
