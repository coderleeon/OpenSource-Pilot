"""Unit tests for PRAgent."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.agents.pr_agent import PRAgent, _assemble_draft_body
from app.core.exceptions import LLMParseError
from app.models.issue import ContributionPlan, GitHubIssue, PRDraft
from app.models.repo import RepoMetadata


# ---------------------------------------------------------------------------
# _assemble_draft_body helper
# ---------------------------------------------------------------------------


class TestAssembleDraftBody:
    def test_includes_summary(self) -> None:
        body = _assemble_draft_body(
            title="fix: do something",
            summary="This PR fixes the session timeout bug.",
            checklist=["Tests pass", "No regressions"],
            notes="Reviewed timezone handling carefully.",
            issue_number=42,
        )
        assert "This PR fixes the session timeout bug." in body

    def test_includes_checklist_as_checkboxes(self) -> None:
        body = _assemble_draft_body(
            title="fix: do something",
            summary="Summary.",
            checklist=["Tests pass", "No regressions"],
            notes="Notes.",
            issue_number=42,
        )
        assert "- [ ] Tests pass" in body
        assert "- [ ] No regressions" in body

    def test_includes_closes_reference(self) -> None:
        body = _assemble_draft_body(
            title="fix: do something",
            summary="Summary.",
            checklist=[],
            notes="Notes.",
            issue_number=99,
        )
        assert "Closes #99" in body

    def test_includes_reviewer_notes(self) -> None:
        body = _assemble_draft_body(
            title="fix: do something",
            summary="Summary.",
            checklist=[],
            notes="This change affects session expiry.",
            issue_number=1,
        )
        assert "This change affects session expiry." in body

    def test_empty_checklist_uses_default(self) -> None:
        body = _assemble_draft_body(
            title="fix: do something",
            summary="Summary.",
            checklist=[],
            notes="",
            issue_number=1,
        )
        assert "- [ ] All existing tests pass" in body


# ---------------------------------------------------------------------------
# PRAgent.generate_pr_draft
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_pr_client() -> AsyncMock:
    client = AsyncMock()
    client.complete_json = AsyncMock(
        return_value={
            "title": "fix(sessions): handle timezone-aware datetime expiry",
            "summary": "This PR fixes the session timeout bug reported in #5420.",
            "testing_checklist": [
                "Run pytest tests/test_sessions.py",
                "Verify session expires after configured timeout",
                "Test with both naive and timezone-aware datetimes",
            ],
            "reviewer_notes": "The root cause was naive datetime comparison in sessions.py.",
            "labels_suggested": ["bug", "needs-review"],
            "draft_body": (
                "## Summary\nThis PR fixes the session timeout bug.\n\n"
                "## Testing\n- [ ] pytest passes\n\nCloses #5420"
            ),
        }
    )
    return client


@pytest.fixture()
def agent(mock_pr_client: AsyncMock) -> PRAgent:
    return PRAgent(llm_client=mock_pr_client)  # type: ignore[arg-type]


class TestGeneratePRDraft:
    async def test_returns_pr_draft_instance(
        self,
        agent: PRAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_pr_draft(
            issue=sample_issue,
            plan=sample_contribution_plan,
            repo_metadata=sample_repo_metadata,
        )
        assert isinstance(result, PRDraft)

    async def test_title_populated(
        self,
        agent: PRAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_pr_draft(
            issue=sample_issue,
            plan=sample_contribution_plan,
            repo_metadata=sample_repo_metadata,
        )
        assert result.title == "fix(sessions): handle timezone-aware datetime expiry"

    async def test_title_conventional_commit_format(
        self,
        agent: PRAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_pr_draft(
            issue=sample_issue,
            plan=sample_contribution_plan,
            repo_metadata=sample_repo_metadata,
        )
        # Should start with a conventional commit type
        assert any(result.title.startswith(t) for t in ["fix", "feat", "docs", "refactor", "test", "chore"])

    async def test_summary_populated(
        self,
        agent: PRAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_pr_draft(
            issue=sample_issue,
            plan=sample_contribution_plan,
            repo_metadata=sample_repo_metadata,
        )
        assert result.summary != ""

    async def test_testing_checklist_is_list(
        self,
        agent: PRAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_pr_draft(
            issue=sample_issue,
            plan=sample_contribution_plan,
            repo_metadata=sample_repo_metadata,
        )
        assert isinstance(result.testing_checklist, list)
        assert len(result.testing_checklist) > 0

    async def test_reviewer_notes_populated(
        self,
        agent: PRAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_pr_draft(
            issue=sample_issue,
            plan=sample_contribution_plan,
            repo_metadata=sample_repo_metadata,
        )
        assert result.reviewer_notes != ""

    async def test_labels_suggested_is_list(
        self,
        agent: PRAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_pr_draft(
            issue=sample_issue,
            plan=sample_contribution_plan,
            repo_metadata=sample_repo_metadata,
        )
        assert isinstance(result.labels_suggested, list)

    async def test_draft_body_populated(
        self,
        agent: PRAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_pr_draft(
            issue=sample_issue,
            plan=sample_contribution_plan,
            repo_metadata=sample_repo_metadata,
        )
        assert result.draft_body != ""
        assert "Closes" in result.draft_body or "closes" in result.draft_body.lower()

    async def test_llm_called_once(
        self,
        agent: PRAgent,
        mock_pr_client: AsyncMock,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        await agent.generate_pr_draft(
            issue=sample_issue,
            plan=sample_contribution_plan,
            repo_metadata=sample_repo_metadata,
        )
        mock_pr_client.complete_json.assert_called_once()

    async def test_llm_parse_error_propagates(
        self,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        bad_client = AsyncMock()
        bad_client.complete_json = AsyncMock(side_effect=LLMParseError("bad json"))
        agent = PRAgent(llm_client=bad_client)  # type: ignore[arg-type]

        with pytest.raises(LLMParseError):
            await agent.generate_pr_draft(
                issue=sample_issue,
                plan=sample_contribution_plan,
                repo_metadata=sample_repo_metadata,
            )

    async def test_fallback_draft_body_when_llm_omits_it(
        self,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """When LLM returns no draft_body, the fallback assembler runs."""
        client = AsyncMock()
        client.complete_json = AsyncMock(
            return_value={
                "title": "fix: something",
                "summary": "Fixed it.",
                "testing_checklist": ["Run tests"],
                "reviewer_notes": "Be careful.",
                "labels_suggested": [],
                # draft_body intentionally absent
            }
        )
        agent = PRAgent(llm_client=client)  # type: ignore[arg-type]
        result = await agent.generate_pr_draft(
            issue=sample_issue,
            plan=sample_contribution_plan,
            repo_metadata=sample_repo_metadata,
        )
        assert result.draft_body != ""
        assert f"Closes #{sample_issue.number}" in result.draft_body

    async def test_answer_plan_pr_draft(
        self,
        agent: PRAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """PR drafts for documentation/answer plans should still work."""
        answer_plan = ContributionPlan(
            plan_type="answer",
            issue_type="documentation",
            problem_explanation="Missing docs for session timeout config.",
        )
        result = await agent.generate_pr_draft(
            issue=sample_issue,
            plan=answer_plan,
            repo_metadata=sample_repo_metadata,
        )
        assert isinstance(result, PRDraft)
