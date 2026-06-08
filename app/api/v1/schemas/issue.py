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


class TestGenerationRequest(BaseModel):
    """Request body for ``POST /api/v1/issue/generate-tests``."""

    repo_url: str = Field(..., description="GitHub repository URL.")
    issue_number: int = Field(..., ge=1, description="Issue number to generate tests for.")

    @field_validator("repo_url", mode="after")
    @classmethod
    def _must_be_github(cls, v: str) -> str:
        if "github.com" not in v.lower():
            raise ValueError("Only GitHub repository URLs are supported.")
        return v.strip().rstrip("/")


class PRDraftRequest(BaseModel):
    """Request body for ``POST /api/v1/issue/generate-pr-draft``."""

    repo_url: str = Field(..., description="GitHub repository URL.")
    issue_number: int = Field(..., ge=1, description="Issue number to generate a PR draft for.")

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

    - ``"answer"`` (question / discussion):
      ``answer_explanation``, ``key_questions``, and ``suggested_resources``
      are populated.
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
    root_cause_hypothesis: str = Field(default="")
    implementation_steps: list[str] = Field(default_factory=list)
    files_to_modify: list[str] = Field(default_factory=list)
    relevant_concepts: list[str] = Field(default_factory=list)
    estimated_effort: str = Field(default="")
    references: list[str] = Field(default_factory=list)
    answer_explanation: str = Field(default="")
    key_questions: list[str] = Field(default_factory=list)
    suggested_resources: list[str] = Field(default_factory=list)


class IssueAnalyzeResponse(BaseModel):
    """Response body for ``POST /api/v1/analyze-issue``."""

    repo_name: str
    issue_type: str = Field(description="Classified issue type value.")
    issue_type_display: str = Field(description="Human-friendly label for the issue type.")
    issue: IssueDetail
    difficulty_estimate: str = Field(description="'easy', 'medium', or 'hard'.")
    beginner_friendly: bool
    suitability_score: float = Field(description="0–10 suitability score.")
    relevant_files: list[str] = Field(description="Unique file paths from semantic search.")
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
    issue_type: str
    issue_type_display: str


class IssueListResponse(BaseModel):
    """Response body for ``POST /api/v1/list-issues``."""

    repo_url: str
    total_returned: int
    issues: list[RankedIssue]


# ---------------------------------------------------------------------------
# Phase 2 schemas
# ---------------------------------------------------------------------------


class GeneratedTestsResponse(BaseModel):
    """The generated test suite for a contribution."""

    framework: str = Field(description="Testing framework used (e.g. 'pytest', 'jest').")
    test_file_path: str = Field(description="Suggested relative path for the test file.")
    unit_tests: str = Field(description="Complete unit test source code with imports.")
    integration_tests: str = Field(description="Complete integration test source code.")
    edge_cases: str = Field(description="Complete edge-case and error-path test source code.")
    dependencies: list[str] = Field(
        default_factory=list,
        description="Additional test dependencies to install.",
    )
    setup_notes: str = Field(default="", description="Setup or configuration notes.")


class TestGenerationResponse(BaseModel):
    """Response body for ``POST /api/v1/issue/generate-tests``."""

    repo_name: str
    issue_number: int
    issue_title: str
    issue_type: str
    tests: GeneratedTestsResponse


class PRDraftResponse(BaseModel):
    """The generated PR draft for a contribution."""

    title: str = Field(description="Concise PR title in conventional commit format.")
    summary: str = Field(description="Markdown-formatted PR summary.")
    testing_checklist: list[str] = Field(
        description="Ordered list of items the reviewer should verify."
    )
    reviewer_notes: str = Field(
        description="Markdown context for reviewers (design decisions, risks)."
    )
    labels_suggested: list[str] = Field(
        default_factory=list, description="Suggested GitHub labels."
    )
    draft_body: str = Field(description="Full assembled PR body markdown.")


class PRDraftResponseEnvelope(BaseModel):
    """Response body for ``POST /api/v1/issue/generate-pr-draft``."""

    repo_name: str
    issue_number: int
    issue_title: str
    issue_type: str
    pr_draft: PRDraftResponse
