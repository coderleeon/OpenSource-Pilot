"""Pydantic schemas for open source radar endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class DiscoverRequest(BaseModel):
    """Request schema for opportunity discovery."""

    skills: list[str] = Field(default_factory=list, description="User skills (e.g. Python, frontend).")
    technologies: list[str] = Field(default_factory=list, description="Target technologies (e.g. FastAPI, react).")
    interests: list[str] = Field(default_factory=list, description="Target interests or fields (e.g. LLMs, database).")
    experience_level: str = Field(
        default="beginner",
        description="Experience level: 'beginner', 'intermediate', or 'advanced'."
    )


class FitAnalysisResponse(BaseModel):
    """LLM evaluation of contributor-issue compatibility."""

    fit_score: int = Field(description="Compatibility score (0-100).")
    difficulty: str = Field(description="Difficulty rating: 'Easy', 'Medium', or 'Hard'.")
    learning_value: str = Field(description="Estimated learning reward: 'Low', 'Medium', or 'High'.")
    reason: str = Field(description="Detailed reason for this matching analysis.")


class MergeProbabilityResponse(BaseModel):
    """PR acceptance likelihood and explanations."""

    merge_probability: int = Field(description="Merge probability score (0-100).")
    confidence: str = Field(description="Confidence rating: 'Low', 'Medium', or 'High'.")
    explanation: str = Field(description="Explainable breakdown of repository responsiveness factors.")


class RepoHealthResponse(BaseModel):
    """Aggregated repository activity metrics."""

    maintainer_activity: int = Field(description="Score (0-100) based on maintainer responsiveness.")
    release_frequency: int = Field(description="Score (0-100) based on tag and release cadence.")
    open_issue_trends: str = Field(description="Open issues trend: 'Improving', 'Stable', or 'Degrading'.")
    contribution_velocity: int = Field(description="Score (0-100) tracking review turnaround.")
    community_engagement: int = Field(description="Score (0-100) tracking community interaction.")
    health_explanation: str = Field(description="Summary of repository health observations.")


class MissingFeatureSuggestion(BaseModel):
    """Suggested feature card description."""

    feature_name: str = Field(description="Short title of the missing feature.")
    description: str = Field(description="Overview of the missing capability.")
    reasoning: str = Field(description="Technical rationale for the suggestion.")


class OpportunityRepositoryDetail(BaseModel):
    """Details of the containing repository."""

    name: str
    full_name: str
    description: str | None = None
    url: str
    stars: int
    forks: int
    open_issues_count: int
    primary_language: str | None = None
    topics: list[str] = Field(default_factory=list)


class OpportunityIssueDetail(BaseModel):
    """Details of the opportunity issue."""

    number: int
    title: str
    body: str | None = None
    labels: list[str] = Field(default_factory=list)
    url: str
    comments_count: int
    author: str
    created_at: str
    age_days: int


class OpportunityResponse(BaseModel):
    """Composite opportunity discovery result."""

    repository: OpportunityRepositoryDetail
    issue: OpportunityIssueDetail
    fit_analysis: FitAnalysisResponse
    merge_probability: MergeProbabilityResponse
    repo_health: RepoHealthResponse
    missing_features: list[MissingFeatureSuggestion] = Field(default_factory=list)


class DiscoverResponse(BaseModel):
    """List of matching open source opportunities."""

    opportunities: list[OpportunityResponse] = Field(default_factory=list)


class MissingFeaturesRequest(BaseModel):
    """Request schema for repo missing feature detection."""

    repo_url: str = Field(..., description="GitHub repository URL.")

    @field_validator("repo_url", mode="after")
    @classmethod
    def _must_be_github(cls, v: str) -> str:
        if "github.com" not in v.lower():
            raise ValueError("Only GitHub repository URLs are supported.")
        return v.strip().rstrip("/")


class MissingFeaturesResponse(BaseModel):
    """List of missing capabilities for a repository."""

    repo_name: str
    missing_features: list[MissingFeatureSuggestion] = Field(default_factory=list)


class RepoHealthRequest(BaseModel):
    """Request schema for repository health analysis."""

    repo_url: str = Field(..., description="GitHub repository URL.")

    @field_validator("repo_url", mode="after")
    @classmethod
    def _must_be_github(cls, v: str) -> str:
        if "github.com" not in v.lower():
            raise ValueError("Only GitHub repository URLs are supported.")
        return v.strip().rstrip("/")


class RepoHealthDetailResponse(BaseModel):
    """Detailed health analysis response."""

    repo_name: str
    repo_health: RepoHealthResponse
