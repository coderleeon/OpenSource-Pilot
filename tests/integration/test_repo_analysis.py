"""Integration tests for the repository analysis workflow.

These tests wire together the real service graph (using mocked external
dependencies — GitHub API, LLM, and ChromaDB) to verify the full orchestration
works end-to-end without touching the network or filesystem in unexpected ways.

Run with:
    pytest tests/integration/ -v -m integration
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.code_analysis_agent import CodeAnalysisAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.repo_agent import RepoAgent
from app.services.repo_service import RepoService
from app.tools.code_chunker import CodeChunker
from app.tools.structure_parser import StructureParser


pytestmark = pytest.mark.integration


@pytest.fixture()
def fake_repo_on_disk(tmp_path: Path) -> Path:
    """Create a minimal fake repository directory tree."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(
        "from flask import Flask\napp = Flask(__name__)\n"
    )
    (tmp_path / "src" / "sessions.py").write_text(
        "class SecureCookieSession:\n    def open_session(self, app, request):\n        pass\n"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("def test_create_app(): pass\n")
    (tmp_path / "README.md").write_text(
        "# Flask\nThe Python micro framework for building web applications."
    )
    (tmp_path / "CONTRIBUTING.md").write_text(
        "# Contributing\nPlease open an issue before submitting a PR."
    )
    (tmp_path / "requirements.txt").write_text("flask>=2.0\npytest>=7.0\n")
    return tmp_path


@pytest.fixture()
def mock_git_tool(fake_repo_on_disk: Path) -> AsyncMock:
    git = AsyncMock()
    git.clone_or_pull = AsyncMock(return_value=fake_repo_on_disk)
    return git


@pytest.fixture()
def repo_service(
    mock_git_tool: AsyncMock,
    mock_github_tool: AsyncMock,
    mock_llm_client: AsyncMock,
    mock_chroma_tool: MagicMock,
) -> RepoService:
    """Build a RepoService with all externals mocked."""
    parser = StructureParser()
    chunker = CodeChunker(chunk_size=500, overlap=50, max_file_size_kb=100)

    repo_agent = RepoAgent(
        git_tool=mock_git_tool,
        github_tool=mock_github_tool,
        structure_parser=parser,
    )
    code_agent = CodeAnalysisAgent(
        chroma_tool=mock_chroma_tool,
        code_chunker=chunker,
        max_files=50,
    )
    planning_agent = PlanningAgent(llm_client=mock_llm_client)

    return RepoService(
        repo_agent=repo_agent,
        code_analysis_agent=code_agent,
        planning_agent=planning_agent,
    )


class TestRepoAnalysisIntegration:
    async def test_analyze_returns_expected_keys(
        self, repo_service: RepoService
    ) -> None:
        result = await repo_service.analyze(
            repo_url="https://github.com/pallets/flask",
            index_code=True,
        )
        assert "analysis_id" in result
        assert "full_name" in result
        assert "directory_structure" in result
        assert "tech_stack" in result
        assert "readme_summary" in result
        assert "total_files_indexed" in result
        # New fields
        assert "total_files_count" in result
        assert "total_directories_count" in result
        assert "key_directories" in result
        assert "architecture_summary" in result

    async def test_analyze_full_name_correct(
        self, repo_service: RepoService
    ) -> None:
        result = await repo_service.analyze(
            repo_url="https://github.com/pallets/flask",
        )
        assert result["full_name"] == "pallets/flask"

    async def test_analyze_tech_stack_detects_python(
        self, repo_service: RepoService
    ) -> None:
        result = await repo_service.analyze(
            repo_url="https://github.com/pallets/flask",
        )
        assert "Python" in result["tech_stack"]["languages"]

    async def test_analyze_skips_indexing_when_flag_false(
        self,
        repo_service: RepoService,
        mock_chroma_tool: MagicMock,
    ) -> None:
        await repo_service.analyze(
            repo_url="https://github.com/pallets/flask",
            index_code=False,
        )
        # upsert_chunks should never be called
        mock_chroma_tool.upsert_chunks.assert_not_called()

    async def test_analyze_skips_reindex_when_already_indexed(
        self,
        mock_git_tool: AsyncMock,
        mock_github_tool: AsyncMock,
        mock_llm_client: AsyncMock,
        mock_chroma_tool: MagicMock,
        fake_repo_on_disk: Path,
    ) -> None:
        """If collection already exists, upsert should not be called again."""
        mock_chroma_tool.collection_exists.return_value = True

        parser = StructureParser()
        chunker = CodeChunker(chunk_size=500, overlap=50, max_file_size_kb=100)
        repo_agent = RepoAgent(mock_git_tool, mock_github_tool, parser)
        code_agent = CodeAnalysisAgent(mock_chroma_tool, chunker)
        planning_agent = PlanningAgent(mock_llm_client)
        service = RepoService(repo_agent, code_agent, planning_agent)

        await service.analyze("https://github.com/pallets/flask", index_code=True)
        mock_chroma_tool.upsert_chunks.assert_not_called()

    async def test_analysis_id_is_uuid(
        self, repo_service: RepoService
    ) -> None:
        import uuid

        result = await repo_service.analyze("https://github.com/pallets/flask")
        # Should not raise
        uuid.UUID(result["analysis_id"])

    async def test_directory_structure_limited_to_2_levels(
        self, repo_service: RepoService
    ) -> None:
        """directory_structure must be depth-2 slim tree, not full recursive tree."""
        result = await repo_service.analyze("https://github.com/pallets/flask")
        tree = result["directory_structure"]
        assert tree.get("is_dir") is True
        assert isinstance(tree.get("children"), list)
        assert len(tree["children"]) > 0

        # Verify depth: level-2 children of directories should have no further children
        for child in tree["children"]:
            if child.get("is_dir") and child.get("children"):
                for grandchild in child["children"]:
                    if grandchild.get("is_dir"):
                        # At depth-2 limit: should have empty children list
                        assert grandchild.get("children") == [] or grandchild.get("children") is None

    async def test_total_files_count_is_positive(
        self, repo_service: RepoService
    ) -> None:
        result = await repo_service.analyze("https://github.com/pallets/flask")
        assert result["total_files_count"] > 0

    async def test_total_directories_count(
        self, repo_service: RepoService
    ) -> None:
        result = await repo_service.analyze("https://github.com/pallets/flask")
        # fake_repo_on_disk has src/ and tests/ directories
        assert result["total_directories_count"] >= 2

    async def test_key_directories_are_strings(
        self, repo_service: RepoService
    ) -> None:
        result = await repo_service.analyze("https://github.com/pallets/flask")
        assert isinstance(result["key_directories"], list)
        assert all(isinstance(d, str) for d in result["key_directories"])

    async def test_key_directories_contains_src(
        self, repo_service: RepoService
    ) -> None:
        """fake_repo_on_disk has src/ and tests/ as top-level dirs."""
        result = await repo_service.analyze("https://github.com/pallets/flask")
        assert "src" in result["key_directories"]

    async def test_architecture_summary_is_non_empty_string(
        self, repo_service: RepoService
    ) -> None:
        result = await repo_service.analyze("https://github.com/pallets/flask")
        assert isinstance(result["architecture_summary"], str)
        assert len(result["architecture_summary"]) > 0
