"""Application configuration utilities."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Container for runtime configuration sourced from environment variables."""

    database_url: str = Field(
        default="sqlite:///" + str(Path("data") / "videoreduce.db"),
        description="SQLAlchemy database URL. Defaults to a local SQLite file.",
    )
    input_dir: Path = Field(
        default=Path("data") / "input",
        description="Directory where the service watches for uploaded originals and manifests.",
    )
    output_dir: Path = Field(
        default=Path("data") / "output",
        description="Directory where transcoded outputs are written.",
    )
    poll_interval_seconds: int = Field(
        default=30,
        description="Polling frequency for queue processing tasks.",
        ge=1,
        le=300,
    )
    jwt_secret_key: str = Field(
        default="change-me",
        description="Secret used to sign JWT session tokens.",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm.")
    jwt_expiration_minutes: int = Field(
        default=120,
        description="Number of minutes a session token remains valid.",
        ge=5,
    )
    admin_username: str = Field(..., description="Dashboard administrator username.")
    admin_password: str = Field(..., description="Dashboard administrator password.")
    handbrake_cli_path: str = Field(
        default="HandBrakeCLI",
        description="Path to the HandBrakeCLI binary used for transcoding.",
    )
    queue_log_retention: int = Field(
        default=90,
        description="Number of days to retain job events before archival.",
        ge=1,
    )

    class Config:
        env_prefix = "VIDEOR_"
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""

    settings = Settings()
    settings.input_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    return settings
