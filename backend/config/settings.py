"""
config/settings.py
------------------
Single source of truth for all environment variables.
Uses pydantic-settings when available; falls back to os.getenv silently.
"""
import os
from functools import lru_cache


try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")

        # ── Database ──────────────────────────────────────────────
        MONGO_URI: str = ""
        DB_NAME: str = "mockDB"
        COLLECTION_NAME: str = "userGoals"

        # ── Auth ──────────────────────────────────────────────────
        JWT_SECRET: str = "change-me-in-production"
        JWT_ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
        REFRESH_TOKEN_EXPIRE_DAYS: int = 7

        # ── LLM ───────────────────────────────────────────────────
        LLM_PROVIDER: str = "groq"
        GROQ_API_KEY: str = ""
        GROQ_MODEL: str = "llama-3.1-8b-instant"

        # ── Vector Store ──────────────────────────────────────────
        VECTOR_PROVIDER: str = "chroma"
        CHROMA_PERSIST_DIR: str = "./chroma_db"
        CHROMA_COLLECTION: str = "finpass_docs"

        # ── Embeddings ────────────────────────────────────────────
        EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

        # ── App ───────────────────────────────────────────────────
        PORT: int = 7860
        ENV: str = "production"
        LOG_LEVEL: str = "INFO"

    @lru_cache
    def get_settings() -> Settings:
        return Settings()

except ImportError:
    # pydantic-settings not installed — use a plain dataclass fallback
    class Settings:  # type: ignore[no-redef]
        MONGO_URI              = os.getenv("MONGO_URI", "")
        DB_NAME                = os.getenv("DB_NAME", "mockDB")
        COLLECTION_NAME        = os.getenv("COLLECTION_NAME", "userGoals")
        JWT_SECRET             = os.getenv("JWT_SECRET", "change-me-in-production")
        JWT_ALGORITHM          = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = 30
        REFRESH_TOKEN_EXPIRE_DAYS   = 7
        LLM_PROVIDER           = os.getenv("LLM_PROVIDER", "groq")
        GROQ_API_KEY           = os.getenv("GROQ_API_KEY", "")
        GROQ_MODEL             = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        VECTOR_PROVIDER        = "chroma"
        CHROMA_PERSIST_DIR     = "./chroma_db"
        CHROMA_COLLECTION      = "finpass_docs"
        EMBEDDING_MODEL        = "all-MiniLM-L6-v2"
        PORT                   = int(os.getenv("PORT", 7860))
        ENV                    = os.getenv("ENV", "production")
        LOG_LEVEL              = os.getenv("LOG_LEVEL", "INFO")

    @lru_cache
    def get_settings() -> Settings:
        return Settings()

