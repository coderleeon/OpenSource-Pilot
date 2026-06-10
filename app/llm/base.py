"""Abstract base class for all LLM client implementations.

Every concrete provider (OpenRouter, OpenAI, Anthropic) must implement
``complete()`` and ``complete_json()``.  This allows agents and services to
be written against the interface — not a specific SDK — making them easy to
test with mocks and simple to swap providers.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod

from app.core.exceptions import LLMParseError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Pattern to extract JSON from markdown fenced code blocks
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)
# Pattern to match a bare JSON object or array
_BARE_JSON_RE = re.compile(r"(\{.*\}|\[.*\])", re.DOTALL)


class LLMClient(ABC):
    """Abstract interface for LLM text-completion clients.

    Implementors should handle:
    - Authentication
    - Retry / backoff on transient errors
    - Provider-specific payload construction
    """

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> str:
        """Send a prompt and return the model's text response.

        Args:
            prompt: The user message to send.
            system: Optional system prompt / instructions.
            temperature: Sampling temperature (0 = deterministic).
            max_tokens: Maximum tokens in the response.

        Returns:
            Raw text response from the model.

        Raises:
            LLMError: If the call fails after all retries.
        """
        ...

    async def complete_json(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> dict:  # type: ignore[type-arg]
        """Send a prompt and parse the response as JSON.

        The prompt should instruct the model to respond with JSON only.
        This method handles extraction from markdown code fences.

        Args:
            prompt: User message instructing the model to return JSON.
            system: Optional system prompt.
            temperature: Lower temperature for more deterministic JSON output.
            max_tokens: Maximum tokens.

        Returns:
            Parsed Python dict from the model's JSON response.

        Raises:
            LLMError: If the completion call fails.
            LLMParseError: If the response cannot be parsed as valid JSON.
        """
        raw = await self.complete(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        logger.info(
            "llm_raw_response",
            length=len(raw),
        )
        return self._extract_json(raw)

    @staticmethod
    def _extract_json(text: str) -> dict:  # type: ignore[type-arg]
        """Extract and parse a JSON object from *text*.

        Handles:
        - Bare JSON: ``{"key": "value"}``
        - Markdown fenced: triple-backtick json block
        - JSON with surrounding text

        Raises:
            LLMParseError: If no valid JSON can be extracted.
        """
        text = text.strip()

        # 1. Try direct parse (common when response_format=json_object is used)
        try:
            result = json.loads(text)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # 2. Try extracting from markdown code fence
        fence_match = _JSON_FENCE_RE.search(text)
        if fence_match:
            try:
                result = json.loads(fence_match.group(1))
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass

        # 3. Try extracting bare JSON object from surrounding text
        bare_match = _BARE_JSON_RE.search(text)
        if bare_match:
            try:
                result = json.loads(bare_match.group(1))
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass

        raise LLMParseError(
            "Failed to extract valid JSON from LLM response",
            details=f"Raw response (first 500 chars): {text[:500]}",
        )
