from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Any
from datetime import datetime

from slavoj.domain.interfaces import DatabaseInterface
from slavoj.domain.models import Book, Author, ConversationContext, Message
from slavoj.core.exceptions import DatabaseError
from slavoj.core.logging import LoggerFactory


class MongoDB(DatabaseInterface):
    def __init__(self, connection_string: str, database: str):
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client[database]
        self.logger = LoggerFactory.create_logger("MongoDB")

    async def get_books_by_author(self, author: str) -> List[Book]:
        try:
            cursor = self.db.books.find({"author": author})
            books = await cursor.to_list(length=None)
            return [Book(**book) for book in books]
        except Exception as e:
            self.logger.error(f"Failed to retrieve books: {e}")
            raise DatabaseError(f"Failed to retrieve books: {e}")

    async def get_author(self, author_id: str) -> Optional[Author]:
        try:
            author_doc = await self.db.authors.find_one({"name": author_id})
            if not author_doc:
                return None

            # Get books for this author
            books = await self.get_books_by_author(author_id)
            author_doc['books'] = books

            return Author(**author_doc)
        except Exception as e:
            self.logger.error(f"Failed to retrieve author: {e}")
            raise DatabaseError(f"Failed to retrieve author: {e}")

    async def get_conversation_context(self, conversation_id: str) -> Optional[
        ConversationContext]:
        try:
            context = await self.db.conversations.find_one(
                {"id": conversation_id})
            if not context:
                return None

            # Convert stored dates back to datetime objects
            context['created_at'] = datetime.fromisoformat(
                context['created_at'])
            context['last_updated'] = datetime.fromisoformat(
                context['last_updated'])

            # Convert message dictionaries to Message objects
            context['messages'] = [Message(**msg) for msg in
                                   context['messages']]

            return ConversationContext(**context)
        except Exception as e:
            self.logger.error(f"Failed to retrieve conversation: {e}")
            raise DatabaseError(f"Failed to retrieve conversation: {e}")

    async def store_conversation(self,
                                 conversation: ConversationContext) -> bool:
        try:
            # Convert datetime objects to ISO format strings for storage
            conversation_dict = {
                "id": conversation.id,
                "user_id": conversation.user_id,
                "author_id": conversation.author_id,
                "messages": [self._message_to_dict(msg) for msg in
                             conversation.messages],
                "created_at": conversation.created_at.isoformat(),
                "last_updated": conversation.last_updated.isoformat(),
                "metadata": conversation.metadata
            }

            result = await self.db.conversations.insert_one(conversation_dict)
            self.logger.info(f"Stored conversation: {result.inserted_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store conversation: {e}")
            raise DatabaseError(f"Failed to store conversation: {e}")

    async def update_conversation(self,
                                  conversation: ConversationContext) -> bool:
        try:
            conversation_dict = {
                "user_id": conversation.user_id,
                "author_id": conversation.author_id,
                "messages": [self._message_to_dict(msg) for msg in
                             conversation.messages],
                "last_updated": conversation.last_updated.isoformat(),
                "metadata": conversation.metadata
            }

            result = await self.db.conversations.update_one(
                {"id": conversation.id},
                {"$set": conversation_dict}
            )

            if result.modified_count == 0:
                raise DatabaseError(
                    f"No conversation found with id: {conversation.id}")

            self.logger.info(f"Updated conversation: {conversation.id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update conversation: {e}")
            raise DatabaseError(f"Failed to update conversation: {e}")

    async def store_message(self, message: Message) -> bool:
        try:
            message_dict = self._message_to_dict(message)
            result = await self.db.messages.insert_one(message_dict)
            self.logger.info(f"Stored message: {result.inserted_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store message: {e}")
            raise DatabaseError(f"Failed to store message: {e}")

    def _message_to_dict(self, message: Message) -> Dict[str, Any]:
        """Convert Message object to dictionary for storage"""
        return {
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "sender_id": message.sender_id,
            "conversation_id": message.conversation_id,
            "message_type": message.message_type.value,
            "metadata": message.metadata
        }