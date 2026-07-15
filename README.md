# Public Safety Monitoring System

End-to-end pipeline for hackathon demo: record video from webcam or RTSP, process in 1-minute chunks via a Redis-backed worker (YOLOv8 + symbolic rules + Gemma), persist events/alerts to PostgreSQL, and push live alerts to a Next.js dashboard over WebSocket.

## Architecture

```
Webcam / RTSP
    ↓  (OpenCV, 60s chunks)
Camera Recorder Service
    ↓  LPUSH video_queue
Redis
    ↓  BRPOP (video_worker)
YOLOv8 → Symbolic Rules → Gemma (if HIGH/CRITICAL)
    ↓
PostgreSQL (events, alerts)
    ↓  PUBLISH alerts + events
WebSocket → Next.js Dashboard (alerts + events panels)
```

## Quick start

### 1. Infrastructure

```bash
cp .env.example .env
docker compose up -d
```

### 2. Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
python scripts/setup/init_db.py
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Video worker (separate terminal)

```bash
./scripts/setup/run_worker.sh
```

### 4. Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000 — register a camera, click **Record**, and alerts will appear after each processed chunk.

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

## Branch

This work lives on **`crsor-code`**, built from `origin/new_code` with integrated YOLO/Gemma pipeline and Next.js frontend.
