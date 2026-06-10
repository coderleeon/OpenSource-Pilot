"""OpenRouter LLM client implementation.

OpenRouter (https://openrouter.ai) provides a unified OpenAI-compatible API
that routes requests to hundreds of models (Claude, Gemini, GPT-4, Mistral…).

This client uses the ``openai`` SDK with a custom base URL and HTTP headers,
which is the recommended OpenRouter integration approach.
"""

from __future__ import annotations

import openai
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

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_APP_SITE_URL = "https://github.com/opensourcepilot"
_APP_TITLE = "OpenSourcePilot"


class OpenRouterClient(LLMClient):
    """LLM client backed by the OpenRouter API.

    Args:
        api_key: OpenRouter API key (``sk-or-v1-...``).
        model: OpenRouter model string (e.g. ``"anthropic/claude-3.5-haiku"``).

    Raises:
        ConfigurationError: If *api_key* is empty.
    """

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ConfigurationError(
                "OPENROUTER_API_KEY is not set",
                details="Set OPENROUTER_API_KEY in your .env file or environment.",
            )
        self._model = model
        self._client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=_OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": _APP_SITE_URL,
                "X-Title": _APP_TITLE,
            },
        )
        logger.info("openrouter_client_ready", model=model)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        retry=retry_if_exception_type(
            (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError)
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
        """Send a chat completion request to OpenRouter.

        Retries up to 3 times on rate-limit / timeout / connection errors
        with exponential backoff (4 s → 8 s → 16 s, capped at 30 s).

        Args:
            prompt: User message.
            system: System prompt (instruction).
            temperature: Sampling temperature.
            max_tokens: Maximum completion tokens.

        Returns:
            Model response text.

        Raises:
            LLMError: After all retry attempts are exhausted.
        """
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            logger.debug(
                "openrouter_request",
                model=self._model,
                prompt_chars=len(prompt),
                has_system=bool(system),
            )
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            logger.debug(
                "openrouter_response",
                model=self._model,
                response_chars=len(content),
                finish_reason=response.choices[0].finish_reason,
            )
            return content
        except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError):
            # Let tenacity handle these
            raise
        except openai.AuthenticationError as exc:
            raise ConfigurationError(
                "OpenRouter authentication failed — check OPENROUTER_API_KEY",
                details=str(exc),
            ) from exc
        except openai.OpenAIError as exc:
            raise LLMError(
                f"OpenRouter API error with model {self._model!r}",
                details=str(exc),
            ) from exc
