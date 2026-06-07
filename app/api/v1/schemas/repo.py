"""Pydantic schemas for repository analysis endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class RepoAnalyzeRequest(BaseModel):
    """Request body for ``POST /api/v1/analyze-repo``."""

    repo_url: str = Field(
        ...,
        description="GitHub repository URL (e.g. https://github.com/pallets/flask).",
        examples=["https://github.com/pallets/flask"],
    )
    index_code: bool = Field(
        default=True,
        description="Whether to chunk and index source files into ChromaDB.",
    )

    @field_validator("repo_url", mode="after")
    @classmethod
    def _must_be_github(cls, v: str) -> str:
        if "github.com" not in v.lower():
            raise ValueError("Only GitHub repository URLs are supported.")
        return v.strip().rstrip("/")


class TechStackResponse(BaseModel):
    """Technology stack detected in the repository."""

    languages: list[str]
    frameworks: list[str]
    tools: list[str]
    package_managers: list[str]


class RepoAnalyzeResponse(BaseModel):
    """Response body for ``POST /api/v1/analyze-repo``."""

    analysis_id: str = Field(description="Unique ID for this analysis run.")
    repo_name: str
    full_name: str = Field(description="owner/repo slug (e.g. 'pallets/flask').")
    description: str | None
    url: str
    primary_language: str | None
    topics: list[str]
    stars: int
    forks: int
    open_issues_count: int
    license_name: str | None
    has_readme: bool
    has_contributing_guide: bool
    directory_structure: dict = Field(  # type: ignore[type-arg]
        description=(
            "Depth-2 file tree of the repository root. "
            "Directories beyond depth 2 show 'truncated: true' instead of children. "
            "Full tree is kept internally for code indexing."
        )
    )
    total_files_count: int = Field(
        description="Total number of files found in the repository (full recursive count)."
    )
    total_directories_count: int = Field(
        description="Total number of directories found in the repository (full recursive count)."
    )
    key_directories: list[str] = Field(
        description="Paths of top-level directories (direct children of the repo root)."
    )
    tech_stack: TechStackResponse
    readme_summary: str = Field(
        description="LLM-generated 2-3 sentence summary of the project's purpose and features."
    )
    contribution_guide_summary: str = Field(
        description="LLM-generated 2-3 sentence summary of the contributing process."
    )
    architecture_summary: str = Field(
        description=(
            "LLM-generated 2-4 sentence description of the repository's software architecture, "
            "pattern (MVC, layered, plugin-based, …), and major structural sections."
        )
    )
    total_files_indexed: int = Field(
        description="Number of source file chunks indexed into ChromaDB (0 if indexing was skipped)."
    )
