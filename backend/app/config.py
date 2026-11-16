"""Application configuration loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration. Secrets live in env vars / .env, never in code."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"

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

    # --- App / security ---
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    # If set, every /api/v1 request must send this value as `X-Api-Key` or
    # `Authorization: Bearer <token>`. Empty = auth disabled (dev/test).
    adrobot_api_token: str = ""
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 120

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

    @property
    def auth_enabled(self) -> bool:
        return bool(self.adrobot_api_token)

    def check_secrets(self) -> None:
        """Fail fast when a required secret is missing (never in tests)."""
        if not self.keitaro_api_token:
            raise RuntimeError(
                "KEITARO_API_TOKEN is not set. Configure it in the environment or .env."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
