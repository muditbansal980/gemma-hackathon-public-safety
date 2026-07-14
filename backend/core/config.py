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


settings = Settings()
