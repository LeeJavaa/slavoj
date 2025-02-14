import argparse
import json
from pathlib import Path
from typing import Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from slavoj.core.config import ConfigLoader
from slavoj.core.logging import LoggerFactory
from slavoj.utils.pdf import extract_text_from_pdf

logger = LoggerFactory.create_logger("BooksSetup")


async def setup_books(
        mongodb_uri: str,
        database: str,
        author: str,
        books_dir: str,
        metadata_file: Optional[str] = None
) -> bool:
    """
    Set up books for an author in the MongoDB database.

    Args:
        mongodb_uri: MongoDB connection URI
        database: Database name
        author: Author name
        books_dir: Directory containing book PDFs
        metadata_file: Optional path to JSON metadata file with book metadata
    """
    try:
        # Initialize MongoDB client
        client = AsyncIOMotorClient(mongodb_uri)
        db = client[database]

        # Verify author exists
        author_doc = await db.authors.find_one({"name": author})
        if not author_doc:
            logger.error(f"Author {author} not found in database")
            return False

        # Load book metadata if provided
        book_metadata = {}
        if metadata_file:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                book_metadata = metadata.get("books", {})

        # Process books
        books_path = Path(books_dir)
        pdf_files = list(books_path.glob("*.pdf"))

        if not pdf_files:
            logger.error(f"No PDF files found in {books_dir}")
            return False

        success_count = 0
        for pdf_file in pdf_files:
            book_title = pdf_file.stem

            # Extract text content
            content = extract_text_from_pdf(str(pdf_file))
            if not content:
                logger.error(f"Failed to extract content from {pdf_file}")
                continue

            # Get book metadata if available
            metadata = book_metadata.get(book_title, {})

            # Create book document
            book_doc = {
                "title": book_title,
                "content": content,
                "author": author,
                "publication_year": metadata.get("publication_year"),
                "metadata": metadata.get("metadata", {})
            }

            # Insert or update book
            result = await db.books.update_one(
                {"title": book_title, "author": author},
                {"$set": book_doc},
                upsert=True
            )

            if result.modified_count > 0:
                logger.info(f"Updated existing book: {book_title}")
                success_count += 1
            elif result.upserted_id:
                logger.info(f"Created new book: {book_title}")
                success_count += 1

        logger.info(
            f"Successfully processed {success_count} out of {len(pdf_files)} books")
        return success_count > 0

    except Exception as e:
        logger.error(f"Error setting up books: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Set up books in MongoDB")

    parser.add_argument("--author", required=True, help="Author name")
    parser.add_argument("--books-dir", required=True,
                        help="Directory containing book PDFs")
    parser.add_argument("--metadata", help="Path to JSON metadata file")
    parser.add_argument("--config", help="Path to config file",
                        default="config.dev.yaml")

    args = parser.parse_args()

    # Load configuration
    config_loader = ConfigLoader(args.config)
    config = config_loader.load_config()

    # Run setup
    import asyncio
    success = asyncio.run(setup_books(
        mongodb_uri=config.mongodb.connection_string,
        database=config.mongodb.database,
        author=args.author,
        books_dir=args.books_dir,
        metadata_file=args.metadata
    ))

    if success:
        logger.info("Books setup completed successfully")
    else:
        logger.error("Books setup failed")
        exit(1)


if __name__ == "__main__":
    main()