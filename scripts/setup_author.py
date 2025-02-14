import argparse
import json

from motor.motor_asyncio import AsyncIOMotorClient

from slavoj.core.config import ConfigLoader
from slavoj.core.logging import LoggerFactory

logger = LoggerFactory.create_logger("AuthorSetup")


async def setup_author(
        mongodb_uri: str,
        database: str,
        author: str,
        metadata_file: str,
) -> bool:
    """
    Set up an author in the MongoDB database.

    Args:
        mongodb_uri: MongoDB connection URI
        database: Database name
        author: Author name
        metadata_file: Path to JSON metadata file
    """
    try:
        # Initialize MongoDB client
        client = AsyncIOMotorClient(mongodb_uri)
        db = client[database]

        # Load author metadata
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        # Set up author document
        author_doc = {
            "name": author,
            "conversation_style": metadata.get("conversation_style", {}),
            "bio": metadata.get("bio", ""),
            "metadata": metadata.get("author_metadata", {})
        }

        # Insert or update author
        result = await db.authors.update_one(
            {"name": author},
            {"$set": author_doc},
            upsert=True
        )

        if result.modified_count > 0:
            logger.info(f"Updated existing author: {author}")
        elif result.upserted_id:
            logger.info(f"Created new author: {author}")

        return True

    except Exception as e:
        logger.error(f"Error setting up author: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Set up author in MongoDB")

    parser.add_argument("--author", required=True, help="Author name")
    parser.add_argument("--metadata", required=True,
                        help="Path to JSON metadata file")
    parser.add_argument("--config", help="Path to config file",
                        default="config.dev.yaml")

    args = parser.parse_args()

    # Load configuration
    config_loader = ConfigLoader(args.config)
    config = config_loader.load_config()

    # Run setup
    import asyncio
    success = asyncio.run(setup_author(
        mongodb_uri=config.mongodb.connection_string,
        database=config.mongodb.database,
        author=args.author,
        metadata_file=args.metadata
    ))

    if success:
        logger.info("Author setup completed successfully")
    else:
        logger.error("Author setup failed")
        exit(1)


if __name__ == "__main__":
    main()