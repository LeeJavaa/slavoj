from datetime import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from slavoj.core.exceptions import DatabaseError
from slavoj.core.logging import LoggerFactory
from slavoj.domain.interfaces import DatabaseInterface
from slavoj.domain.models import Author, Book, ConversationContext, Message, MessageType
from slavoj.utils.mongodb import strip_mongo_id


class MongoDB(DatabaseInterface):
    def __init__(self, connection_string: str, database: str):
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client[database]
        self.logger = LoggerFactory.create_logger("MongoDB")

    async def get_books_by_author(self, author: str) -> List[Book]:
        try:
            cursor = self.db.books.find({"author": author})
            books = await cursor.to_list(length=None)

            return [Book(**strip_mongo_id(book)) for book in books]
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
            author_doc["books"] = books

            return Author(**strip_mongo_id(author_doc))
        except Exception as e:
            self.logger.error(f"Failed to retrieve author: {e}")
            raise DatabaseError(f"Failed to retrieve author: {e}")

    async def get_author_by_whatsapp(self, whatsapp_number: str) -> Optional[
        Author]:
        try:
            author_doc = await self.db.authors.find_one(
                {"whatsapp_number": whatsapp_number})
            if not author_doc:
                return None

            # Get books for this author
            books = await self.get_books_by_author(author_doc["name"])
            author_doc["books"] = books

            return Author(**strip_mongo_id(author_doc))
        except Exception as e:
            self.logger.error(
                f"Failed to retrieve author by WhatsApp number: {e}")
            raise DatabaseError(
                f"Failed to retrieve author by WhatsApp number: {e}")

    async def get_conversation_context(
        self, conversation_id: str
    ) -> Optional[ConversationContext]:
        try:
            context = await self.db.conversations.find_one({"id": conversation_id})
            if not context:
                return None

            # Convert stored dates back to datetime objects
            context["created_at"] = datetime.fromisoformat(context["created_at"])
            context["last_updated"] = datetime.fromisoformat(context["last_updated"])

            # Convert message dictionaries to Message objects
            context["messages"] = [Message(**strip_mongo_id(msg)) for msg in context["messages"]]

            return ConversationContext(**strip_mongo_id(context))
        except Exception as e:
            self.logger.error(f"Failed to retrieve conversation: {e}")
            raise DatabaseError(f"Failed to retrieve conversation: {e}")

    async def store_conversation(self, conversation: ConversationContext) -> bool:
        try:
            # Convert datetime objects to ISO format strings for storage
            conversation_dict = {
                "id": conversation.id,
                "user_id": conversation.user_id,
                "author_id": conversation.author_id,
                "messages": [
                    Message.message_to_dict(msg) for msg in conversation.messages
                ],
                "created_at": conversation.created_at.isoformat(),
                "last_updated": conversation.last_updated.isoformat(),
                "metadata": conversation.metadata,
            }

            result = await self.db.conversations.insert_one(conversation_dict)
            self.logger.info(f"Stored conversation: {result.inserted_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store conversation: {e}")
            raise DatabaseError(f"Failed to store conversation: {e}")

    async def update_conversation(self, conversation: ConversationContext) -> bool:
        try:
            conversation_dict = {
                "user_id": conversation.user_id,
                "author_id": conversation.author_id,
                "messages": [
                    Message.message_to_dict(msg) for msg in conversation.messages
                ],
                "last_updated": conversation.last_updated.isoformat(),
                "metadata": conversation.metadata,
            }

            result = await self.db.conversations.update_one(
                {"id": conversation.id}, {"$set": conversation_dict}
            )

            if result.modified_count == 0:
                raise DatabaseError(f"No conversation found with id: {conversation.id}")

            self.logger.info(f"Updated conversation: {conversation.id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update conversation: {e}")
            raise DatabaseError(f"Failed to update conversation: {e}")

    async def store_message(self, message: Message) -> bool:
        try:
            message_dict = Message.message_to_dict(message)
            result = await self.db.messages.insert_one(message_dict)
            self.logger.info(f"Stored message: {result.inserted_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store message: {e}")
            raise DatabaseError(f"Failed to store message: {e}")
