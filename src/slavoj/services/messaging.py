from datetime import datetime
from typing import Optional

from slavoj.core.exceptions import MessageDeliveryError
from slavoj.core.logging import LoggerFactory
from slavoj.domain.interfaces import MessagingInterface
from slavoj.domain.models import Message, MessageType


class MessagingService:
    def __init__(self, messaging_adapter: MessagingInterface):
        self.adapter = messaging_adapter
        self.logger = LoggerFactory.create_logger("MessagingService")

    def send_message(
        self, content: str, recipient_id: str, sender_id: str, conversation_id: str
    ) -> bool:
        """Send a message to a user"""
        try:
            message = Message(
                content=content,
                timestamp=datetime.utcnow(),
                sender_id=sender_id,
                recipient_id=recipient_id,
                conversation_id=conversation_id,
                message_type=MessageType.AUTHOR,
            )

            return self.adapter.send_message(message)

        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise MessageDeliveryError(f"Failed to send message: {e}")

    async def process_incoming_message(
        self, content: str, sender_id: str, recipient_id: str,
    ) -> Message:
        """Process an incoming message from Twilio webhook"""
        conversation_id = self._generate_conversation_id(sender_id,
                                                         recipient_id)

        try:
            message = Message(
                content=content,
                timestamp=datetime.utcnow(),
                sender_id=sender_id,
                recipient_id=recipient_id,
                conversation_id=conversation_id,
                message_type=MessageType.USER,
            )

            self.logger.info(f"Processed incoming message from {sender_id}")
            return message

        except Exception as e:
            self.logger.error(f"Failed to process incoming message: {e}")
            raise MessageDeliveryError(f"Failed to process incoming message: {e}")

    async def handle_delivery_status(self, message_id: str, status: str) -> None:
        """Handle message delivery status updates"""
        try:
            await self.adapter.handle_delivery_status(message_id, status)
        except Exception as e:
            self.logger.error(f"Failed to handle delivery status: {e}")
            raise MessageDeliveryError(f"Failed to handle delivery status: {e}")

    def _generate_conversation_id(self, user_number: str,
                                  author_number: str) -> str:
        """Generate a unique conversation ID from user and author numbers"""
        # Sort numbers to ensure consistency regardless of order
        return f"{user_number}:{author_number}"