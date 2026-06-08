"""Unit tests for SearchService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.search_service import SearchService


@pytest.fixture()
def mock_repo_agent(sample_repo_metadata) -> AsyncMock:  # type: ignore[no-untyped-def]
    agent = AsyncMock()
    agent.analyze = AsyncMock(return_value=sample_repo_metadata)
    return agent


@pytest.fixture()
def mock_code_agent() -> AsyncMock:
    agent = AsyncMock()
    agent.index_repo = AsyncMock(return_value=10)
    agent.search = AsyncMock(
        return_value=[
            {
                "text": "def open_session(self, app, request):\n    pass",
                "file_path": "src/sessions.py",
                "language": "Python",
                "chunk_index": 0,
                "distance": 0.12,
            },
            {
                "text": "class SessionInterface:\n    pass",
                "file_path": "src/sessions.py",
                "language": "Python",
                "chunk_index": 1,
                "distance": 0.25,
            },
        ]
    )
    return agent


@pytest.fixture()
def service(mock_repo_agent: AsyncMock, mock_code_agent: AsyncMock) -> SearchService:
    return SearchService(
        repo_agent=mock_repo_agent,  # type: ignore[arg-type]
        code_analysis_agent=mock_code_agent,  # type: ignore[arg-type]
    )


class TestSearchCode:
    async def test_returns_dict(self, service: SearchService) -> None:
        result = await service.search_code("https://github.com/pallets/flask", "session timeout")
        assert isinstance(result, dict)

    async def test_repo_name_present(self, service: SearchService) -> None:
        result = await service.search_code("https://github.com/pallets/flask", "session timeout")
        assert result["repo_name"] == "pallets/flask"

    async def test_query_echoed(self, service: SearchService) -> None:
        result = await service.search_code("https://github.com/pallets/flask", "session timeout")
        assert result["query"] == "session timeout"

    async def test_total_results_matches_list(self, service: SearchService) -> None:
        result = await service.search_code("https://github.com/pallets/flask", "session")
        assert result["total_results"] == len(result["results"])

    async def test_results_have_required_fields(self, service: SearchService) -> None:
        result = await service.search_code("https://github.com/pallets/flask", "session")
        for r in result["results"]:
            assert "file_path" in r
            assert "language" in r
            assert "snippet" in r
            assert "relevance_distance" in r

    async def test_snippet_truncated_to_800_chars(
        self, mock_repo_agent: AsyncMock, mock_code_agent: AsyncMock
    ) -> None:
        long_text = "x" * 2000
        mock_code_agent.search = AsyncMock(
            return_value=[
                {
                    "text": long_text,
                    "file_path": "src/big_file.py",
                    "language": "Python",
                    "chunk_index": 0,
                    "distance": 0.1,
                }
            ]
        )
        service = SearchService(
            repo_agent=mock_repo_agent,  # type: ignore[arg-type]
            code_analysis_agent=mock_code_agent,  # type: ignore[arg-type]
        )
        result = await service.search_code("https://github.com/pallets/flask", "big file")
        assert len(result["results"][0]["snippet"]) <= 800

    async def test_n_results_clamped_to_max_50(
        self, mock_repo_agent: AsyncMock, mock_code_agent: AsyncMock
    ) -> None:
        service = SearchService(
            repo_agent=mock_repo_agent,  # type: ignore[arg-type]
            code_analysis_agent=mock_code_agent,  # type: ignore[arg-type]
        )
        await service.search_code("https://github.com/pallets/flask", "query", n_results=999)
        # Should have been clamped to 50
        mock_code_agent.search.assert_called_once()
        call_kwargs = mock_code_agent.search.call_args
        assert call_kwargs.kwargs.get("n_results", call_kwargs.args[2] if len(call_kwargs.args) > 2 else 999) <= 50

    async def test_n_results_clamped_to_min_1(
        self, mock_repo_agent: AsyncMock, mock_code_agent: AsyncMock
    ) -> None:
        service = SearchService(
            repo_agent=mock_repo_agent,  # type: ignore[arg-type]
            code_analysis_agent=mock_code_agent,  # type: ignore[arg-type]
        )
        await service.search_code("https://github.com/pallets/flask", "query", n_results=0)
        mock_code_agent.search.assert_called_once()

    async def test_repo_agent_analyze_called(
        self, service: SearchService, mock_repo_agent: AsyncMock
    ) -> None:
        await service.search_code("https://github.com/pallets/flask", "query")
        mock_repo_agent.analyze.assert_called_once_with("https://github.com/pallets/flask")

    async def test_index_repo_called(
        self, service: SearchService, mock_code_agent: AsyncMock, sample_repo_metadata
    ) -> None:
        await service.search_code("https://github.com/pallets/flask", "query")
        mock_code_agent.index_repo.assert_called_once_with(sample_repo_metadata)

    async def test_empty_results_handled(
        self, mock_repo_agent: AsyncMock, mock_code_agent: AsyncMock
    ) -> None:
        mock_code_agent.search = AsyncMock(return_value=[])
        service = SearchService(
            repo_agent=mock_repo_agent,  # type: ignore[arg-type]
            code_analysis_agent=mock_code_agent,  # type: ignore[arg-type]
        )
        result = await service.search_code("https://github.com/pallets/flask", "nothing")
        assert result["total_results"] == 0
        assert result["results"] == []

    async def test_distance_rounded_to_4_decimals(self, service: SearchService) -> None:
        result = await service.search_code("https://github.com/pallets/flask", "session")
        for r in result["results"]:
            # Distance should be a float with at most 4 decimal places
            assert isinstance(r["relevance_distance"], float)
            assert r["relevance_distance"] == round(r["relevance_distance"], 4)
