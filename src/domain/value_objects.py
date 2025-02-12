from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class MessageId:
    """Value object for message identification"""
    value: str
    platform: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class UserId:
    """Value object for user identification"""
    value: str
    platform: str
    metadata: Optional[dict] = None


@dataclass(frozen=True)
class AuthorId:
    """Value object for author identification"""
    value: str
    normalized_name: str  # Normalized version of author name for lookups