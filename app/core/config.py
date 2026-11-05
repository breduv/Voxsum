from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        hide_input_in_errors=True,
    )

    bot_token: SecretStr

    api_base: str
    api_key: SecretStr | None = Field(default=None)

    llm_model: str
    asr_model: Literal[
        "gigaam-v3-e2e-rnnt",
        "gigaam-v3-e2e-ctc",
    ] = "gigaam-v3-e2e-rnnt"

    proxy: SecretStr | None = Field(default=None)
    tg_proxy: SecretStr | None = Field(default=None)

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = Field(default="INFO")

    metrics_port: int = Field(default=9103, ge=1, le=65535)
    telegram_health_interval_seconds: int = Field(default=30, ge=10, le=300)

    @field_validator("proxy", "tg_proxy", mode="before")
    @classmethod
    def empty_value_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
