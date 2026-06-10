"""Integration tests verifying issue retrieval states."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import IssueNotFoundError
from app.services.contribution_workflow_service import ContributionWorkflowService
from app.services.issue_service import IssueService


@pytest.fixture()
def mock_issue_service() -> AsyncMock:
    """Mock IssueService."""
    return AsyncMock(spec=IssueService)


@pytest.fixture()
def mock_workflow_service() -> AsyncMock:
    """Mock ContributionWorkflowService."""
    return AsyncMock(spec=ContributionWorkflowService)


@pytest.fixture()
def test_client(
    mock_workflow_service: AsyncMock,
    mock_issue_service: AsyncMock,
    test_settings,
) -> TestClient:
    """TestClient with dependency overrides."""
    from app.api.deps import get_contribution_workflow_service, get_issue_service
    from app.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()

    with patch("app.main.get_settings", return_value=test_settings):
        app = create_app()
        app.dependency_overrides[get_contribution_workflow_service] = lambda: mock_workflow_service
        app.dependency_overrides[get_issue_service] = lambda: mock_issue_service

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    app.dependency_overrides.clear()
    get_settings.cache_clear()


class TestIssueHandlingLifecycle:
    def test_repo_exists_issue_exists(
        self,
        test_client: TestClient,
        mock_workflow_service: AsyncMock,
    ) -> None:
        """Scenario A: Repository exists, issue exists. Expects 200 OK."""
        mock_workflow_service.run_complete_workflow.return_value = {
            "repository": {
                "name": "flask",
                "full_name": "pallets/flask",
                "description": "Flask web framework",
                "url": "https://github.com/pallets/flask",
                "primary_language": "Python",
                "default_branch": "main",
            },
            "issue": {
                "number": 123,
                "title": "Existing Bug",
                "body": "Describe the session issue...",
                "labels": ["bug"],
                "state": "open",
                "url": "https://github.com/pallets/flask/issues/123",
                "comments_count": 0,
                "author": "tester",
                "created_at": "2026-06-08T12:00:00Z",
            },
            "classification": {
                "issue_type": "bug",
                "issue_type_display": "Bug Report",
                "difficulty_estimate": "easy",
                "suitability_score": 8.0,
                "beginner_friendly": True,
            },
            "relevant_files": ["src/sessions.py"],
            "search_results": [
                {
                    "file_path": "src/sessions.py",
                    "language": "Python",
                    "snippet": "def open_session(): pass",
                    "relevance_distance": 0.12,
                }
            ],
            "contribution_plan": {
                "plan_type": "contribution",
                "issue_type": "bug",
                "problem_explanation": "Sessions fail to expire",
                "root_cause_hypothesis": "naive datetime used",
                "implementation_steps": ["step 1"],
                "files_to_modify": ["src/sessions.py"],
                "relevant_concepts": ["WSGI"],
                "estimated_effort": "2 hours",
                "references": [],
            },
            "generated_tests": None,
            "pr_draft": None,
            "estimated_effort": None,
            "metadata": {
                "status": "completed",
                "started_at": "2026-06-08T12:00:00Z",
                "completed_at": "2026-06-08T12:00:02Z",
                "duration_seconds": 1.0,
                "errors": [],
            },
        }

        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "issue_number": 123,
            },
        )
        assert response.status_code == 200
        assert response.json()["repository"]["name"] == "flask"
        assert response.json()["issue"]["number"] == 123

        mock_workflow_service.run_complete_workflow.assert_called_once_with(
            repo_url="https://github.com/pallets/flask",
            issue_number=123,
        )

    def test_repo_exists_issue_does_not_exist(
        self,
        test_client: TestClient,
        mock_workflow_service: AsyncMock,
    ) -> None:
        """Scenario B: Repository exists, issue does not exist. Expects HTTP 404."""
        mock_workflow_service.run_complete_workflow.side_effect = IssueNotFoundError(
            "Issue #999 was not found in this repository."
        )

        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "issue_number": 999,
            },
        )
        assert response.status_code == 404
        assert response.json() == {
            "detail": "Issue #999 was not found in this repository."
        }

        mock_workflow_service.run_complete_workflow.assert_called_once_with(
            repo_url="https://github.com/pallets/flask",
            issue_number=999,
        )

    def test_repo_has_zero_issues(
        self,
        test_client: TestClient,
        mock_issue_service: AsyncMock,
    ) -> None:
        """Scenario C: Repository has zero issues. Expects empty list response."""
        mock_issue_service.list_issues.return_value = {
            "repo_url": "https://github.com/pallets/flask",
            "total_returned": 0,
            "issues": [],
        }

        response = test_client.post(
            "/api/v1/issue/list",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "limit": 30,
            },
        )
        assert response.status_code == 200
        assert response.json()["total_returned"] == 0
        assert response.json()["issues"] == []
