"""Integration tests for the Open Source Radar endpoints.

Uses FastAPI's TestClient with dependency_overrides to inject a mock RadarService.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.services.radar_service import RadarService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_radar_service() -> AsyncMock:
    """Mock RadarService returning canned responses for radar operations."""
    svc = AsyncMock(spec=RadarService)
    
    # Mock discover
    svc.discover = AsyncMock(
        return_value=[{
            "repository": {
                "name": "flask",
                "full_name": "pallets/flask",
                "description": "Python microframework",
                "url": "https://github.com/pallets/flask",
                "stars": 60000,
                "forks": 15000,
                "open_issues_count": 50,
                "primary_language": "Python",
                "topics": ["web", "framework"],
            },
            "issue": {
                "number": 123,
                "title": "Fix some bug",
                "body": "This is a bug description",
                "labels": ["bug", "easy"],
                "url": "https://github.com/pallets/flask/issues/123",
                "comments_count": 2,
                "author": "john_doe",
                "created_at": "2026-06-22T00:00:00Z",
                "age_days": 10,
            },
            "fit_analysis": {
                "fit_score": 90,
                "difficulty": "Easy",
                "learning_value": "High",
                "reason": "Good match",
            },
            "merge_probability": {
                "merge_probability": 85,
                "confidence": "High",
                "explanation": "Active maintainers",
            },
            "repo_health": {
                "maintainer_activity": 90,
                "release_frequency": 80,
                "open_issue_trends": "Stable",
                "contribution_velocity": 85,
                "community_engagement": 90,
                "health_explanation": "Healthy project",
            },
            "missing_features": [
                {
                    "feature_name": "Export chats",
                    "description": "Export chats to json",
                    "reasoning": "Useful for users",
                }
            ],
        }]
    )
    
    # Mock missing features
    svc.get_missing_features = AsyncMock(
        return_value={
            "repo_name": "flask",
            "missing_features": [
                {
                    "feature_name": "Export chats",
                    "description": "Export chats to json",
                    "reasoning": "Useful for users",
                }
            ],
        }
    )
    
    # Mock repo health
    svc.get_repo_health = AsyncMock(
        return_value={
            "repo_name": "flask",
            "repo_health": {
                "maintainer_activity": 90,
                "release_frequency": 80,
                "open_issue_trends": "Stable",
                "contribution_velocity": 85,
                "community_engagement": 90,
                "health_explanation": "Healthy project",
            },
        }
    )
    
    return svc


@pytest.fixture()
def test_client(
    mock_radar_service: AsyncMock,
    test_settings,
) -> TestClient:
    """TestClient that:
    - patches ``get_settings`` so the lifespan uses ``test_settings``
    - injects the mock radar service via dependency override
    """
    from app.api.deps import get_radar_service
    from app.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()  # clear the lru_cache so our mock takes effect

    with patch("app.main.get_settings", return_value=test_settings):
        app = create_app()
        app.dependency_overrides[get_radar_service] = lambda: mock_radar_service

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    app.dependency_overrides.clear()
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRadarEndpoints:
    def test_discover_opportunities_returns_200(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/radar/discover",
            json={
                "skills": ["Python"],
                "technologies": ["FastAPI"],
                "interests": ["database"],
                "experience_level": "beginner",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "opportunities" in data
        assert len(data["opportunities"]) == 1
        opp = data["opportunities"][0]
        assert opp["repository"]["name"] == "flask"
        assert opp["issue"]["number"] == 123
        assert opp["fit_analysis"]["fit_score"] == 90

    def test_discover_missing_params_still_default_valid_returns_200(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/radar/discover",
            json={},
        )
        # Verify it succeeds since default empty lists are allowed
        assert response.status_code == 200

    def test_get_missing_features_returns_200(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/radar/missing-features",
            json={
                "repo_url": "https://github.com/pallets/flask",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["repo_name"] == "flask"
        assert len(data["missing_features"]) == 1
        assert data["missing_features"][0]["feature_name"] == "Export chats"

    def test_get_missing_features_invalid_url_returns_422(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/radar/missing-features",
            json={
                "repo_url": "https://gitlab.com/some/repo",
            },
        )
        assert response.status_code == 422

    def test_get_repo_health_returns_200(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/radar/repo-health",
            json={
                "repo_url": "https://github.com/pallets/flask",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["repo_name"] == "flask"
        assert data["repo_health"]["maintainer_activity"] == 90
        assert data["repo_health"]["open_issue_trends"] == "Stable"

    def test_get_repo_health_invalid_url_returns_422(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/radar/repo-health",
            json={
                "repo_url": "https://gitlab.com/some/repo",
            },
        )
        assert response.status_code == 422
