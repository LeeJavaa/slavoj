import asyncio
from typing import List

from slavoj.core.config import ProcessingConfig
from slavoj.core.exceptions import BookProcessingError
from slavoj.core.logging import LoggerFactory
from slavoj.domain.interfaces import (
    BookProcessorInterface,
    DatabaseInterface,
    LLMInterface,
)
from slavoj.domain.models import Book, ConversationContext, GeneratedResponse


class BookProcessor(BookProcessorInterface):
    def __init__(
        self, db: DatabaseInterface, llm: LLMInterface, config: ProcessingConfig
    ):
        self.db = db
        self.llm = llm
        self.config = config
        self.logger = LoggerFactory.create_logger("BookProcessor")

    async def process_query(
        self, query: str, author: str, conversation_context: ConversationContext
    ) -> List[GeneratedResponse]:
        try:
            # Get all books for the author
            books = await self.db.get_books_by_author(author)
            if not books:
                self.logger.warning(f"No books found for author: {author}")
                return []

            # Process books in parallel with concurrency limit
            semaphore = asyncio.Semaphore(self.config.max_concurrent_books)
            tasks = [
                self._process_book_with_semaphore(
                    book, conversation_context, query, semaphore
                )
                for book in books
            ]

            responses = await asyncio.gather(*tasks)
            return [
                r for r in responses if r is not None
            ]  # Filter out any failed responses

        except Exception as e:
            self.logger.error(f"Book processing failed: {e}")
            raise BookProcessingError(f"Failed to process books: {e}")

    async def process_single_book(
        self, book: Book, conversation_context: ConversationContext, query: str
    ) -> GeneratedResponse:
        try:
            response = await self.llm.generate_response(
                book_title=book.title,
                book_content=book.content,
                conversation_context=conversation_context,
                query=query,
            )
            return response
        except Exception as e:
            self.logger.error(f"Single book processing failed: {e}")
            raise BookProcessingError(f"Failed to process book {book.title}: {e}")

    async def _process_book_with_semaphore(
        self,
        book: Book,
        conversation_context: ConversationContext,
        query: str,
        semaphore: asyncio.Semaphore,
    ) -> GeneratedResponse:
        """Process a single book with semaphore for concurrency control"""
        async with semaphore:
            try:
                return await asyncio.wait_for(
                    self.process_single_book(book, conversation_context, query),
                    timeout=self.config.response_timeout,
                )
            except asyncio.TimeoutError:
                self.logger.error(f"Processing timed out for book: {book.title}")
                return None
            except Exception as e:
                self.logger.error(f"Error processing book {book.title}: {e}")
                return None
