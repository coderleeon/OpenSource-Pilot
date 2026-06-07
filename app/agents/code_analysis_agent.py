"""Code Analysis Agent: indexes repository code and performs semantic search."""

from __future__ import annotations

import asyncio

from app.agents.base import BaseAgent
from app.models.repo import RepoMetadata
from app.tools.chroma_tool import ChromaTool
from app.tools.code_chunker import CodeChunker


class CodeAnalysisAgent(BaseAgent):
    """Indexes a repository's source code into ChromaDB and queries it semantically.

    This agent bridges the ``CodeChunker`` (file splitting) and ``ChromaTool``
    (vector storage) to provide semantic code search.  Large batch upserts are
    offloaded to a thread pool to keep the event loop responsive.

    Args:
        chroma_tool: Configured ``ChromaTool`` instance.
        code_chunker: Configured ``CodeChunker`` instance.
        max_files: Maximum number of files to index per repository.
    """

    def __init__(
        self,
        chroma_tool: ChromaTool,
        code_chunker: CodeChunker,
        max_files: int = 500,
    ) -> None:
        super().__init__()
        self._chroma = chroma_tool
        self._chunker = code_chunker
        self._max_files = max_files

    async def index_repo(self, repo_metadata: RepoMetadata) -> int:
        """Chunk and index all source files from the cloned repository.

        Skips indexing if the collection already contains documents —
        call ``force_reindex`` instead to rebuild from scratch.

        Args:
            repo_metadata: Metadata including ``local_path`` and ``full_name``.

        Returns:
            Total number of chunks indexed (0 if already indexed).

        Raises:
            IndexingError: If the upsert operation fails.
        """
        full_name = repo_metadata.full_name

        if self._chroma.collection_exists(full_name):
            self.logger.info("repo_already_indexed", repo=full_name)
            return 0

        self.logger.info("starting_indexing", repo=full_name)

        # Chunking is CPU-bound (disk I/O + string ops); offload to thread pool
        chunks = await asyncio.to_thread(
            self._chunker.chunk_directory,
            repo_metadata.local_path_obj,
            self._max_files,
        )

        if not chunks:
            self.logger.warning("no_chunks_generated", repo=full_name)
            return 0

        self.logger.info(
            "chunks_generated",
            repo=full_name,
            count=len(chunks),
        )

        # Upsert is also sync under the hood; offload for large repos
        total = await asyncio.to_thread(
            self._chroma.upsert_chunks,
            full_name,
            chunks,
        )

        self.logger.info("indexing_done", repo=full_name, total_chunks=total)
        return total

    async def force_reindex(self, repo_metadata: RepoMetadata) -> int:
        """Delete existing index and rebuild from scratch.

        Args:
            repo_metadata: Repository metadata with ``full_name`` and ``local_path``.

        Returns:
            Total number of chunks indexed after reindexing.
        """
        self.logger.info("force_reindex", repo=repo_metadata.full_name)
        await asyncio.to_thread(self._chroma.delete_collection, repo_metadata.full_name)
        return await self.index_repo(repo_metadata)

    async def search(
        self,
        repo_full_name: str,
        query: str,
        n_results: int = 10,
    ) -> list[dict]:  # type: ignore[type-arg]
        """Perform a semantic search against the repository's code index.

        Args:
            repo_full_name: Repository slug (e.g. ``"pallets/flask"``).
            query: Free-text search query (issue title, description, keywords).
            n_results: Maximum number of results to return.

        Returns:
            List of result dicts with keys: ``text``, ``file_path``,
            ``language``, ``chunk_index``, ``distance``.

        Raises:
            SearchError: If the query fails.
        """
        self.logger.debug("semantic_search", repo=repo_full_name, query=query[:80])
        results = await asyncio.to_thread(
            self._chroma.query,
            repo_full_name,
            query,
            n_results,
        )
        self.logger.debug(
            "search_results",
            repo=repo_full_name,
            count=len(results),
        )
        return results
