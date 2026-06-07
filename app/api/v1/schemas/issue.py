"""Pydantic schemas for issue analysis endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class IssueAnalyzeRequest(BaseModel):
    """Request body for ``POST /api/v1/analyze-issue``."""

    repo_url: str = Field(
        ...,
        description="GitHub repository URL.",
        examples=["https://github.com/pallets/flask"],
    )
    issue_number: int = Field(
        ...,
        ge=1,
        description="GitHub issue number to analyse.",
        examples=[5420],
    )

    @field_validator("repo_url", mode="after")
    @classmethod
    def _must_be_github(cls, v: str) -> str:
        if "github.com" not in v.lower():
            raise ValueError("Only GitHub repository URLs are supported.")
        return v.strip().rstrip("/")


class IssueListRequest(BaseModel):
    """Request body for ``POST /api/v1/list-issues``."""

    repo_url: str = Field(..., description="GitHub repository URL.")
    limit: int = Field(default=30, ge=1, le=100, description="Max issues to return.")

    @field_validator("repo_url", mode="after")
    @classmethod
    def _must_be_github(cls, v: str) -> str:
        if "github.com" not in v.lower():
            raise ValueError("Only GitHub repository URLs are supported.")
        return v.strip().rstrip("/")


class IssueDetail(BaseModel):
    """Details of a single GitHub issue."""

    number: int
    title: str
    body: str | None
    labels: list[str]
    state: str
    url: str
    comments_count: int
    author: str
    created_at: str


class CodeSnippet(BaseModel):
    """A relevant code snippet returned by semantic search."""

    file_path: str
    language: str
    snippet: str
    relevance_distance: float


class ContributionPlanResponse(BaseModel):
    """LLM-generated plan for a GitHub issue.

    The shape of meaningful fields depends on ``plan_type``:

    - ``"contribution"`` (bug / feature_request / documentation):
      ``implementation_steps``, ``files_to_modify``, ``root_cause_hypothesis``,
      and ``estimated_effort`` are populated.
      ``answer_explanation``, ``key_questions``, and ``suggested_resources``
      are empty strings / empty lists.

    - ``"answer"`` (question / discussion):
      ``answer_explanation``, ``key_questions``, and ``suggested_resources``
      are populated.
      ``implementation_steps``, ``files_to_modify``, ``root_cause_hypothesis``,
      and ``estimated_effort`` are empty.
    """

    plan_type: str = Field(
        description="'contribution' for bug/feature/docs issues; 'answer' for questions/discussions."
    )
    issue_type: str = Field(
        description=(
            "Classified issue type: 'bug', 'feature_request', 'documentation', "
            "'question', 'discussion', or 'unknown'."
        )
    )
    problem_explanation: str = Field(
        description="Plain-language description of what the issue is about."
    )
    # --- Contribution plan fields ---
    root_cause_hypothesis: str = Field(
        default="",
        description="[contribution only] Hypothesis about the root cause or missing feature.",
    )
    implementation_steps: list[str] = Field(
        default_factory=list,
        description="[contribution only] Ordered implementation steps.",
    )
    files_to_modify: list[str] = Field(
        default_factory=list,
        description="[contribution only] Repo-relative paths of files to modify.",
    )
    relevant_concepts: list[str] = Field(
        default_factory=list,
        description="[contribution only] Concepts a contributor needs to understand.",
    )
    estimated_effort: str = Field(
        default="",
        description="[contribution only] Rough effort estimate, e.g. '1-2 hours'.",
    )
    references: list[str] = Field(
        default_factory=list,
        description="Useful links, docs, or related issues (both plan types).",
    )
    # --- Answer plan fields ---
    answer_explanation: str = Field(
        default="",
        description="[answer only] Full answer or explanation of the question/discussion.",
    )
    key_questions: list[str] = Field(
        default_factory=list,
        description="[answer only] Follow-up questions or aspects to investigate.",
    )
    suggested_resources: list[str] = Field(
        default_factory=list,
        description="[answer only] Links to docs, tutorials, or examples.",
    )


class IssueAnalyzeResponse(BaseModel):
    """Response body for ``POST /api/v1/analyze-issue``."""

    repo_name: str
    issue_type: str = Field(
        description=(
            "Classified issue type: 'bug', 'feature_request', 'documentation', "
            "'question', 'discussion', or 'unknown'."
        )
    )
    issue_type_display: str = Field(
        description="Human-friendly label for the issue type (e.g. 'Bug Report')."
    )
    issue: IssueDetail
    difficulty_estimate: str = Field(description="'easy', 'medium', or 'hard'.")
    beginner_friendly: bool
    suitability_score: float = Field(description="0–10 suitability score.")
    relevant_files: list[str] = Field(
        description="Unique file paths from semantic search results."
    )
    relevant_code_snippets: list[CodeSnippet]
    contribution_plan: ContributionPlanResponse


class RankedIssue(BaseModel):
    """A single ranked issue in the list-issues response."""

    number: int
    title: str
    labels: list[str]
    state: str
    url: str
    comments_count: int
    difficulty_estimate: str
    suitability_score: float
    beginner_friendly: bool
    required_skills: list[str]
    issue_type: str = Field(
        description="Classified issue type value (e.g. 'bug', 'question')."
    )
    issue_type_display: str = Field(
        description="Human-friendly label (e.g. 'Bug Report', 'Question')."
    )


class IssueListResponse(BaseModel):
    """Response body for ``POST /api/v1/list-issues``."""

    repo_url: str
    total_returned: int
    issues: list[RankedIssue]
