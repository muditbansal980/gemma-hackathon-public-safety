import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.api.routes.alerts import router as alerts_router
from backend.api.routes.camera import router as camera_router
from backend.api.routes.events import router as events_router
from backend.api.routes.recording import router as recording_router
from backend.core.config import settings
from backend.core.database import engine, get_db
from backend.models import Base
from backend.websocket.alert_ws import alert_ws_manager
from backend.websocket.event_ws import event_ws_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    redis_task = asyncio.create_task(alert_ws_manager.listen_redis())
    events_task = asyncio.create_task(event_ws_manager.listen_redis())
    logger.info("Application started")
    yield
    redis_task.cancel()
    events_task.cancel()
    try:
        await redis_task
    except asyncio.CancelledError:
        pass
    try:
        await events_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Public Safety API",
    description="Local-first public safety monitoring backend",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(camera_router, prefix="/api/v1")
app.include_router(recording_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")


@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    await alert_ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        alert_ws_manager.disconnect(websocket)


@app.websocket("/ws/events")
async def events_websocket(websocket: WebSocket):
    await event_ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
