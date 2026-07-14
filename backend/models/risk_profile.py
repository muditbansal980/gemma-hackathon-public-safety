import uuid

from sqlalchemy import Enum, Float, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin
from backend.models.enums import RiskLevel


class RiskProfile(Base, TimestampMixin):
    __tablename__ = "risk_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risk_level"), unique=True, nullable=False
    )
    sensitivity: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    settings: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )
    description: Mapped[str | None] = mapped_column(String(255))
