"""Create database tables from SQLAlchemy models."""

from backend.core.database import engine
from backend.models import Base


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    init_db()
