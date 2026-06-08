"""Unit tests for TestGenerationAgent."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.agents.test_generation_agent import TestGenerationAgent, _detect_framework
from app.core.exceptions import LLMParseError
from app.models.issue import ContributionPlan, GeneratedTests, GitHubIssue
from app.models.repo import RepoMetadata, TechStack


# ---------------------------------------------------------------------------
# Framework detection
# ---------------------------------------------------------------------------


class TestDetectFramework:
    def test_python_returns_pytest(self, sample_repo_metadata: RepoMetadata) -> None:
        assert _detect_framework(sample_repo_metadata) == "pytest"

    def test_javascript_returns_jest(self, sample_repo_metadata: RepoMetadata) -> None:
        sample_repo_metadata.tech_stack.languages = ["JavaScript"]
        assert _detect_framework(sample_repo_metadata) == "Jest"

    def test_typescript_returns_jest(self, sample_repo_metadata: RepoMetadata) -> None:
        sample_repo_metadata.tech_stack.languages = ["TypeScript"]
        assert _detect_framework(sample_repo_metadata) == "Jest"

    def test_go_returns_go_testing(self, sample_repo_metadata: RepoMetadata) -> None:
        sample_repo_metadata.tech_stack.languages = ["Go"]
        assert "Go" in _detect_framework(sample_repo_metadata)

    def test_rust_returns_rust_harness(self, sample_repo_metadata: RepoMetadata) -> None:
        sample_repo_metadata.tech_stack.languages = ["Rust"]
        result = _detect_framework(sample_repo_metadata)
        assert "Rust" in result or "built-in" in result

    def test_java_returns_junit(self, sample_repo_metadata: RepoMetadata) -> None:
        sample_repo_metadata.tech_stack.languages = ["Java"]
        assert "JUnit" in _detect_framework(sample_repo_metadata)

    def test_unknown_language_defaults_to_pytest(self, sample_repo_metadata: RepoMetadata) -> None:
        sample_repo_metadata.tech_stack.languages = ["COBOL"]
        assert _detect_framework(sample_repo_metadata) == "pytest"


# ---------------------------------------------------------------------------
# TestGenerationAgent.generate_tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_test_gen_client() -> AsyncMock:
    """Mock LLM returning a well-formed GeneratedTests JSON."""
    client = AsyncMock()
    client.complete_json = AsyncMock(
        return_value={
            "unit_tests": "import pytest\n\ndef test_session_expires():\n    assert True",
            "integration_tests": "import pytest\n\ndef test_session_integration():\n    assert True",
            "edge_cases": "import pytest\n\ndef test_session_empty_token():\n    assert True",
            "test_file_path": "tests/test_sessions.py",
            "framework": "pytest",
            "dependencies": ["pytest-mock"],
            "setup_notes": "Install dependencies with: pip install pytest pytest-mock",
        }
    )
    return client


@pytest.fixture()
def agent(mock_test_gen_client: AsyncMock) -> TestGenerationAgent:
    return TestGenerationAgent(llm_client=mock_test_gen_client)  # type: ignore[arg-type]


class TestGenerateTests:
    async def test_returns_generated_tests_instance(
        self,
        agent: TestGenerationAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_tests(
            issue=sample_issue,
            plan=sample_contribution_plan,
            relevant_code=[],
            repo_metadata=sample_repo_metadata,
        )
        assert isinstance(result, GeneratedTests)

    async def test_unit_tests_populated(
        self,
        agent: TestGenerationAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_tests(
            issue=sample_issue,
            plan=sample_contribution_plan,
            relevant_code=[],
            repo_metadata=sample_repo_metadata,
        )
        assert "def test_" in result.unit_tests

    async def test_integration_tests_populated(
        self,
        agent: TestGenerationAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_tests(
            issue=sample_issue,
            plan=sample_contribution_plan,
            relevant_code=[],
            repo_metadata=sample_repo_metadata,
        )
        assert result.integration_tests != ""

    async def test_edge_cases_populated(
        self,
        agent: TestGenerationAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_tests(
            issue=sample_issue,
            plan=sample_contribution_plan,
            relevant_code=[],
            repo_metadata=sample_repo_metadata,
        )
        assert result.edge_cases != ""

    async def test_framework_field_populated(
        self,
        agent: TestGenerationAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_tests(
            issue=sample_issue,
            plan=sample_contribution_plan,
            relevant_code=[],
            repo_metadata=sample_repo_metadata,
        )
        assert result.framework == "pytest"

    async def test_test_file_path_populated(
        self,
        agent: TestGenerationAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_tests(
            issue=sample_issue,
            plan=sample_contribution_plan,
            relevant_code=[],
            repo_metadata=sample_repo_metadata,
        )
        assert result.test_file_path.endswith(".py")

    async def test_dependencies_list(
        self,
        agent: TestGenerationAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        result = await agent.generate_tests(
            issue=sample_issue,
            plan=sample_contribution_plan,
            relevant_code=[],
            repo_metadata=sample_repo_metadata,
        )
        assert isinstance(result.dependencies, list)
        assert "pytest-mock" in result.dependencies

    async def test_llm_called_once(
        self,
        agent: TestGenerationAgent,
        mock_test_gen_client: AsyncMock,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        await agent.generate_tests(
            issue=sample_issue,
            plan=sample_contribution_plan,
            relevant_code=[],
            repo_metadata=sample_repo_metadata,
        )
        mock_test_gen_client.complete_json.assert_called_once()

    async def test_with_relevant_code_snippets(
        self,
        agent: TestGenerationAgent,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """Agent should work fine with populated code context."""
        relevant_code = [
            {
                "text": "def open_session(self, app, request):\n    pass",
                "file_path": "src/sessions.py",
                "language": "Python",
                "chunk_index": 0,
                "distance": 0.1,
            }
        ]
        result = await agent.generate_tests(
            issue=sample_issue,
            plan=sample_contribution_plan,
            relevant_code=relevant_code,
            repo_metadata=sample_repo_metadata,
        )
        assert isinstance(result, GeneratedTests)

    async def test_llm_parse_error_propagates(
        self,
        sample_issue: GitHubIssue,
        sample_contribution_plan: ContributionPlan,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        bad_client = AsyncMock()
        bad_client.complete_json = AsyncMock(side_effect=LLMParseError("bad json"))
        agent = TestGenerationAgent(llm_client=bad_client)  # type: ignore[arg-type]

        with pytest.raises(LLMParseError):
            await agent.generate_tests(
                issue=sample_issue,
                plan=sample_contribution_plan,
                relevant_code=[],
                repo_metadata=sample_repo_metadata,
            )

    async def test_answer_plan_handled_gracefully(
        self,
        agent: TestGenerationAgent,
        sample_issue: GitHubIssue,
        sample_repo_metadata: RepoMetadata,
    ) -> None:
        """Answer plans (question/discussion) should still produce a test output."""
        answer_plan = ContributionPlan(
            plan_type="answer",
            issue_type="question",
            problem_explanation="How does Flask handle sessions?",
            answer_explanation="Flask uses signed cookies.",
        )
        result = await agent.generate_tests(
            issue=sample_issue,
            plan=answer_plan,
            relevant_code=[],
            repo_metadata=sample_repo_metadata,
        )
        assert isinstance(result, GeneratedTests)
