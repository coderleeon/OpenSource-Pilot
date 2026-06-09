"""Unit tests for ContributionWorkflowService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.code_analysis_agent import CodeAnalysisAgent
from app.agents.contribution_workflow_agent import ContributionWorkflowAgent
from app.agents.issue_agent import IssueAgent
from app.agents.repo_agent import RepoAgent
from app.core.exceptions import (
    GitHubAPIError,
    IndexingError,
    IssueNotFoundError,
    LLMParseError,
    OpenSourcePilotError,
    RepoNotFoundError,
    SearchError,
    StructureParseError,
)
from app.models.issue import ContributionPlan, GeneratedTests, GitHubIssue, IssueType, PRDraft
from app.models.repo import FileNode, RepoMetadata
from app.services.contribution_workflow_service import ContributionWorkflowService


@pytest.fixture()
def mock_repo_agent(sample_repo_metadata: RepoMetadata) -> AsyncMock:
    agent = AsyncMock(spec=RepoAgent)
    agent.analyze = AsyncMock(return_value=sample_repo_metadata)
    return agent


@pytest.fixture()
def mock_issue_agent(sample_issue: GitHubIssue) -> AsyncMock:
    agent = AsyncMock(spec=IssueAgent)
    agent.get_issue = AsyncMock(return_value=sample_issue)
    agent.classify = MagicMock(return_value=IssueType.BUG)
    return agent


@pytest.fixture()
def mock_code_agent() -> AsyncMock:
    agent = AsyncMock(spec=CodeAnalysisAgent)
    agent.index_repo = AsyncMock(return_value=5)
    agent.search = AsyncMock(
        return_value=[
            {
                "text": "class Flask:\n    pass",
                "file_path": "src/app.py",
                "language": "Python",
                "chunk_index": 0,
                "distance": 0.15,
            }
        ]
    )
    return agent


@pytest.fixture()
def mock_workflow_agent(
    sample_contribution_plan: ContributionPlan,
    sample_generated_tests: GeneratedTests,
    sample_pr_draft: PRDraft,
) -> AsyncMock:
    agent = AsyncMock(spec=ContributionWorkflowAgent)
    agent.execute_workflow = AsyncMock(
        return_value={
            "contribution_plan": sample_contribution_plan,
            "generated_tests": sample_generated_tests,
            "pr_draft": sample_pr_draft,
        }
    )
    return agent


@pytest.fixture()
def workflow_service(
    mock_repo_agent: AsyncMock,
    mock_issue_agent: AsyncMock,
    mock_code_agent: AsyncMock,
    mock_workflow_agent: AsyncMock,
) -> ContributionWorkflowService:
    return ContributionWorkflowService(
        repo_agent=mock_repo_agent,  # type: ignore[arg-type]
        issue_agent=mock_issue_agent,  # type: ignore[arg-type]
        code_analysis_agent=mock_code_agent,  # type: ignore[arg-type]
        workflow_agent=mock_workflow_agent,  # type: ignore[arg-type]
    )


class TestContributionWorkflowService:
    async def test_run_complete_workflow_bug(
        self,
        workflow_service: ContributionWorkflowService,
        mock_repo_agent: AsyncMock,
        mock_issue_agent: AsyncMock,
        mock_code_agent: AsyncMock,
        mock_workflow_agent: AsyncMock,
    ) -> None:
        """Complete workflow coordinates all steps for a bug issue."""
        result = await workflow_service.run_complete_workflow(
            repo_url="https://github.com/pallets/flask",
            issue_number=5420,
        )

        assert result["repository"]["full_name"] == "pallets/flask"
        assert result["issue"]["number"] == 5420
        assert result["classification"]["issue_type"] == "bug"
        assert len(result["search_results"]) == 1
        assert result["contribution_plan"]["plan_type"] == "contribution"
        assert result["generated_tests"] is not None
        assert result["pr_draft"] is not None
        assert result["metadata"]["status"] == "completed"
        assert result["metadata"]["duration_seconds"] > 0

        # Verify calls
        mock_repo_agent.analyze.assert_called_once_with("https://github.com/pallets/flask")
        mock_issue_agent.get_issue.assert_called_once_with("https://github.com/pallets/flask", 5420)
        mock_issue_agent.classify.assert_called_once()
        mock_code_agent.index_repo.assert_called_once()
        mock_code_agent.search.assert_called_once()
        mock_workflow_agent.execute_workflow.assert_called_once()

    async def test_run_complete_workflow_feature_request(
        self,
        workflow_service: ContributionWorkflowService,
        mock_issue_agent: MagicMock,
    ) -> None:
        """Runs workflow for a feature request (needs contribution plan path)."""
        mock_issue_agent.classify.return_value = IssueType.FEATURE_REQUEST

        result = await workflow_service.run_complete_workflow(
            repo_url="https://github.com/pallets/flask",
            issue_number=5420,
        )
        assert result["classification"]["issue_type"] == "feature_request"
        assert result["generated_tests"] is not None

    async def test_run_complete_workflow_documentation(
        self,
        workflow_service: ContributionWorkflowService,
        mock_issue_agent: MagicMock,
    ) -> None:
        """Runs workflow for a documentation issue (needs contribution plan path)."""
        mock_issue_agent.classify.return_value = IssueType.DOCUMENTATION

        result = await workflow_service.run_complete_workflow(
            repo_url="https://github.com/pallets/flask",
            issue_number=5420,
        )
        assert result["classification"]["issue_type"] == "documentation"
        assert result["generated_tests"] is not None

    async def test_run_complete_workflow_question(
        self,
        workflow_service: ContributionWorkflowService,
        mock_issue_agent: AsyncMock,
        mock_code_agent: AsyncMock,
        mock_workflow_agent: AsyncMock,
        sample_contribution_plan: ContributionPlan,
    ) -> None:
        """Question branches bypass index, search, test, and PR generation."""
        mock_issue_agent.classify.return_value = IssueType.QUESTION
        sample_contribution_plan.plan_type = "answer"
        sample_contribution_plan.issue_type = "question"

        mock_workflow_agent.execute_workflow.return_value = {
            "contribution_plan": sample_contribution_plan,
            "generated_tests": None,
            "pr_draft": None,
        }

        result = await workflow_service.run_complete_workflow(
            repo_url="https://github.com/pallets/flask",
            issue_number=5420,
        )

        assert result["classification"]["issue_type"] == "question"
        assert result["search_results"] == []
        assert result["relevant_files"] == []
        assert result["generated_tests"] is None
        assert result["pr_draft"] is None

        # Verify index/search skipped
        mock_code_agent.index_repo.assert_not_called()
        mock_code_agent.search.assert_not_called()

    async def test_run_complete_workflow_discussion(
        self,
        workflow_service: ContributionWorkflowService,
        mock_issue_agent: AsyncMock,
        mock_code_agent: AsyncMock,
        mock_workflow_agent: AsyncMock,
        sample_contribution_plan: ContributionPlan,
    ) -> None:
        """Discussion branches bypass indexing, search, tests, and PR drafts."""
        mock_issue_agent.classify.return_value = IssueType.DISCUSSION
        sample_contribution_plan.plan_type = "answer"
        sample_contribution_plan.issue_type = "discussion"

        mock_workflow_agent.execute_workflow.return_value = {
            "contribution_plan": sample_contribution_plan,
            "generated_tests": None,
            "pr_draft": None,
        }

        result = await workflow_service.run_complete_workflow(
            repo_url="https://github.com/pallets/flask",
            issue_number=5420,
        )

        assert result["classification"]["issue_type"] == "discussion"
        assert result["search_results"] == []
        assert result["generated_tests"] is None
        mock_code_agent.search.assert_not_called()

    async def test_run_complete_workflow_unknown(
        self,
        workflow_service: ContributionWorkflowService,
        mock_issue_agent: MagicMock,
    ) -> None:
        """UNKNOWN type defaults to the contribution plan workflow."""
        mock_issue_agent.classify.return_value = IssueType.UNKNOWN

        result = await workflow_service.run_complete_workflow(
            repo_url="https://github.com/pallets/flask",
            issue_number=5420,
        )
        assert result["classification"]["issue_type"] == "unknown"
        assert result["generated_tests"] is not None

    async def test_empty_repository_raises_exception(
        self,
        workflow_service: ContributionWorkflowService,
        mock_repo_agent: AsyncMock,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """An empty repository triggers a StructureParseError and stops execution."""
        sample_repo_metadata.file_tree = FileNode(name="flask", path="", is_dir=True, children=[])

        with pytest.raises(StructureParseError) as exc_info:
            await workflow_service.run_complete_workflow(
                repo_url="https://github.com/pallets/flask",
                issue_number=5420,
            )
        assert "empty" in str(exc_info.value).lower()

    async def test_github_api_error_propagated(
        self,
        workflow_service: ContributionWorkflowService,
        mock_issue_agent: AsyncMock,
    ) -> None:
        """Standard OpenSourcePilotError instances are propagated without modifications."""
        mock_issue_agent.get_issue.side_effect = GitHubAPIError("Rate limit exceeded")

        with pytest.raises(GitHubAPIError):
            await workflow_service.run_complete_workflow(
                repo_url="https://github.com/pallets/flask",
                issue_number=5420,
            )

    async def test_unexpected_error_wrapped(
        self,
        workflow_service: ContributionWorkflowService,
        mock_issue_agent: AsyncMock,
    ) -> None:
        """Unexpected Python errors are wrapped in a generic OpenSourcePilotError."""
        mock_issue_agent.get_issue.side_effect = ValueError("Runtime fail")

        with pytest.raises(OpenSourcePilotError) as exc_info:
            await workflow_service.run_complete_workflow(
                repo_url="https://github.com/pallets/flask",
                issue_number=5420,
            )
        assert "unexpected" in exc_info.value.message.lower()

    async def test_indexing_error_propagates(
        self,
        workflow_service: ContributionWorkflowService,
        mock_code_agent: AsyncMock,
    ) -> None:
        """ChromaDB indexing error propagates correctly."""
        mock_code_agent.index_repo.side_effect = IndexingError("Chroma fail")

        with pytest.raises(IndexingError):
            await workflow_service.run_complete_workflow(
                repo_url="https://github.com/pallets/flask",
                issue_number=5420,
            )

    async def test_search_error_propagates(
        self,
        workflow_service: ContributionWorkflowService,
        mock_code_agent: AsyncMock,
    ) -> None:
        """Search query errors propagate directly."""
        mock_code_agent.search.side_effect = SearchError("Query fail")

        with pytest.raises(SearchError):
            await workflow_service.run_complete_workflow(
                repo_url="https://github.com/pallets/flask",
                issue_number=5420,
            )

    async def test_workflow_agent_llm_parse_error_propagates(
        self,
        workflow_service: ContributionWorkflowService,
        mock_workflow_agent: AsyncMock,
    ) -> None:
        """LLM parse error inside downstream agents propagates directly."""
        mock_workflow_agent.execute_workflow.side_effect = LLMParseError("Bad JSON returned")

        with pytest.raises(LLMParseError):
            await workflow_service.run_complete_workflow(
                repo_url="https://github.com/pallets/flask",
                issue_number=5420,
            )

    async def test_response_contains_estimated_effort(
        self,
        workflow_service: ContributionWorkflowService,
    ) -> None:
        """Verify the top-level estimated_effort reflects the plan's estimated_effort."""
        result = await workflow_service.run_complete_workflow(
            repo_url="https://github.com/pallets/flask",
            issue_number=5420,
        )
        assert result["estimated_effort"] == "2-4 hours"  # from sample_contribution_plan

    async def test_issue_not_found_propagated(
        self,
        workflow_service: ContributionWorkflowService,
        mock_issue_agent: AsyncMock,
    ) -> None:
        """Verify that issue not found exception propagates."""
        mock_issue_agent.get_issue.side_effect = IssueNotFoundError("Issue 123 not found")

        with pytest.raises(IssueNotFoundError):
            await workflow_service.run_complete_workflow(
                repo_url="https://github.com/pallets/flask",
                issue_number=123,
            )
