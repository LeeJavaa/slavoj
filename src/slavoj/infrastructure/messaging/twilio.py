from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from datetime import datetime

from slavoj.domain.interfaces import MessagingInterface
from slavoj.domain.models import Message, MessageType
from slavoj.core.config import TwilioConfig
from slavoj.core.exceptions import MessageDeliveryError
from slavoj.core.logging import LoggerFactory

class TwilioAdapter(MessagingInterface):
    def __init__(self, config: TwilioConfig):
        self.config = config
        self.client = Client(config.account_sid, config.auth_token)
        self.logger = LoggerFactory.create_logger("TwilioAdapter")

    async def send_message(self, message: Message) -> bool:
        try:
            response = await self.client.messages.create(
                body=message.content,
                from_=f"whatsapp:{self.config.phone_number}",
                to=f"whatsapp:{message.sender_id}"
            )
            self.logger.info(f"Message sent successfully: {response.sid}")
            return True
        except TwilioRestException as e:
            self.logger.error(f"Failed to send message: {e}")
            raise MessageDeliveryError(f"Failed to send message: {e}")

    async def receive_message(self) -> Message:
        """
        Note: This method is typically not used directly.
        Messages are received via webhook endpoints.
        """
        raise NotImplementedError(
            "Messages should be received via webhook endpoints"
        )

    async def handle_delivery_status(self, message_id: str, status: str) -> None:
        try:
            self.logger.info(f"Message {message_id} status updated to: {status}")
            # Implement status handling logic here if needed
            pass
        except Exception as e:
            self.logger.error(f"Failed to handle delivery status: {e}")
            raise MessageDeliveryError(f"Failed to handle delivery status: {e}")