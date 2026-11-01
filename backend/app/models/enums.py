import enum


class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    PCELL_MEMBER = "PCELL_MEMBER"
    TPO = "TPO"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    SUSPENDED = "SUSPENDED"
    REJECTED = "REJECTED"
    INACTIVE = "INACTIVE"


class QuestionSubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CORRECTION_REQUIRED = "CORRECTION_REQUIRED"
    DUPLICATE = "DUPLICATE"


class ExperienceStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CORRECTION_REQUIRED = "CORRECTION_REQUIRED"


class Difficulty(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    UNKNOWN = "UNKNOWN"


class FormStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class EventStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class PlacementStatus(str, enum.Enum):
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    JOINED = "JOINED"
    DECLINED = "DECLINED"


class NotificationType(str, enum.Enum):
    INFO = "INFO"
    DEADLINE = "DEADLINE"
    VERIFICATION = "VERIFICATION"
    SYSTEM = "SYSTEM"
