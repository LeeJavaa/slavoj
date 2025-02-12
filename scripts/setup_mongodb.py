# scripts/setup_mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING

async def setup_collections(uri: str):
    client = AsyncIOMotorClient(uri)
    db = client.author_chat

    # Create collections
    await db.create_collection("books")
    await db.create_collection("conversations")

    # Create indexes
    await db.books.create_indexes([
        IndexModel([("author", ASCENDING)]),
        IndexModel([("title", ASCENDING)])
    ])

    await db.conversations.create_indexes([
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("author_id", ASCENDING)])
    ])

if __name__ == "__main__":
    import asyncio
    import os
    from dotenv import load_dotenv

    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    asyncio.run(setup_collections(uri))