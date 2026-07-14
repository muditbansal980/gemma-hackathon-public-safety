import enum


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"


class EventType(str, enum.Enum):
    DETECTION = "detection"
    ACTION = "action"
    ALERT = "alert"
    HUMAN_INTERVENTION = "human_intervention"
