"""
config/settings.py
------------------
Single source of truth for all environment variables.
Uses pydantic-settings so every value is type-checked at startup.
Swap-compatible: change LLM_PROVIDER to "ollama" when self-hosting.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Database ─────────────────────────────────────────────────
    MONGO_URI: str
    DB_NAME: str = "mockDB"
    COLLECTION_NAME: str = "userGoals"

    # ── Auth ─────────────────────────────────────────────────────
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── LLM (swap provider without touching any other file) ──────
    LLM_PROVIDER: str = "groq"           # "groq" | "ollama" | "openai"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # ── Vector Store ─────────────────────────────────────────────
    VECTOR_PROVIDER: str = "chroma"      # "chroma" | "pinecone" | "qdrant"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION: str = "finpass_docs"

    # ── Embeddings ───────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # local sentence-transformer

    # ── App ──────────────────────────────────────────────────────
    PORT: int = 7860
    ENV: str = "production"             # "development" | "production"
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — import this everywhere."""
    return Settings()
