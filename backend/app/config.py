"""Application configuration loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration. Secrets live in env vars / .env, never in code."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "dev"

    # --- Keitaro integration ---
    keitaro_base_url: str = "https://tlgk.host/admin_api/v1"
    keitaro_api_token: str = ""
    keitaro_timeout: float = 30.0
    keitaro_max_retries: int = 3
    # Keitaro entity ids used by the campaign creator (kept out of business logic).
    keitaro_traffic_source_id: int = 836
    keitaro_group_id: int = 10332
    keitaro_group_type: str = "campaigns"
    google_redirect_url: str = "https://google.com"
    default_offer_share: int = 100

    # --- PostgreSQL ---
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "adrobot"
    postgres_user: str = "adrobot"
    postgres_password: str = "adrobot"

    # --- RabbitMQ ---
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "adrobot"
    rabbitmq_password: str = "adrobot"
    rabbitmq_vhost: str = "/"

    # --- App ---
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
