from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.database import engine, get_db
from backend.models import Base


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

from backend.api.routes.camera import (
    router as camera_router
)


app = FastAPI(
    title="Public Safety API",
    description="Local-first public safety monitoring backend",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(
    camera_router,
    prefix="/api/v1"
)


@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
