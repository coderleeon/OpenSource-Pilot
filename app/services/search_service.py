"""Search Service: orchestrates repository indexing and semantic code search.

This service is the entry point for the ``POST /search-code`` endpoint.
It ensures the repository is cloned and indexed before delegating the
semantic query to ``CodeAnalysisAgent``.
"""

from __future__ import annotations

from app.agents.code_analysis_agent import CodeAnalysisAgent
from app.agents.repo_agent import RepoAgent
from app.core.logging import get_logger

logger = get_logger(__name__)


class SearchService:
    """Orchestrates repository indexing and semantic code search.

    Reuses ``RepoAgent`` (cloning) and ``CodeAnalysisAgent`` (indexing +
    querying) from Phase 1.  No new tools are required.

    Args:
        repo_agent: Handles repository cloning and metadata retrieval.
        code_analysis_agent: Handles ChromaDB indexing and semantic search.
    """

    def __init__(
        self,
        repo_agent: RepoAgent,
        code_analysis_agent: CodeAnalysisAgent,
    ) -> None:
        self._repo = repo_agent
        self._code = code_analysis_agent

    async def search_code(
        self,
        repo_url: str,
        query: str,
        n_results: int = 10,
    ) -> dict:  # type: ignore[type-arg]
        """Search the repository's code index for snippets relevant to *query*.

        The repository is cloned (if not already present) and indexed into
        ChromaDB (if not already indexed) before the search.

        Args:
            repo_url: GitHub repository URL.
            query: Free-text search query (natural language or code fragment).
            n_results: Maximum number of results to return (clamped to 1–50).

        Returns:
            Dict with ``repo_name``, ``query``, ``total_results``, and
            ``results`` list.  Each result has ``file_path``, ``language``,
            ``snippet``, and ``relevance_distance``.
        """
        # Clamp to sensible bounds
        n_results = max(1, min(n_results, 50))

        logger.info("search_code_start", url=repo_url, query=query[:80], n_results=n_results)

        # Step 1: Ensure repo is cloned and we have metadata
        repo_metadata = await self._repo.analyze(repo_url)

        # Step 2: Index if not already done (no-op if collection exists)
        await self._code.index_repo(repo_metadata)

        # Step 3: Semantic search
        results = await self._code.search(
            repo_full_name=repo_metadata.full_name,
            query=query,
            n_results=n_results,
        )

        logger.info(
            "search_code_complete",
            repo=repo_metadata.full_name,
            query=query[:80],
            results_returned=len(results),
        )

        return {
            "repo_name": repo_metadata.full_name,
            "query": query,
            "total_results": len(results),
            "results": [
                {
                    "file_path": r["file_path"],
                    "language": r.get("language", ""),
                    "snippet": r["text"][:800],
                    "relevance_distance": round(r.get("distance", 0.0), 4),
                }
                for r in results
            ],
        }
