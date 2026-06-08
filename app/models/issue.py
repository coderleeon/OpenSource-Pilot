"""Domain models representing GitHub issues and contribution plans."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class IssueType(str, Enum):
    """Classification of a GitHub issue by intent.

    Used to choose the appropriate plan generation strategy:

    - ``BUG`` / ``FEATURE_REQUEST`` / ``DOCUMENTATION`` → full contribution plan
      (implementation steps + files to modify)
    - ``QUESTION`` / ``DISCUSSION`` → answer/explanation plan
      (no implementation steps, no files to modify)
    - ``UNKNOWN`` → fallback when classification is inconclusive
    """

    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    DOCUMENTATION = "documentation"
    QUESTION = "question"
    DISCUSSION = "discussion"
    UNKNOWN = "unknown"

    @property
    def needs_contribution_plan(self) -> bool:
        """True when the issue warrants implementation steps and file changes."""
        return self in (IssueType.BUG, IssueType.FEATURE_REQUEST, IssueType.DOCUMENTATION)

    @property
    def needs_answer_plan(self) -> bool:
        """True when the issue should receive an explanation rather than code changes."""
        return self in (IssueType.QUESTION, IssueType.DISCUSSION)

    @property
    def display_name(self) -> str:
        """Human-friendly display label."""
        return {
            IssueType.BUG: "Bug Report",
            IssueType.FEATURE_REQUEST: "Feature Request",
            IssueType.DOCUMENTATION: "Documentation",
            IssueType.QUESTION: "Question",
            IssueType.DISCUSSION: "Discussion",
            IssueType.UNKNOWN: "Unknown",
        }[self]


@dataclass
class GitHubIssue:
    """A GitHub issue retrieved via the API.

    Attributes:
        number: Issue number.
        title: Issue title.
        body: Issue body text (may be empty or ``None``).
        labels: List of label names.
        state: ``"open"`` or ``"closed"``.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        url: HTML URL of the issue.
        comments_count: Number of comments on the issue.
        author: GitHub login of the issue author.
    """

    number: int
    title: str
    body: str | None
    labels: list[str]
    state: str
    created_at: datetime
    updated_at: datetime
    url: str
    comments_count: int
    author: str = ""

    @property
    def full_text(self) -> str:
        """Combined title and body for use in search queries."""
        body = self.body or ""
        return f"{self.title}\n\n{body}".strip()

    @property
    def age_days(self) -> int:
        """Approximate age of the issue in days."""
        delta = datetime.utcnow() - self.created_at.replace(tzinfo=None)
        return delta.days


@dataclass
class IssueRanking:
    """An issue ranked and scored for beginner contribution suitability.

    Attributes:
        issue: The underlying ``GitHubIssue``.
        difficulty_estimate: Human-readable estimate: ``"easy"``, ``"medium"``, or ``"hard"``.
        score: Numeric suitability score (0–10, higher = more suitable).
        beginner_friendly: True if the issue is tagged as beginner-friendly.
        required_skills: Skills likely needed (e.g. ``["Python", "async", "testing"]``).
        matching_labels: Labels that contributed to ranking (e.g. ``["good first issue"]``).
        issue_type: Classified issue type (bug, feature_request, question, …).
    """

    issue: GitHubIssue
    difficulty_estimate: str
    score: float
    beginner_friendly: bool
    required_skills: list[str] = field(default_factory=list)
    matching_labels: list[str] = field(default_factory=list)
    issue_type: IssueType = IssueType.UNKNOWN


@dataclass
class GeneratedTests:
    """LLM-generated test suite for a contribution.

    Attributes:
        unit_tests: Source code for unit tests (isolated, mocked dependencies).
        integration_tests: Source code for integration tests (component interactions).
        edge_cases: Source code for edge-case and error-path tests.
        test_file_path: Suggested file path for the test file (e.g. ``tests/test_sessions.py``).
        framework: Testing framework used (e.g. ``"pytest"``, ``"unittest"``, ``"jest"``).
        dependencies: Additional test dependencies to install (e.g. ``["pytest-mock", "httpx"]``).
        setup_notes: Any setup or configuration notes for running the tests.
    """

    unit_tests: str
    integration_tests: str
    edge_cases: str
    test_file_path: str
    framework: str
    dependencies: list[str] = field(default_factory=list)
    setup_notes: str = ""


@dataclass
class PRDraft:
    """LLM-generated pull request draft for a contribution.

    Attributes:
        title: Concise PR title following conventional commit style.
        summary: Markdown-formatted PR body summarising the change.
        testing_checklist: Ordered list of items the reviewer should verify.
        reviewer_notes: Context for reviewers (design decisions, trade-offs, risks).
        labels_suggested: Suggested GitHub labels (e.g. ``["bug", "needs-review"]``).
        draft_body: Full combined PR body (title + summary + checklist + notes).
    """

    title: str
    summary: str
    testing_checklist: list[str]
    reviewer_notes: str
    labels_suggested: list[str] = field(default_factory=list)
    draft_body: str = ""


@dataclass
class ContributionPlan:
    """A structured response plan for a GitHub issue.

    The shape of the plan depends on ``plan_type``:

    - ``"contribution"`` (bug / feature_request / documentation):
      Populated: ``implementation_steps``, ``files_to_modify``,
      ``root_cause_hypothesis``, ``estimated_effort``.
      Empty: ``answer_explanation``, ``key_questions``, ``suggested_resources``.

    - ``"answer"`` (question / discussion):
      Populated: ``answer_explanation``, ``key_questions``,
      ``suggested_resources``.
      Empty: ``implementation_steps``, ``files_to_modify``,
      ``root_cause_hypothesis``, ``estimated_effort``.

    Attributes:
        plan_type: ``"contribution"`` or ``"answer"``.
        issue_type: The classified issue type that drove plan generation.
        problem_explanation: Plain-language explanation of the issue.
        root_cause_hypothesis: Hypothesis about what is causing the problem
            (contribution plans only).
        implementation_steps: Ordered list of concrete implementation steps
            (contribution plans only).
        files_to_modify: Repository-relative paths of files to modify
            (contribution plans only).
        relevant_concepts: Key concepts a contributor needs to understand.
        estimated_effort: Rough effort estimate, e.g. ``"2–4 hours"``
            (contribution plans only).
        references: Useful links, docs, or related issues.
        answer_explanation: Full answer / explanation of the question
            (answer plans only).
        key_questions: Follow-up questions or aspects to investigate
            (answer plans only).
        suggested_resources: Links to documentation, tutorials, or related issues
            (answer plans only).
    """

    plan_type: str  # "contribution" | "answer"
    issue_type: str  # IssueType.value
    problem_explanation: str
    # --- Contribution plan fields ---
    root_cause_hypothesis: str = ""
    implementation_steps: list[str] = field(default_factory=list)
    files_to_modify: list[str] = field(default_factory=list)
    relevant_concepts: list[str] = field(default_factory=list)
    estimated_effort: str = ""
    references: list[str] = field(default_factory=list)
    # --- Answer plan fields ---
    answer_explanation: str = ""
    key_questions: list[str] = field(default_factory=list)
    suggested_resources: list[str] = field(default_factory=list)
