from abc import ABC, abstractmethod
from typing import List, Optional

from .models import Author, Book, ConversationContext, GeneratedResponse, Message


class MessagingInterface(ABC):
    """Interface for messaging service implementations"""

    @abstractmethod
    async def send_message(self, message: Message) -> bool:
        """Send a message through the messaging service"""
        pass

    @abstractmethod
    async def receive_message(self) -> Message:
        """Receive a message from the messaging service"""
        pass

    @abstractmethod
    async def handle_delivery_status(self, message_id: str, status: str) -> None:
        """Handle message delivery status updates"""
        pass


class LLMInterface(ABC):
    """Interface for LLM service implementations"""

    @abstractmethod
    async def generate_response(
        self, book_content: str, conversation_context: ConversationContext, query: str
    ) -> GeneratedResponse:
        """Generate a response based on book content and conversation context"""
        pass

    @abstractmethod
    async def aggregate_responses(
        self, responses: List[GeneratedResponse], query: str
    ) -> str:
        """Aggregate multiple book-specific responses into a single response"""
        pass

    @abstractmethod
    async def validate_response(self, response: str) -> bool:
        """Validate that a generated response meets quality criteria"""
        pass


class DatabaseInterface(ABC):
    """Interface for database operations"""

    @abstractmethod
    async def get_books_by_author(self, author: str) -> List[Book]:
        """Retrieve all books for a given author"""
        pass

    @abstractmethod
    async def get_author(self, author_id: str) -> Optional[Author]:
        """Retrieve author information"""
        pass

    @abstractmethod
    async def get_conversation_context(
        self, conversation_id: str
    ) -> Optional[ConversationContext]:
        """Retrieve conversation context"""
        pass

    @abstractmethod
    async def store_conversation(self, conversation: ConversationContext) -> bool:
        """Store conversation context"""
        pass

    @abstractmethod
    async def update_conversation(self, conversation: ConversationContext) -> bool:
        """Update existing conversation context"""
        pass

    @abstractmethod
    async def store_message(self, message: Message) -> bool:
        """Store a new message"""
        pass


class BookProcessorInterface(ABC):
    """Interface for book processing operations"""

    @abstractmethod
    async def process_query(
        self, query: str, author: str, conversation_context: ConversationContext
    ) -> List[GeneratedResponse]:
        """Process a query against all books by an author"""
        pass

    @abstractmethod
    async def process_single_book(
        self, book: Book, conversation_context: ConversationContext, query: str
    ) -> GeneratedResponse:
        """Process a query against a single book"""
        pass


class ConversationManagerInterface(ABC):
    """Interface for conversation management"""

    @abstractmethod
    async def process_message(self, message: Message) -> str:
        """Process an incoming message and generate a response"""
        pass

    @abstractmethod
    async def get_or_create_context(self, conversation_id: str) -> ConversationContext:
        """Get existing conversation context or create new one"""
        pass

    @abstractmethod
    async def update_context(
        self, context: ConversationContext, message: Message, response: str
    ) -> None:
        """Update conversation context with new message and response"""
        pass
