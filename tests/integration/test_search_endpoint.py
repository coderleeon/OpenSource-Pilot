"""Integration tests for the semantic code search endpoint.

Uses FastAPI's TestClient with dependency_overrides to inject a mock
SearchService. We also patch ``get_settings`` so the full app lifespan
runs without real API keys.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.services.search_service import SearchService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_search_result(
    file_path: str = "src/sessions.py",
    snippet: str = "def open_session(): pass",
    distance: float = 0.15,
) -> dict:  # type: ignore[type-arg]
    return {
        "file_path": file_path,
        "language": "Python",
        "snippet": snippet,
        "relevance_distance": distance,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_search_service() -> AsyncMock:
    """Mock SearchService returning two canned search results."""
    svc = AsyncMock(spec=SearchService)
    svc.search_code = AsyncMock(
        return_value={
            "repo_name": "pallets/flask",
            "query": "session timeout",
            "total_results": 2,
            "results": [
                _make_search_result("src/sessions.py", "def open_session(): pass", 0.12),
                _make_search_result("src/app.py", "class Flask: pass", 0.25),
            ],
        }
    )
    return svc


@pytest.fixture()
def test_client(
    mock_search_service: AsyncMock,
    test_settings,  # from conftest — has a fake API key
    tmp_path: Path,
) -> TestClient:
    """TestClient that:
    - patches ``get_settings`` so the lifespan uses ``test_settings``
    - injects the mock search service via dependency override
    """
    from app.api.deps import get_search_service
    from app.config import get_settings
    from app.main import create_app

    # test_settings already has a tmp chroma/clone dir and fake API key
    get_settings.cache_clear()  # clear the lru_cache so our mock takes effect

    with patch("app.main.get_settings", return_value=test_settings):
        app = create_app()
        app.dependency_overrides[get_search_service] = lambda: mock_search_service

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    app.dependency_overrides.clear()
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSearchCodeEndpoint:
    def test_valid_request_returns_200(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "query": "session timeout",
                "n_results": 5,
            },
        )
        assert response.status_code == 200

    def test_response_has_repo_name(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={"repo_url": "https://github.com/pallets/flask", "query": "session"},
        )
        data = response.json()
        assert "repo_name" in data
        assert data["repo_name"] == "pallets/flask"

    def test_response_has_results_list(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={"repo_url": "https://github.com/pallets/flask", "query": "session"},
        )
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_response_has_total_results(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={"repo_url": "https://github.com/pallets/flask", "query": "session"},
        )
        data = response.json()
        assert "total_results" in data
        assert data["total_results"] == len(data["results"])

    def test_each_result_has_file_path(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={"repo_url": "https://github.com/pallets/flask", "query": "session"},
        )
        for result in response.json()["results"]:
            assert "file_path" in result

    def test_each_result_has_snippet(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={"repo_url": "https://github.com/pallets/flask", "query": "session"},
        )
        for result in response.json()["results"]:
            assert "snippet" in result

    def test_each_result_has_relevance_distance(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={"repo_url": "https://github.com/pallets/flask", "query": "session"},
        )
        for result in response.json()["results"]:
            assert "relevance_distance" in result

    def test_missing_repo_url_returns_422(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={"query": "session timeout"},
        )
        assert response.status_code == 422

    def test_missing_query_returns_422(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={"repo_url": "https://github.com/pallets/flask"},
        )
        assert response.status_code == 422

    def test_non_github_url_returns_422(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={
                "repo_url": "https://gitlab.com/some/repo",
                "query": "session timeout",
            },
        )
        assert response.status_code == 422

    def test_query_too_short_returns_422(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "query": "x",  # min_length=2
            },
        )
        assert response.status_code == 422

    def test_n_results_above_50_returns_422(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "query": "session",
                "n_results": 51,
            },
        )
        assert response.status_code == 422

    def test_n_results_below_1_returns_422(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "query": "session",
                "n_results": 0,
            },
        )
        assert response.status_code == 422

    def test_default_n_results_is_10(
        self,
        test_client: TestClient,
        mock_search_service: AsyncMock,
    ) -> None:
        test_client.post(
            "/api/v1/search/code",
            json={
                "repo_url": "https://github.com/pallets/flask",
                "query": "session timeout",
            },
        )
        mock_search_service.search_code.assert_called_once()
        call_kwargs = mock_search_service.search_code.call_args.kwargs
        assert call_kwargs.get("n_results", 10) == 10

    def test_query_echoed_in_response(self, test_client: TestClient) -> None:
        response = test_client.post(
            "/api/v1/search/code",
            json={"repo_url": "https://github.com/pallets/flask", "query": "session timeout"},
        )
        assert response.json()["query"] == "session timeout"
