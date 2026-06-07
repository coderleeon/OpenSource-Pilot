"""Unit tests for PlanningAgent — including issue-type-based plan branching."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.agents.planning_agent import PlanningAgent
from app.core.exceptions import LLMParseError
from app.models.issue import ContributionPlan, GitHubIssue, IssueType
from app.models.repo import RepoMetadata


class TestPlanningAgentContribution:
    """Tests for contribution plan path (bug / feature_request / documentation)."""

    @pytest.fixture()
    def agent(self, mock_llm_client: AsyncMock) -> PlanningAgent:
        return PlanningAgent(llm_client=mock_llm_client)  # type: ignore[arg-type]

    async def test_generate_plan_returns_contribution_plan(
        self,
        agent: PlanningAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        relevant_code = [
            {
                "text": "def open_session(self, app, request):\n    pass",
                "file_path": "src/sessions.py",
                "language": "Python",
                "chunk_index": 0,
                "distance": 0.15,
            }
        ]
        plan = await agent.generate_plan(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=relevant_code,
            issue_type=IssueType.BUG,
        )
        assert isinstance(plan, ContributionPlan)
        assert plan.plan_type == "contribution"
        assert plan.problem_explanation
        assert len(plan.implementation_steps) > 0
        assert isinstance(plan.files_to_modify, list)

    async def test_generate_plan_with_empty_code_context(
        self,
        agent: PlanningAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """Should still produce a plan even with no relevant code snippets."""
        plan = await agent.generate_plan(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.BUG,
        )
        assert isinstance(plan, ContributionPlan)
        assert plan.plan_type == "contribution"

    async def test_generate_plan_calls_llm(
        self,
        agent: PlanningAgent,
        mock_llm_client: AsyncMock,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        await agent.generate_plan(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.BUG,
        )
        mock_llm_client.complete_json.assert_called_once()

    async def test_generate_plan_llm_parse_error(
        self,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """LLMParseError should propagate from complete_json."""
        bad_client = AsyncMock()
        bad_client.complete_json = AsyncMock(side_effect=LLMParseError("bad json"))
        agent = PlanningAgent(llm_client=bad_client)  # type: ignore[arg-type]

        with pytest.raises(LLMParseError):
            await agent.generate_plan(
                issue=sample_issue,
                repo_metadata=sample_repo_metadata,
                relevant_code=[],
                issue_type=IssueType.BUG,
            )

    async def test_plan_estimated_effort_present(
        self,
        agent: PlanningAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        plan = await agent.generate_plan(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.BUG,
        )
        assert plan.estimated_effort != ""

    async def test_feature_request_uses_contribution_path(
        self,
        agent: PlanningAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        plan = await agent.generate_plan(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.FEATURE_REQUEST,
        )
        assert plan.plan_type == "contribution"

    async def test_documentation_uses_contribution_path(
        self,
        agent: PlanningAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        plan = await agent.generate_plan(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.DOCUMENTATION,
        )
        assert plan.plan_type == "contribution"

    async def test_unknown_type_uses_contribution_path(
        self,
        agent: PlanningAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """UNKNOWN should fall back to contribution plan (safest default)."""
        plan = await agent.generate_plan(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.UNKNOWN,
        )
        assert plan.plan_type == "contribution"


class TestPlanningAgentAnswer:
    """Tests for answer plan path (question / discussion)."""

    @pytest.fixture()
    def mock_answer_client(self) -> AsyncMock:
        """Mock LLM that returns an answer-plan JSON."""
        client = AsyncMock()
        client.complete_json = AsyncMock(
            return_value={
                "problem_explanation": "The user is asking how Flask sessions work.",
                "answer_explanation": (
                    "Flask sessions use signed cookies by default. The session object "
                    "behaves like a dictionary and is stored client-side."
                ),
                "key_questions": [
                    "Are you using server-side or client-side sessions?",
                    "Which Flask-Session extension, if any?",
                ],
                "suggested_resources": [
                    "https://flask.palletsprojects.com/en/stable/quickstart/#sessions"
                ],
                "references": [],
                # Contribution fields should be ignored by the answer path
                "implementation_steps": [],
                "files_to_modify": [],
            }
        )
        return client

    @pytest.fixture()
    def answer_agent(self, mock_answer_client: AsyncMock) -> PlanningAgent:
        return PlanningAgent(llm_client=mock_answer_client)  # type: ignore[arg-type]

    async def test_question_produces_answer_plan(
        self,
        answer_agent: PlanningAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        plan = await answer_agent.generate_plan(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.QUESTION,
        )
        assert plan.plan_type == "answer"

    async def test_discussion_produces_answer_plan(
        self,
        answer_agent: PlanningAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        plan = await answer_agent.generate_plan(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.DISCUSSION,
        )
        assert plan.plan_type == "answer"

    async def test_answer_plan_has_no_implementation_steps(
        self,
        answer_agent: PlanningAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        plan = await answer_agent.generate_plan(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.QUESTION,
        )
        assert plan.implementation_steps == []

    async def test_answer_plan_has_no_files_to_modify(
        self,
        answer_agent: PlanningAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        plan = await answer_agent.generate_plan(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.QUESTION,
        )
        assert plan.files_to_modify == []

    async def test_answer_plan_has_answer_explanation(
        self,
        answer_agent: PlanningAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        plan = await answer_agent.generate_plan(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.QUESTION,
        )
        assert plan.answer_explanation

    async def test_answer_plan_issue_type_recorded(
        self,
        answer_agent: PlanningAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        plan = await answer_agent.generate_plan(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.QUESTION,
        )
        assert plan.issue_type == IssueType.QUESTION.value


class TestSummarizeRepo:
    @pytest.fixture()
    def agent(self, mock_llm_client: AsyncMock) -> PlanningAgent:
        return PlanningAgent(llm_client=mock_llm_client)  # type: ignore[arg-type]

    async def test_summarize_repo_returns_summaries(
        self,
        agent: PlanningAgent,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.summarize_repo(sample_repo_metadata)
        assert "readme_summary" in result
        assert "contribution_guide_summary" in result
        assert result["readme_summary"]  # non-empty
