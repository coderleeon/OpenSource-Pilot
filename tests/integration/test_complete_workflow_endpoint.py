"""Integration tests for the complete contributor workflow endpoint."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import GitHubAPIError, IndexingError, IssueNotFoundError, OpenSourcePilotError, RepoNotFoundError, SearchError
from app.services.contribution_workflow_service import ContributionWorkflowService


@pytest.fixture()
def mock_workflow_service() -> AsyncMock:
    """Mock ContributionWorkflowService returning a canned workflow response."""
    svc = AsyncMock(spec=ContributionWorkflowService)
    svc.run_complete_workflow = AsyncMock(
        return_value={
            "repository": {
                "name": "flask",
                "full_name": "pallets/flask",
                "description": "Flask web framework",
                "url": "https://github.com/pallets/flask",
                "primary_language": "Python",
                "default_branch": "main",
            },
            "issue": {
                "number": 5420,
                "title": "Fix session timeout",
                "body": "Describe the session issue...",
                "labels": ["bug"],
                "state": "open",
                "url": "https://github.com/pallets/flask/issues/5420",
                "comments_count": 3,
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
            "generated_tests": {
                "framework": "pytest",
                "test_file_path": "tests/test_sessions.py",
                "unit_tests": "def test_session(): pass",
                "integration_tests": "",
                "edge_cases": "",
                "dependencies": [],
                "setup_notes": "",
            },
            "pr_draft": {
                "title": "fix(sessions): use timezone-aware expiry",
                "summary": "Fix session timeout bug.",
                "testing_checklist": ["Run pytest"],
                "reviewer_notes": "",
                "labels_suggested": ["bug"],
                "draft_body": "PR draft body",
            },
            "estimated_effort": "2 hours",
            "metadata": {
                "status": "completed",
                "started_at": "2026-06-08T12:00:00Z",
                "completed_at": "2026-06-08T12:00:05Z",
                "duration_seconds": 5.234,
                "errors": [],
            },
        }
    )
    return svc


@pytest.fixture()
def test_client(
    mock_workflow_service: AsyncMock,
    test_settings,
    tmp_path: Path,
) -> TestClient:
    """TestClient wrapping custom dependency override for get_contribution_workflow_service."""
    from app.api.deps import get_contribution_workflow_service
    from app.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()

    with patch("app.main.get_settings", return_value=test_settings):
        app = create_app()
        app.dependency_overrides[get_contribution_workflow_service] = lambda: mock_workflow_service

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    app.dependency_overrides.clear()
    get_settings.cache_clear()


class TestCompleteWorkflowEndpoint:
    def test_valid_request_returns_200(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "issue_number": 5420,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["repository"]["name"] == "flask"
        assert data["classification"]["issue_type"] == "bug"
        assert len(data["relevant_files"]) == 1
        assert data["contribution_plan"]["plan_type"] == "contribution"
        assert data["pr_draft"]["title"] == "fix(sessions): use timezone-aware expiry"
        assert data["metadata"]["status"] == "completed"

    def test_missing_repo_url_returns_422(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={"issue_number": 5420},
        )
        assert response.status_code == 422

    def test_missing_issue_number_returns_422(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={"repo_url": "https://github.com/pallets/flask"},
        )
        assert response.status_code == 422

    def test_non_github_url_returns_422(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={
                "repo_url": "https://gitlab.com/some/repo",
                "issue_number": 5420,
            },
        )
        assert response.status_code == 422

    def test_invalid_issue_number_bounds(self, test_client: TestClient) -> None:
        """Issue number must be >= 1."""
        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "issue_number": 0,
            },
        )
        assert response.status_code == 422

    def test_get_method_not_allowed(self, test_client: TestClient) -> None:
        """GET method is not supported on this endpoint."""
        response = test_client.get("/api/v1/issue/complete-workflow")
        assert response.status_code == 405

    def test_put_method_not_allowed(self, test_client: TestClient) -> None:
        """PUT method is not supported on this endpoint."""
        response = test_client.put(
            "/api/v1/issue/complete-workflow",
            json={"repo_url": "https://github.com/pallets/flask", "issue_number": 1},
        )
        assert response.status_code == 405

    def test_delete_method_not_allowed(self, test_client: TestClient) -> None:
        """DELETE method is not supported on this endpoint."""
        response = test_client.delete("/api/v1/issue/complete-workflow")
        assert response.status_code == 405

    def test_repo_not_found_returns_404(
        self,
        test_client: TestClient,
        mock_workflow_service: AsyncMock,
    ) -> None:
        mock_workflow_service.run_complete_workflow.side_effect = RepoNotFoundError("Repository not found")

        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={
                "repo_url": "https://github.com/nonexistent/repo",
                "issue_number": 1,
            },
        )
        assert response.status_code == 404
        assert response.json()["error"] == "RepoNotFoundError"

    def test_issue_not_found_returns_404(
        self,
        test_client: TestClient,
        mock_workflow_service: AsyncMock,
    ) -> None:
        mock_workflow_service.run_complete_workflow.side_effect = IssueNotFoundError("Issue #999 not found")

        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "issue_number": 999,
            },
        )
        assert response.status_code == 404
        assert response.json()["error"] == "IssueNotFoundError"

    def test_github_api_error_returns_502(
        self,
        test_client: TestClient,
        mock_workflow_service: AsyncMock,
    ) -> None:
        mock_workflow_service.run_complete_workflow.side_effect = GitHubAPIError("Rate limit exceeded")

        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "issue_number": 5420,
            },
        )
        assert response.status_code == 502
        assert response.json()["error"] == "GitHubAPIError"

    def test_indexing_error_returns_500(
        self,
        test_client: TestClient,
        mock_workflow_service: AsyncMock,
    ) -> None:
        """ChromaDB indexing failures map to 500 error."""
        mock_workflow_service.run_complete_workflow.side_effect = IndexingError("Chroma persist error")

        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "issue_number": 5420,
            },
        )
        assert response.status_code == 500
        assert response.json()["error"] == "IndexingError"

    def test_search_error_returns_500(
        self,
        test_client: TestClient,
        mock_workflow_service: AsyncMock,
    ) -> None:
        """ChromaDB query failures map to 500 error."""
        mock_workflow_service.run_complete_workflow.side_effect = SearchError("Chroma query failed")

        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "issue_number": 5420,
            },
        )
        assert response.status_code == 500
        assert response.json()["error"] == "SearchError"

    def test_unexpected_workflow_error_returns_500(
        self,
        test_client: TestClient,
        mock_workflow_service: AsyncMock,
    ) -> None:
        """Unexpected OpenSourcePilotError instances map to 500 error."""
        mock_workflow_service.run_complete_workflow.side_effect = OpenSourcePilotError("Unknown error occurred")

        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "issue_number": 5420,
            },
        )
        assert response.status_code == 500
        assert response.json()["error"] == "OpenSourcePilotError"

    def test_question_returns_null_for_tests_and_pr(
        self,
        test_client: TestClient,
        mock_workflow_service: AsyncMock,
    ) -> None:
        """Answer plans (e.g. for questions) serialize tests and PR drafts as null."""
        mock_workflow_service.run_complete_workflow.return_value = {
            "repository": {
                "name": "flask",
                "full_name": "pallets/flask",
                "url": "https://github.com/pallets/flask",
                "primary_language": "Python",
                "default_branch": "main",
            },
            "issue": {
                "number": 5420,
                "title": "Question about session limits",
                "body": "How long is a session?",
                "labels": ["question"],
                "state": "open",
                "url": "https://github.com/pallets/flask/issues/5420",
                "comments_count": 0,
                "author": "tester",
                "created_at": "2026-06-08T12:00:00Z",
            },
            "classification": {
                "issue_type": "question",
                "issue_type_display": "Question",
                "difficulty_estimate": "easy",
                "suitability_score": 9.0,
                "beginner_friendly": True,
            },
            "relevant_files": [],
            "search_results": [],
            "contribution_plan": {
                "plan_type": "answer",
                "issue_type": "question",
                "problem_explanation": "Question on session limits",
                "answer_explanation": "Sessions last 31 days by default.",
                "key_questions": [],
                "suggested_resources": [],
            },
            "generated_tests": None,
            "pr_draft": None,
            "estimated_effort": None,
            "metadata": {
                "status": "completed",
                "started_at": "2026-06-08T12:00:00Z",
                "completed_at": "2026-06-08T12:00:02Z",
                "duration_seconds": 2.112,
                "errors": [],
            },
        }

        response = test_client.post(
            "/api/v1/issue/complete-workflow",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "issue_number": 5420,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["generated_tests"] is None
        assert data["pr_draft"] is None
        assert data["estimated_effort"] is None
        assert data["relevant_files"] == []
        assert data["search_results"] == []
        assert data["contribution_plan"]["plan_type"] == "answer"
