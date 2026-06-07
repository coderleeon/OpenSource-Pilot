"""Abstract base agent providing shared utilities.

All concrete agents inherit from ``BaseAgent`` to get a pre-configured
logger and shared helper methods.
"""

from __future__ import annotations

from abc import ABC

import structlog

from app.core.logging import get_logger


class BaseAgent(ABC):
    """Base class for all OpenSourcePilot agents.

    Provides:
    - A structlog logger bound to the subclass name.
    - Shared prompt-building helpers.
    """

    def __init__(self) -> None:
        self._logger = get_logger(type(self).__module__ + "." + type(self).__name__)

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Agent-specific logger instance."""
        return self._logger  # type: ignore[return-value]

    @staticmethod
    def _truncate(text: str, max_chars: int = 3000) -> str:
        """Truncate *text* to *max_chars* with an ellipsis indicator."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + f"\n... [truncated, {len(text) - max_chars} chars omitted]"
