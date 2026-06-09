"""Unit tests for ContributionWorkflowAgent."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.agents.contribution_workflow_agent import ContributionWorkflowAgent
from app.models.issue import ContributionPlan, GeneratedTests, GitHubIssue, IssueType, PRDraft
from app.models.repo import RepoMetadata


@pytest.fixture()
def mock_planning_agent() -> AsyncMock:
    agent = AsyncMock()
    agent.generate_plan = AsyncMock(
        return_value=ContributionPlan(
            plan_type="contribution",
            issue_type="bug",
            problem_explanation="Problem description",
            root_cause_hypothesis="Root cause",
            implementation_steps=["Step 1"],
            files_to_modify=["src/main.py"],
            relevant_concepts=[],
            estimated_effort="1 hour",
            references=[],
        )
    )
    return agent


@pytest.fixture()
def mock_test_gen_agent() -> AsyncMock:
    agent = AsyncMock()
    agent.generate_tests = AsyncMock(
        return_value=GeneratedTests(
            unit_tests="def test_unit(): pass",
            integration_tests="def test_integration(): pass",
            edge_cases="def test_edge(): pass",
            test_file_path="tests/test_unit.py",
            framework="pytest",
            dependencies=[],
            setup_notes="",
        )
    )
    return agent


@pytest.fixture()
def mock_pr_agent() -> AsyncMock:
    agent = AsyncMock()
    agent.generate_pr_draft = AsyncMock(
        return_value=PRDraft(
            title="fix: resolve bug",
            summary="A quick summary",
            testing_checklist=["Unit test passes"],
            reviewer_notes="",
            labels_suggested=[],
            draft_body="body text",
        )
    )
    return agent


@pytest.fixture()
def workflow_agent(
    mock_planning_agent: AsyncMock,
    mock_test_gen_agent: AsyncMock,
    mock_pr_agent: AsyncMock,
) -> ContributionWorkflowAgent:
    return ContributionWorkflowAgent(
        planning_agent=mock_planning_agent,  # type: ignore[arg-type]
        test_generation_agent=mock_test_gen_agent,  # type: ignore[arg-type]
        pr_agent=mock_pr_agent,  # type: ignore[arg-type]
    )


class TestContributionWorkflowAgent:
    async def test_execute_workflow_bug(
        self,
        workflow_agent: ContributionWorkflowAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """Bug report issue runs plan, test gen, and PR draft agents."""
        results = await workflow_agent.execute_workflow(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.BUG,
        )

        assert isinstance(results["contribution_plan"], ContributionPlan)
        assert isinstance(results["generated_tests"], GeneratedTests)
        assert isinstance(results["pr_draft"], PRDraft)

    async def test_execute_workflow_feature_request(
        self,
        workflow_agent: ContributionWorkflowAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """Feature request issue runs plan, test gen, and PR draft agents."""
        results = await workflow_agent.execute_workflow(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.FEATURE_REQUEST,
        )

        assert results["contribution_plan"] is not None
        assert results["generated_tests"] is not None
        assert results["pr_draft"] is not None

    async def test_execute_workflow_documentation(
        self,
        workflow_agent: ContributionWorkflowAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """Documentation issue runs plan, test gen, and PR draft agents."""
        results = await workflow_agent.execute_workflow(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.DOCUMENTATION,
        )

        assert results["contribution_plan"] is not None
        assert results["generated_tests"] is not None
        assert results["pr_draft"] is not None

    async def test_execute_workflow_question_skips_implementation(
        self,
        workflow_agent: ContributionWorkflowAgent,
        mock_planning_agent: AsyncMock,
        mock_test_gen_agent: AsyncMock,
        mock_pr_agent: AsyncMock,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """Question classification skips test generation and PR draft generation."""
        # Setup answer plan
        mock_planning_agent.generate_plan.return_value = ContributionPlan(
            plan_type="answer",
            issue_type="question",
            problem_explanation="How do I do X?",
            answer_explanation="Use Y.",
        )

        results = await workflow_agent.execute_workflow(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.QUESTION,
        )

        assert results["contribution_plan"].plan_type == "answer"
        assert results["generated_tests"] is None
        assert results["pr_draft"] is None

        # Verify test gen and PR agent were not invoked
        mock_test_gen_agent.generate_tests.assert_not_called()
        mock_pr_agent.generate_pr_draft.assert_not_called()

    async def test_execute_workflow_discussion_skips_implementation(
        self,
        workflow_agent: ContributionWorkflowAgent,
        mock_planning_agent: AsyncMock,
        mock_test_gen_agent: AsyncMock,
        mock_pr_agent: AsyncMock,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """Discussion classification skips test generation and PR draft generation."""
        mock_planning_agent.generate_plan.return_value = ContributionPlan(
            plan_type="answer",
            issue_type="discussion",
            problem_explanation="Should we use X?",
            answer_explanation="Yes, it's good.",
        )

        results = await workflow_agent.execute_workflow(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.DISCUSSION,
        )

        assert results["contribution_plan"].plan_type == "answer"
        assert results["generated_tests"] is None
        assert results["pr_draft"] is None

    async def test_execute_workflow_unknown_uses_contribution(
        self,
        workflow_agent: ContributionWorkflowAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """Unknown classification defaults to generating plans, tests, and PR draft."""
        results = await workflow_agent.execute_workflow(
            issue=sample_issue,
            repo_metadata=sample_repo_metadata,
            relevant_code=[],
            issue_type=IssueType.UNKNOWN,
        )

        # UNKNOWN does not need answer plan -> needs contribution plan
        assert results["contribution_plan"] is not None
        assert results["generated_tests"] is not None
        assert results["pr_draft"] is not None

    async def test_planning_agent_error_propagates(
        self,
        workflow_agent: ContributionWorkflowAgent,
        mock_planning_agent: AsyncMock,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """Errors thrown by the planning agent propagate up."""
        mock_planning_agent.generate_plan.side_effect = RuntimeError("LLM error")

        with pytest.raises(RuntimeError) as exc_info:
            await workflow_agent.execute_workflow(
                issue=sample_issue,
                repo_metadata=sample_repo_metadata,
                relevant_code=[],
                issue_type=IssueType.BUG,
            )
        assert "LLM error" in str(exc_info.value)

    async def test_test_generation_agent_error_propagates(
        self,
        workflow_agent: ContributionWorkflowAgent,
        mock_test_gen_agent: AsyncMock,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """Errors thrown by the test generation agent propagate up."""
        mock_test_gen_agent.generate_tests.side_effect = RuntimeError("Test gen error")

        with pytest.raises(RuntimeError) as exc_info:
            await workflow_agent.execute_workflow(
                issue=sample_issue,
                repo_metadata=sample_repo_metadata,
                relevant_code=[],
                issue_type=IssueType.BUG,
            )
        assert "Test gen error" in str(exc_info.value)

    async def test_pr_agent_error_propagates(
        self,
        workflow_agent: ContributionWorkflowAgent,
        mock_pr_agent: AsyncMock,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """Errors thrown by the PR agent propagate up."""
        mock_pr_agent.generate_pr_draft.side_effect = RuntimeError("PR draft error")

        with pytest.raises(RuntimeError) as exc_info:
            await workflow_agent.execute_workflow(
                issue=sample_issue,
                repo_metadata=sample_repo_metadata,
                relevant_code=[],
                issue_type=IssueType.BUG,
            )
        assert "PR draft error" in str(exc_info.value)
