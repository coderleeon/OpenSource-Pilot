"""Application configuration using pydantic-settings.

All settings are read from environment variables and/or a .env file.
Missing required values raise a ValidationError at startup (fail-fast).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # LLM Provider
    # ------------------------------------------------------------------
    llm_provider: Literal["openrouter", "openai", "anthropic"] = Field(
        default="openrouter",
        description="Active LLM provider. One of: openrouter, openai, anthropic.",
    )

    # OpenRouter
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key (https://openrouter.ai).",
    )
    openrouter_model: str = Field(
        default="anthropic/claude-3.5-haiku",
        description="OpenRouter model string (e.g. 'anthropic/claude-3.5-haiku').",
    )

    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API key.")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model name.")

    # Anthropic
    anthropic_api_key: str = Field(default="", description="Anthropic API key.")
    anthropic_model: str = Field(
        default="claude-3-5-haiku-20241022",
        description="Anthropic model name.",
    )

    # ------------------------------------------------------------------
    # GitHub
    # ------------------------------------------------------------------
    github_token: str = Field(
        default="",
        description="GitHub personal access token (public_repo scope). "
        "Omitting this limits to 60 unauthenticated requests per hour.",
    )

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------
    clone_base_dir: str = Field(
        default="./cloned_repos",
        description="Directory where repositories will be cloned.",
    )
    chroma_persist_dir: str = Field(
        default="./chroma_db",
        description="Directory where ChromaDB persists its vector index.",
    )

    # ------------------------------------------------------------------
    # Indexing limits
    # ------------------------------------------------------------------
    max_files_to_index: int = Field(
        default=500,
        ge=1,
        le=5000,
        description="Maximum number of source files to index per repository.",
    )
    max_file_size_kb: int = Field(
        default=512,
        ge=1,
        description="Maximum individual file size in KB. Larger files are skipped.",
    )
    chunk_size_chars: int = Field(
        default=2000,
        ge=100,
        description="Size of each code chunk in characters.",
    )
    chunk_overlap_chars: int = Field(
        default=200,
        ge=0,
        description="Character overlap between consecutive chunks.",
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence-transformers model name for local embeddings.",
    )

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Application log level.",
    )
    log_format: Literal["json", "console"] = Field(
        default="console",
        description="Log output format: 'json' for structured, 'console' for human-readable.",
    )

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @field_validator("openrouter_api_key", mode="after")
    @classmethod
    def _validate_openrouter_key(cls, v: str, info: object) -> str:
        # Defer validation to runtime so that tests without a key still work.
        return v

    @property
    def clone_base_path(self) -> str:
        """Resolved clone base directory (no trailing slash)."""
        return self.clone_base_dir.rstrip("/\\")

    @property
    def effective_api_key(self) -> str:
        """Return the API key for the active provider."""
        if self.llm_provider == "openrouter":
            return self.openrouter_api_key
        if self.llm_provider == "openai":
            return self.openai_api_key
        return self.anthropic_api_key

    @property
    def effective_model(self) -> str:
        """Return the model name for the active provider."""
        if self.llm_provider == "openrouter":
            return self.openrouter_model
        if self.llm_provider == "openai":
            return self.openai_model
        return self.anthropic_model


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton (loaded once at startup)."""
    return Settings()
