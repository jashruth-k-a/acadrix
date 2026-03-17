from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str
    database_name: str = "acadrix"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Groq
    groq_api_key: str

    # File storage
    upload_dir: str = "uploads"
    max_file_size_mb: int = 20

    # FAISS index
    faiss_index_path: str = "faiss_index"

    # App
    app_name: str = "Acadrix"
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()