from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5440/public_safety"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_video_queue: str = "video_queue"
    redis_alert_channel: str = "alerts"
    redis_events_channel: str = "events"

    recordings_dir: Path = Path("data/recordings")
    chunk_duration_seconds: int = 60
    default_webcam_index: int = 0
    default_fps: int = 20

    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
settings.recordings_dir.mkdir(parents=True, exist_ok=True)
