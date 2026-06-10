"""Anthropic (Claude) LLM client implementation."""

from __future__ import annotations

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import ConfigurationError, LLMError
from app.core.logging import get_logger
from app.llm.base import LLMClient

logger = get_logger(__name__)


class AnthropicClient(LLMClient):
    """LLM client backed by the Anthropic Messages API.

    Args:
        api_key: Anthropic API key (``sk-ant-...``).
        model: Anthropic model name (e.g. ``"claude-3-5-haiku-20241022"``).

    Raises:
        ConfigurationError: If *api_key* is empty.
    """

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY is not set",
                details="Set ANTHROPIC_API_KEY in your .env file or environment.",
            )
        self._model = model
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        logger.info("anthropic_client_ready", model=model)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        retry=retry_if_exception_type(
            (anthropic.RateLimitError, anthropic.APITimeoutError, anthropic.APIConnectionError)
        ),
        reraise=True,
    )
    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> str:
        """Send a message to the Anthropic Messages API.

        Note: Anthropic's API uses a separate ``system`` parameter (not a
        system message in the messages array), so it maps cleanly here.
        """
        try:
            kwargs: dict = {
                "model": self._model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system

            response = await self._client.messages.create(**kwargs)
            return response.content[0].text if response.content else ""
        except (
            anthropic.RateLimitError,
            anthropic.APITimeoutError,
            anthropic.APIConnectionError,
        ):
            raise
        except anthropic.AuthenticationError as exc:
            raise ConfigurationError(
                "Anthropic authentication failed — check ANTHROPIC_API_KEY",
                details=str(exc),
            ) from exc
        except anthropic.AnthropicError as exc:
            raise LLMError(
                f"Anthropic API error with model {self._model!r}",
                details=str(exc),
            ) from exc
