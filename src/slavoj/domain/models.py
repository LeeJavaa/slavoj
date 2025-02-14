from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageType(Enum):
    """Enum for different types of messages"""

    USER = "user"
    AUTHOR = "author"
    SYSTEM = "system"


@dataclass
class Message:
    """Represents a single message in a conversation"""

    content: str
    timestamp: datetime
    sender_id: str
    recipient_id: str
    conversation_id: str
    message_type: MessageType
    metadata: Dict[str, any] = field(default_factory=dict)

    @classmethod
    def message_to_dict(cls, message: "Message") -> Dict[str, Any]:
        """Convert Message object to dictionary for storage"""

        # Sometimes the Message objects are conversions from the MongoDB
        # document, in these cases we need to first convert the string fields
        # into the correct type
        timestamp = (
            message.timestamp.isoformat()
            if isinstance(message.timestamp, datetime)
            else message.timestamp
        )

        message_type = (
            message.message_type.value
            if isinstance(message.message_type, MessageType)
            else message.message_type
        )

        return {
            "content": message.content,
            "timestamp": timestamp,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "conversation_id": message.conversation_id,
            "message_type": message_type,
            "metadata": message.metadata,
        }

@dataclass
class Book:
    """Represents a book in the system"""

    title: str
    content: str
    author: str
    publication_year: Optional[int] = None
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class Author:
    """Represents an author and their associated data"""

    name: str
    whatsapp_number: str
    books: List[Book]
    conversation_style: Dict[str, any]
    bio: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Represents the context of an ongoing conversation"""

    id: str
    user_id: str
    author_id: str
    messages: List[Message]
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class GeneratedResponse:
    """Represents a response generated for a specific book"""

    book_title: str
    content: str
    confidence_score: float
    generation_time: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, any] = field(default_factory=dict)
