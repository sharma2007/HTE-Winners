from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = ""

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "doomlearn"
    postgres_user: str = "doomlearn"
    postgres_password: str = "doomlearn"

    # Redis/Celery
    redis_url: str = "redis://localhost:6379/0"

    # Storage (S3-compatible)
    s3_endpoint_url: str = "http://localhost:9000"
    s3_region: str = "us-east-1"
    s3_access_key_id: str = "minioadmin"
    s3_secret_access_key: str = "minioadmin"
    s3_bucket: str = "doomlearn"
    s3_public_base_url: str = "http://localhost:9000/doomlearn"

    # Auth / JWT
    jwt_secret: str = "dev-change-me"
    jwt_issuer: str = "doomlearn"
    jwt_audience: str = "doomlearn-mobile"
    auth_mock: bool = True
    google_client_id: str | None = None

    # MiniMax
    minimax_base_url: str = "https://api.minimax.chat"
    minimax_api_key: str | None = None
    minimax_mock: bool = True

    # Embeddings/RAG
    embeddings_mode: str = "mock"  # mock|local
    vector_dim: int = 384

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def cors_origins_list(self) -> list[str]:
        if not self.api_cors_origins.strip():
            return []
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


settings = Settings()

