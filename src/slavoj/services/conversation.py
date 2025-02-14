import uuid
from datetime import datetime

from slavoj.core.exceptions import ConversationError
from slavoj.core.logging import LoggerFactory
from slavoj.domain.interfaces import (
    BookProcessorInterface,
    ConversationManagerInterface,
    DatabaseInterface,
    LLMInterface,
)
from slavoj.domain.models import ConversationContext, Message, MessageType


class ConversationManager(ConversationManagerInterface):
    def __init__(
        self,
        db: DatabaseInterface,
        book_processor: BookProcessorInterface,
        llm: LLMInterface,
    ):
        self.db = db
        self.book_processor = book_processor
        self.llm = llm
        self.logger = LoggerFactory.create_logger("ConversationManager")

    async def process_message(self, message: Message) -> str:
        try:
            # Get or create conversation context
            context = await self.get_or_create_context(message.conversation_id)

            # Process query against all books
            responses = await self.book_processor.process_query(
                query=message.content,
                author=context.author_id,
                conversation_context=context,
            )

            if not responses:
                raise ConversationError("No responses generated from books")

            # Aggregate responses
            final_response = await self.llm.aggregate_responses(
                responses=responses, query=message.content
            )

            # Update conversation context
            await self.update_context(context, message, final_response)

            return final_response

        except Exception as e:
            self.logger.error(f"Message processing failed: {e}")
            raise ConversationError(f"Failed to process message: {e}")

    async def get_or_create_context(self, conversation_id: str) -> ConversationContext:
        try:
            # Try to get existing context
            context = await self.db.get_conversation_context(conversation_id)
            if context:
                return context

            # Create new context if none exists
            new_context = ConversationContext(
                id=conversation_id or str(uuid.uuid4()),
                user_id="",  # Will be set from first message
                author_id="",  # Will be set from configuration
                messages=[],
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow(),
            )

            await self.db.store_conversation(new_context)
            return new_context

        except Exception as e:
            self.logger.error(f"Failed to get/create conversation context: {e}")
            raise ConversationError(f"Failed to get/create conversation context: {e}")

    async def update_context(
        self, context: ConversationContext, message: Message, response: str
    ) -> None:
        try:
            # Add user message to context
            context.messages.append(message)

            # Create and add response message
            response_message = Message(
                content=response,
                timestamp=datetime.utcnow(),
                sender_id=context.author_id,
                conversation_id=context.id,
                message_type=MessageType.AUTHOR,
            )
            context.messages.append(response_message)

            # Update last_updated timestamp
            context.last_updated = datetime.utcnow()

            # Store user message
            await self.db.store_message(message)

            # Store response message
            await self.db.store_message(response_message)

            # Update conversation context
            await self.db.update_conversation(context)

        except Exception as e:
            self.logger.error(f"Failed to update conversation context: {e}")
            raise ConversationError(f"Failed to update conversation context: {e}")
