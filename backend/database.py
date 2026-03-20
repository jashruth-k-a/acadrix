from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from config import get_settings

settings = get_settings()

client: AsyncIOMotorClient = None
db = None
fs: AsyncIOMotorGridFSBucket = None


async def connect_db():
    global client, db, fs
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    fs = AsyncIOMotorGridFSBucket(db, bucket_name="faiss_indexes")
    print(f"✅ Connected to MongoDB — database: '{settings.database_name}'")


async def close_db():
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed.")


def get_db():
    return db


def get_fs():
    return fs


def get_users_collection():
    return db["users"]


def get_documents_collection():
    return db["documents"]


def get_history_collection():
    return db["query_history"]