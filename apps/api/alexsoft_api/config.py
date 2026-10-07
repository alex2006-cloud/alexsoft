"""Service configuration. Source of truth: repo-root `.env` (see `.env.example`)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # service (BL listens on localhost only, ADR-0020)
    bl_host: str = "127.0.0.1"
    bl_port: int = 8100
    bl_daily_run_quota: int = 20
    bl_run_timeout_s: float = 120.0
    bl_max_input_chars: int = 8000

    # agents: LangGraph Agent Server (apps/agent1); BL calls it directly until RabbitMQ (stage 6)
    bl_agent_server_url: str = "http://127.0.0.1:2024"

    # IAM (Authentik). Issuer is what the browser-facing host puts into `iss`;
    # JWKS / API are fetched directly from the Authentik port (no gateway hop).
    auth_public_url: str = "http://auth.alexsoft.localhost:8000"
    authentik_port_http: int = 9100
    oidc_app_slug: str = "alexsoft-cabinet"
    oidc_client_id: str = "alexsoft-cabinet"
    bl_oidc_issuer: str = ""
    bl_jwks_url: str = ""
    bl_authentik_api_url: str = ""
    authentik_bl_token: str = ""
    bl_group_user: str = "alexsoft-users"
    bl_group_admin: str = "alexsoft-admins"

    # postgres (schema "bl" inside POSTGRES_DB)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "alexsoft"
    postgres_user: str = "alexsoft"
    postgres_password: str = "change-me"
    bl_database_url: str = ""

    @property
    def issuer(self) -> str:
        return self.bl_oidc_issuer or f"{self.auth_public_url.rstrip('/')}/application/o/{self.oidc_app_slug}/"

    @property
    def jwks_url(self) -> str:
        return self.bl_jwks_url or (
            f"http://127.0.0.1:{self.authentik_port_http}/application/o/{self.oidc_app_slug}/jwks/"
        )

    @property
    def authentik_api_url(self) -> str:
        return (self.bl_authentik_api_url or f"http://127.0.0.1:{self.authentik_port_http}/api/v3").rstrip("/")

    @property
    def database_dsn(self) -> str:
        if self.bl_database_url:
            return self.bl_database_url
        return (
            f"postgresql://{quote(self.postgres_user)}:{quote(self.postgres_password)}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
