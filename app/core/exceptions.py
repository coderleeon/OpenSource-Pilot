"""Custom exception hierarchy for OpenSourcePilot.

All application exceptions inherit from OpenSourcePilotError so callers
can catch the base type when broad error handling is appropriate.
"""

from __future__ import annotations


class OpenSourcePilotError(Exception):
    """Base exception for all OpenSourcePilot errors."""

    def __init__(self, message: str, *, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} — {self.details}"
        return self.message


# ---------------------------------------------------------------------------
# Repository / Git errors
# ---------------------------------------------------------------------------


class RepoNotFoundError(OpenSourcePilotError):
    """Raised when a GitHub repository cannot be found or accessed."""


class CloneError(OpenSourcePilotError):
    """Raised when cloning a repository fails."""


class StructureParseError(OpenSourcePilotError):
    """Raised when the repository directory structure cannot be parsed."""


# ---------------------------------------------------------------------------
# GitHub API errors
# ---------------------------------------------------------------------------


class GitHubAPIError(OpenSourcePilotError):
    """Raised when a GitHub API call fails (rate limit, auth, network, …)."""


class IssueNotFoundError(OpenSourcePilotError):
    """Raised when a requested issue number does not exist in the repository."""


# ---------------------------------------------------------------------------
# LLM errors
# ---------------------------------------------------------------------------


class LLMError(OpenSourcePilotError):
    """Raised when an LLM call fails after all retries."""


class LLMParseError(OpenSourcePilotError):
    """Raised when the LLM response cannot be parsed as expected (e.g. invalid JSON)."""


# ---------------------------------------------------------------------------
# Indexing / vector store errors
# ---------------------------------------------------------------------------


class IndexingError(OpenSourcePilotError):
    """Raised when ChromaDB indexing fails."""


class SearchError(OpenSourcePilotError):
    """Raised when a semantic search query fails."""


# ---------------------------------------------------------------------------
# Configuration errors
# ---------------------------------------------------------------------------


class ConfigurationError(OpenSourcePilotError):
    """Raised when required configuration is missing or invalid."""
