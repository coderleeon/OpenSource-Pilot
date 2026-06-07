"""Shared pytest fixtures and test utilities.

Fixtures defined here are automatically available to all tests via conftest
discovery.  We use ``pytest-mock`` (``mocker``) for patching and
``httpx.AsyncClient`` (via ``pytest-asyncio``) for endpoint testing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.config import Settings
from app.models.issue import ContributionPlan, GitHubIssue, IssueRanking
from app.models.repo import FileNode, RepoMetadata, TechStack


# ---------------------------------------------------------------------------
# Settings override
# ---------------------------------------------------------------------------


@pytest.fixture()
def test_settings(tmp_path: Path) -> Settings:
    """Settings instance using tmp_path for storage to avoid polluting working dir."""
    return Settings(
        llm_provider="openrouter",
        openrouter_api_key="sk-or-test-key",
        openrouter_model="anthropic/claude-3.5-haiku",
        github_token="ghp_test",
        clone_base_dir=str(tmp_path / "clones"),
        chroma_persist_dir=str(tmp_path / "chroma"),
        max_files_to_index=10,
        log_level="DEBUG",
        log_format="console",
    )


# ---------------------------------------------------------------------------
# Domain model fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_file_tree() -> FileNode:
    """A minimal FileNode tree for testing."""
    return FileNode(
        name="flask",
        path="",
        is_dir=True,
        children=[
            FileNode(name="src", path="src", is_dir=True, children=[
                FileNode(
                    name="app.py",
                    path="src/app.py",
                    is_dir=False,
                    language="Python",
                    size_bytes=1024,
                ),
                FileNode(
                    name="sessions.py",
                    path="src/sessions.py",
                    is_dir=False,
                    language="Python",
                    size_bytes=2048,
                ),
            ]),
            FileNode(
                name="README.md",
                path="README.md",
                is_dir=False,
                language="Markdown",
                size_bytes=512,
            ),
        ],
    )


@pytest.fixture()
def sample_tech_stack() -> TechStack:
    return TechStack(
        languages=["Python"],
        frameworks=["Flask"],
        tools=["Docker", "GitHub Actions"],
        package_managers=["pip"],
    )


@pytest.fixture()
def sample_repo_metadata(
    sample_file_tree: FileNode,
    sample_tech_stack: TechStack,
    tmp_path: Path,
) -> RepoMetadata:
    """A fully populated RepoMetadata for testing agents and services."""
    return RepoMetadata(
        name="flask",
        full_name="pallets/flask",
        description="The Python micro framework for building web applications.",
        url="https://github.com/pallets/flask",
        clone_url="https://github.com/pallets/flask.git",
        default_branch="main",
        primary_language="Python",
        topics=["flask", "python", "web"],
        stars=67000,
        forks=16000,
        open_issues_count=40,
        license_name="BSD-3-Clause",
        has_contributing_guide=True,
        has_readme=True,
        local_path=str(tmp_path / "flask"),
        file_tree=sample_file_tree,
        tech_stack=sample_tech_stack,
        readme_content="# Flask\nFlask is a lightweight WSGI web application framework.",
        contributing_content="# Contributing\nPlease read the contributing guide.",
    )


@pytest.fixture()
def sample_issue() -> GitHubIssue:
    return GitHubIssue(
        number=5420,
        title="Fix session timeout not working correctly",
        body=(
            "When a user session expires, the timeout is not handled correctly. "
            "The session remains active beyond the configured timeout period."
        ),
        labels=["bug", "help wanted"],
        state="open",
        created_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        updated_at=datetime(2024, 2, 1, tzinfo=timezone.utc),
        url="https://github.com/pallets/flask/issues/5420",
        comments_count=5,
        author="contributor123",
    )


@pytest.fixture()
def sample_contribution_plan() -> ContributionPlan:
    return ContributionPlan(
        plan_type="contribution",
        issue_type="bug",
        problem_explanation="Sessions are not expiring at the configured timeout.",
        root_cause_hypothesis=(
            "The session expiry check in sessions.py does not account for "
            "timezone-aware datetimes."
        ),
        implementation_steps=[
            "Step 1: Locate session expiry logic in src/sessions.py",
            "Step 2: Add timezone-aware datetime comparison",
            "Step 3: Write a unit test for the fixed behaviour",
        ],
        files_to_modify=["src/sessions.py"],
        relevant_concepts=["Python datetime", "WSGI sessions", "Flask session interface"],
        estimated_effort="2-4 hours",
        references=["https://flask.palletsprojects.com/en/stable/api/#flask.session"],
    )



# ---------------------------------------------------------------------------
# Mock LLM client
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_llm_client(sample_contribution_plan: ContributionPlan) -> AsyncMock:
    """AsyncMock LLM client that returns predictable JSON responses."""
    import json

    client = AsyncMock()
    client.complete = AsyncMock(return_value="Mocked LLM response")
    client.complete_json = AsyncMock(
        return_value={
            # Contribution plan fields
            "plan_type": "contribution",
            "issue_type": "bug",
            "problem_explanation": sample_contribution_plan.problem_explanation,
            "root_cause_hypothesis": sample_contribution_plan.root_cause_hypothesis,
            "implementation_steps": sample_contribution_plan.implementation_steps,
            "files_to_modify": sample_contribution_plan.files_to_modify,
            "relevant_concepts": sample_contribution_plan.relevant_concepts,
            "estimated_effort": sample_contribution_plan.estimated_effort,
            "references": sample_contribution_plan.references,
            # Answer plan fields (present but empty for contribution plans)
            "answer_explanation": "",
            "key_questions": [],
            "suggested_resources": [],
            # For summarize_repo
            "readme_summary": "Flask is a lightweight Python web framework.",
            "contribution_guide_summary": "Submit PRs with tests and follow PEP 8.",
            # For generate_architecture_summary
            "architecture_summary": (
                "Flask follows a classic library architecture with a flat src layout. "
                "The src/ directory holds the core framework modules while tests/ contains "
                "the test suite. Configuration files in the root enable standard Python "
                "packaging and CI tooling."
            ),
        }
    )
    return client



# ---------------------------------------------------------------------------
# Mock GitHub tool
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_github_tool(sample_issue: GitHubIssue) -> AsyncMock:
    """AsyncMock GitHubAPITool."""
    tool = AsyncMock()
    mock_repo = MagicMock()
    mock_repo.name = "flask"
    mock_repo.full_name = "pallets/flask"
    mock_repo.description = "The Python micro framework."
    mock_repo.html_url = "https://github.com/pallets/flask"
    mock_repo.clone_url = "https://github.com/pallets/flask.git"
    mock_repo.default_branch = "main"
    mock_repo.language = "Python"
    mock_repo.stargazers_count = 67000
    mock_repo.forks_count = 16000
    mock_repo.open_issues_count = 40
    mock_repo.license = MagicMock(name="BSD-3-Clause")
    mock_repo.license.name = "BSD-3-Clause"
    mock_repo.get_topics = MagicMock(return_value=["flask", "python"])

    tool.get_gh_repo = AsyncMock(return_value=mock_repo)
    tool.get_issue = AsyncMock(return_value=sample_issue)
    tool.get_issues = AsyncMock(return_value=[sample_issue])
    tool.get_file_content = AsyncMock(return_value=None)
    return tool


# ---------------------------------------------------------------------------
# Mock ChromaTool
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_chroma_tool() -> MagicMock:
    """MagicMock ChromaTool with sensible defaults."""
    tool = MagicMock()
    tool.collection_exists.return_value = False
    tool.upsert_chunks.return_value = 42
    tool.query.return_value = [
        {
            "text": "def open_session(self, app, request):\n    ...",
            "file_path": "src/sessions.py",
            "language": "Python",
            "chunk_index": 0,
            "distance": 0.12,
        }
    ]
    tool.delete_collection.return_value = None
    return tool
