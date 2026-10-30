import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()


@dataclass
class Settings:
    PROJECT_NAME: str = "VeraDocs Intelligence Platform"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL & pgvector Database Settings
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "veradocs_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "veradocs_password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "veradocs_db")

    # Embedding dimension for vector operations (e.g. OpenAI ada-002/3-small is 1536)
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "1536"))

    # Security & Auth Settings
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "veradocs-platform-super-secret-key-32chars"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    @property
    def DATABASE_URL(self) -> str:
        url = os.getenv("DATABASE_URL")
        if url:
            return url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        url = os.getenv("SYNC_DATABASE_URL")
        if url:
            return url
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
