from motor.motor_asyncio import AsyncIOMotorClient
from config import get_settings

settings = get_settings()

# MongoDB client — created once, reused across requests
client: AsyncIOMotorClient = None
db = None


async def connect_db():
    """Open MongoDB connection — called on app startup."""
    global client, db
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    print(f"✅ Connected to MongoDB — database: '{settings.database_name}'")


async def close_db():
    """Close MongoDB connection — called on app shutdown."""
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed.")


def get_db():
    """Return the active database instance."""
    return db


# ── Collection helpers ─────────────────────────────────────────────────────────

def get_users_collection():
    return db["users"]


def get_documents_collection():
    return db["documents"]


def get_history_collection():
    return db["query_history"]