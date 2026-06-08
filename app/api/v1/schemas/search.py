"""Pydantic schemas for the semantic code search endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CodeSearchRequest(BaseModel):
    """Request body for ``POST /api/v1/search-code``."""

    repo_url: str = Field(
        ...,
        description="GitHub repository URL.",
        examples=["https://github.com/pallets/flask"],
    )
    query: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Natural language or code fragment to search for.",
        examples=["session expiry timeout handling"],
    )
    n_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return (1–50).",
    )

    @field_validator("repo_url", mode="after")
    @classmethod
    def _must_be_github(cls, v: str) -> str:
        if "github.com" not in v.lower():
            raise ValueError("Only GitHub repository URLs are supported.")
        return v.strip().rstrip("/")


class CodeSearchResult(BaseModel):
    """A single code search result."""

    file_path: str = Field(description="Relative path of the file within the repository.")
    language: str = Field(description="Detected programming language.")
    snippet: str = Field(description="Matching code snippet (up to 800 chars).")
    relevance_distance: float = Field(
        description="Semantic distance score (lower = more relevant, range 0–2)."
    )


class CodeSearchResponse(BaseModel):
    """Response body for ``POST /api/v1/search-code``."""

    repo_name: str = Field(description="Full repository slug (owner/repo).")
    query: str = Field(description="The search query that was executed.")
    total_results: int = Field(description="Number of results returned.")
    results: list[CodeSearchResult]
