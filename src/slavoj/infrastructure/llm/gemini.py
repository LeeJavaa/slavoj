from datetime import datetime
from typing import List

import google.generativeai as genai

from slavoj.core.config import LLMConfig
from slavoj.core.exceptions import LLMError
from slavoj.core.logging import LoggerFactory
from slavoj.domain.interfaces import LLMInterface
from slavoj.domain.models import ConversationContext, GeneratedResponse


class GeminiLLM(LLMInterface):
    def __init__(self, config: LLMConfig):
        self.config = config
        genai.configure(api_key=config.api_key)
        self.model = genai.GenerativeModel(
            model_name=config.model,
            generation_config={
                "temperature": config.temperature,
                "max_output_tokens": config.max_tokens,
            },
        )
        self.logger = LoggerFactory.create_logger("GeminiLLM")

    async def generate_response(
        self, book_title: str, book_content: str, conversation_context: ConversationContext, query: str
    ) -> GeneratedResponse:
        try:
            # Construct prompt with book content and conversation history
            prompt = self._construct_prompt(book_content, conversation_context, query)

            # Generate response
            response = self.model.generate_content(prompt)

            return GeneratedResponse(
                book_title=book_title,
                content=response.text,
                confidence_score=0.0,
                # Gemini doesn't provide confidence scores
                generation_time=datetime.utcnow(),
            )
        except Exception as e:
            self.logger.error(f"Gemini generation failed: {e}")
            raise LLMError(f"Failed to generate response: {e}")

    async def aggregate_responses(
        self, responses: List[GeneratedResponse], query: str
    ) -> str:
        try:
            # Construct aggregation prompt
            prompt = self._construct_aggregation_prompt(responses, query)

            # Generate aggregated response
            response = self.model.generate_content(prompt)

            return response.text
        except Exception as e:
            self.logger.error(f"Response aggregation failed: {e}")
            raise LLMError(f"Failed to aggregate responses: {e}")

    async def validate_response(self, response: str) -> bool:
        """Basic validation of response content"""
        if not response or len(response.strip()) < 10:
            return False
        return True

    def _construct_prompt(
        self, book_content: str, conversation_context: ConversationContext, query: str
    ) -> str:
        """Construct prompt for single-book response generation"""
        conversation_history = "\n".join(
            [
                f"{msg.sender_id}: {msg.content}"
                for msg in conversation_context.messages[-5:]  # Last 5 messages
            ]
        )

        return f"""
        You are helping to simulate a conversation with {conversation_context.author_id}.

        Book Content:
        {book_content}

        Previous Conversation:
        {conversation_history}

        Current Query:
        {query}

        Generate a response in the style of {conversation_context.author_id} 
        based on the ideas present in this specific book.
        """

    def _construct_aggregation_prompt(
        self, responses: List[GeneratedResponse], query: str
    ) -> str:
        """Construct prompt for response aggregation"""
        formatted_responses = "\n\n".join(
            [f"From {r.book_title}:\n{r.content}" for r in responses]
        )

        return f"""
        The following are different responses to the query: "{query}"
        Each response is generated based on a different book by the author.

        {formatted_responses}
        
        You are the author that wrote these books and a curious mind is having a 
        conversation with you over text. You must synthesize these responses and
        respond to this person over text.

        Please synthesize these responses into a single, coherent response that:
        1. Looks at the key ideas from all books and picks the most relevant one, or summarises them. 
        2. Maintains the author's voice and style
        3. Presents a unified perspective
        4. Mentions the relevant books only when absolutely necessary. 
        5. Is not longer than 1000 characters!
        6. Does not have mutliple paragraphs with gaps. Is only a single paragraph.
        7. Medium response length (400-800) characters preferred.
        8. Do not detail the actions or motions you are performing, this is a text message.

        Synthesized response:
        """
