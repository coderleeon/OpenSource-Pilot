"""LLM client factory.

Reads ``LLM_PROVIDER`` from settings and instantiates the appropriate
concrete ``LLMClient`` implementation.  Raises ``ConfigurationError``
immediately if the required API key is not set.
"""

from __future__ import annotations

from app.core.exceptions import ConfigurationError
from app.core.logging import get_logger
from app.llm.anthropic_client import AnthropicClient
from app.llm.base import LLMClient
from app.llm.openai_client import OpenAIClient
from app.llm.openrouter_client import OpenRouterClient

logger = get_logger(__name__)


def create_llm_client(
    provider: str,
    openrouter_api_key: str = "",
    openrouter_model: str = "anthropic/claude-3.5-haiku",
    openai_api_key: str = "",
    openai_model: str = "gpt-4o-mini",
    anthropic_api_key: str = "",
    anthropic_model: str = "claude-3-5-haiku-20241022",
) -> LLMClient:
    """Construct and return the appropriate ``LLMClient`` for *provider*.

    Args:
        provider: One of ``"openrouter"``, ``"openai"``, or ``"anthropic"``.
        openrouter_api_key: OpenRouter API key.
        openrouter_model: OpenRouter model string.
        openai_api_key: OpenAI API key.
        openai_model: OpenAI model name.
        anthropic_api_key: Anthropic API key.
        anthropic_model: Anthropic model name.

    Returns:
        Configured ``LLMClient`` instance.

    Raises:
        ConfigurationError: If *provider* is unknown or the required key is missing.
    """
    logger.info("creating_llm_client", provider=provider)

    if provider == "openrouter":
        return OpenRouterClient(api_key=openrouter_api_key, model=openrouter_model)

    if provider == "openai":
        return OpenAIClient(api_key=openai_api_key, model=openai_model)

    if provider == "anthropic":
        return AnthropicClient(api_key=anthropic_api_key, model=anthropic_model)

    raise ConfigurationError(
        f"Unknown LLM_PROVIDER: {provider!r}",
        details="Valid options: openrouter, openai, anthropic",
    )


def create_llm_client_from_settings(settings: object) -> LLMClient:  # type: ignore[type-arg]
    """Convenience factory that reads all values from a ``Settings`` instance.

    Args:
        settings: A ``Settings`` object (from ``app.config``).

    Returns:
        Configured ``LLMClient`` instance.
    """
    return create_llm_client(
        provider=getattr(settings, "llm_provider", "openrouter"),
        openrouter_api_key=getattr(settings, "openrouter_api_key", ""),
        openrouter_model=getattr(settings, "openrouter_model", "anthropic/claude-3.5-haiku"),
        openai_api_key=getattr(settings, "openai_api_key", ""),
        openai_model=getattr(settings, "openai_model", "gpt-4o-mini"),
        anthropic_api_key=getattr(settings, "anthropic_api_key", ""),
        anthropic_model=getattr(settings, "anthropic_model", "claude-3-5-haiku-20241022"),
    )
