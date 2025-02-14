import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from slavoj.core.config import AppConfig, ConfigLoader
from slavoj.core.exceptions import BaseError
from slavoj.core.logging import LoggerFactory
from slavoj.infrastructure.database.mongodb import MongoDB
from slavoj.infrastructure.llm.factory import LLMFactory
from slavoj.infrastructure.messaging.twilio import TwilioAdapter
from slavoj.services.book_processor import BookProcessor
from slavoj.services.conversation import ConversationManager
from slavoj.services.messaging import MessagingService

logger = LoggerFactory.create_logger("main")


class Application:
    def __init__(self):
        self.config: AppConfig = None
        self.db: MongoDB = None
        self.llm = None
        self.twilio_adapter = None
        self.book_processor = None
        self.conversation_manager = None
        self.messaging_service = None

    async def startup(self):
        """Initialize all application components"""
        try:
            # Load configuration
            config_loader = ConfigLoader()
            self.config = config_loader.load_config()

            # Initialize database
            self.db = MongoDB(
                self.config.mongodb.connection_string, self.config.mongodb.database
            )

            # Initialize LLM
            self.llm = LLMFactory.create_llm(self.config.llm)

            # Initialize Twilio adapter
            self.twilio_adapter = TwilioAdapter(self.config.twilio)

            # Initialize services
            self.book_processor = BookProcessor(
                self.db, self.llm, self.config.processing
            )

            self.conversation_manager = ConversationManager(
                self.db, self.book_processor, self.llm
            )

            self.messaging_service = MessagingService(self.twilio_adapter)

            logger.info("Application initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise


def create_app() -> FastAPI:
    """Factory function to create and initialize the FastAPI app"""
    app_instance = Application()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await app_instance.startup()
        yield

    # Create FastAPI instance with initialized app_instance
    app = FastAPI(title="Slavoj", lifespan=lifespan)

    # Register routes
    @app.post("/webhook/twilio")
    async def twilio_webhook(request: Request):
        """Handle incoming Twilio WhatsApp messages"""
        try:
            # Parse form data from Twilio
            form_data = await request.form()

            # Extract message details
            message_content = form_data.get("Body")
            sender_id = form_data.get("From").replace("whatsapp:", "")
            recipient_id = form_data.get("To").replace("whatsapp:", "")

            # Log incoming message
            logger.info(f"Received message from {sender_id}: {message_content}")

            # Process incoming message
            message = await app_instance.messaging_service.process_incoming_message(
                content=message_content,
                sender_id=sender_id,
                recipient_id=recipient_id
            )

            # Get response from conversation manager
            response = await app_instance.conversation_manager.process_message(message)

            # Send response back to user
            app_instance.messaging_service.send_message(
                content=response,
                recipient_id=sender_id,
                sender_id=recipient_id,
                conversation_id=message.conversation_id,
            )

            return Response(status_code=200)

        except BaseError as e:
            logger.error(f"Application error: {e}")
            return JSONResponse(status_code=400, content={"error": str(e)})
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return JSONResponse(
                status_code=500, content={"error": "Internal server error"}
            )

    @app.post("/webhook/status")
    async def status_webhook(request: Request):
        """Handle Twilio message status updates"""
        try:
            form_data = await request.form()
            message_id = form_data.get("MessageSid")
            status = form_data.get("MessageStatus")

            await app_instance.messaging_service.handle_delivery_status(
                message_id=message_id, status=status
            )

            return Response(status_code=200)

        except Exception as e:
            logger.error(f"Error handling status update: {e}")
            return JSONResponse(
                status_code=500, content={"error": "Internal server error"}
            )

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy"}

    return app


# Create the app
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("APP_ENVIRONMENT") == "development" else False,
    )
