from typing import Optional
from datetime import datetime

from slavoj.domain.interfaces import MessagingInterface
from slavoj.domain.models import Message, MessageType
from slavoj.core.exceptions import MessageDeliveryError
from slavoj.core.logging import LoggerFactory


class MessagingService:
    def __init__(self, messaging_adapter: MessagingInterface):
        self.adapter = messaging_adapter
        self.logger = LoggerFactory.create_logger("MessagingService")

    async def send_message(self, content: str, recipient_id: str,
                           conversation_id: str) -> bool:
        """Send a message to a user"""
        try:
            message = Message(
                content=content,
                timestamp=datetime.utcnow(),
                sender_id=recipient_id,
                # For Twilio, this is the recipient's phone number
                conversation_id=conversation_id,
                message_type=MessageType.AUTHOR
            )

            return await self.adapter.send_message(message)

        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise MessageDeliveryError(f"Failed to send message: {e}")

    async def process_incoming_message(self,
                                       content: str,
                                       sender_id: str,
                                       conversation_id: Optional[
                                           str] = None) -> Message:
        """Process an incoming message from Twilio webhook"""
        try:
            message = Message(
                content=content,
                timestamp=datetime.utcnow(),
                sender_id=sender_id,
                conversation_id=conversation_id or str(sender_id),
                # Use sender_id as conversation_id if none provided
                message_type=MessageType.USER
            )

            self.logger.info(f"Processed incoming message from {sender_id}")
            return message

        except Exception as e:
            self.logger.error(f"Failed to process incoming message: {e}")
            raise MessageDeliveryError(
                f"Failed to process incoming message: {e}")

    async def handle_delivery_status(self, message_id: str,
                                     status: str) -> None:
        """Handle message delivery status updates"""
        try:
            await self.adapter.handle_delivery_status(message_id, status)
        except Exception as e:
            self.logger.error(f"Failed to handle delivery status: {e}")
            raise MessageDeliveryError(f"Failed to handle delivery status: {e}")
