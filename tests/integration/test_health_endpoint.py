"""Integration tests for the health check endpoint."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def test_client(test_settings) -> TestClient:
    """TestClient that patches ``get_settings`` so the lifespan runs without real API keys."""
    from app.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()  # clear the lru_cache so our mock takes effect

    with patch("app.main.get_settings", return_value=test_settings):
        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    get_settings.cache_clear()


class TestHealthEndpoint:
    def test_health_healthy_returns_200(self, test_client: TestClient) -> None:
        """Health endpoint returns 200 and status healthy when configured correctly."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_health_missing_api_key_returns_503(self, test_settings) -> None:
        """Health endpoint returns 503 if LLM provider key is missing."""
        from app.config import get_settings
        from app.main import create_app

        test_settings.openrouter_api_key = ""  # clear api key
        get_settings.cache_clear()

        with patch("app.main.get_settings", return_value=test_settings):
            with patch("app.main.create_llm_client_from_settings", return_value=None):
                app = create_app()
                with TestClient(app, raise_server_exceptions=False) as c:
                    response = c.get("/health")
                    assert response.status_code == 503
                    assert "API key is missing" in response.json()["detail"]

        get_settings.cache_clear()

    def test_health_chroma_not_writeable_returns_503(self, test_client: TestClient) -> None:
        """Health endpoint returns 503 if ChromaDB directory cannot be written to."""
        # Mock open inside main to raise OSError on chroma check
        original_open = open

        def mock_open(file, *args, **kwargs):
            if ".health_check" in str(file) and "chroma" in str(file):
                raise PermissionError("Permission denied")
            return original_open(file, *args, **kwargs)

        with patch("builtins.open", side_effect=mock_open):
            response = test_client.get("/health")
            assert response.status_code == 503
            assert "ChromaDB directory is not writeable" in response.json()["detail"]

    def test_health_cloned_repos_not_writeable_returns_503(self, test_client: TestClient) -> None:
        """Health endpoint returns 503 if cloned repos directory cannot be written to."""
        original_open = open

        def mock_open(file, *args, **kwargs):
            if ".health_check" in str(file) and "clones" in str(file):
                raise PermissionError("Permission denied")
            return original_open(file, *args, **kwargs)

        with patch("builtins.open", side_effect=mock_open):
            response = test_client.get("/health")
            assert response.status_code == 503
            assert "Cloned repos directory is not writeable" in response.json()["detail"]
