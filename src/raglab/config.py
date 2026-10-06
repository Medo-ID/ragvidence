"""Explicit environment configuration with secret values kept redacted."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAGLAB_", env_file=".env", extra="ignore")
    embedding_provider: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_base_url: str | None = None
    embedding_api_key: SecretStr | None = None
    generation_provider: str | None = None
    generation_model: str | None = None
    generation_base_url: str | None = None
    generation_api_key: SecretStr | None = None
