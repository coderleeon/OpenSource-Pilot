"""ChromaDB wrapper for vector storage and semantic code search.

Uses ``sentence-transformers/all-MiniLM-L6-v2`` for local embeddings —
no external API calls or cost. The model (~80 MB) is downloaded automatically
on first use and cached by the sentence-transformers library.

Collection names are derived from the repository full name (e.g.
``"pallets_flask"``) and must satisfy ChromaDB naming rules:
3–63 chars, start/end alphanumeric, contain only alphanumeric/dash/underscore/dot.
"""

from __future__ import annotations

import re

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.core.exceptions import IndexingError, SearchError
from app.core.logging import get_logger
from app.tools.code_chunker import CodeChunk

logger = get_logger(__name__)

# ChromaDB collection name constraints
_INVALID_CHARS_RE = re.compile(r"[^a-zA-Z0-9._-]")
_LEADING_TRAILING_RE = re.compile(r"^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$")
_MIN_LEN = 3
_MAX_LEN = 63


def _sanitise_collection_name(raw: str) -> str:
    """Convert a raw string (e.g. repo full_name) to a valid ChromaDB collection name.

    Examples:
        ``"pallets/flask"`` → ``"pallets_flask"``
        ``"org/my-repo.git"`` → ``"org_my-repo.git"``
    """
    name = raw.strip()
    name = _INVALID_CHARS_RE.sub("_", name)
    name = _LEADING_TRAILING_RE.sub("", name)

    # Truncate to max length
    if len(name) > _MAX_LEN:
        name = name[:_MAX_LEN]
        # Ensure we don't end on a non-alphanumeric after truncation
        name = _LEADING_TRAILING_RE.sub("", name)

    # Pad if too short (shouldn't happen with real repo names)
    if len(name) < _MIN_LEN:
        name = name.ljust(_MIN_LEN, "0")

    return name


class ChromaTool:
    """Async-compatible ChromaDB client for code indexing and semantic search.

    Wraps ChromaDB's synchronous API. Since ChromaDB operations are typically
    fast (local SQLite + HNSW index), they are called directly.
    For large batch upserts, the caller should use ``asyncio.to_thread``.

    Args:
        persist_dir: Directory path where ChromaDB persists its data.
        embedding_model: Sentence-transformers model name for local embeddings.
    """

    def __init__(
        self,
        persist_dir: str = "./chroma_db",
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        self._persist_dir = persist_dir
        self._embedding_model = embedding_model

        logger.info(
            "chromadb_initialising",
            persist_dir=persist_dir,
            embedding_model=embedding_model,
        )

        self._client = chromadb.PersistentClient(path=persist_dir)

        # Initialise embedding function once — this may trigger model download
        logger.info(
            "loading_embedding_model",
            model=embedding_model,
            note="Model download (~80 MB) occurs on first use",
        )
        self._embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=embedding_model,
            device="cpu",
        )

        logger.info("chromadb_ready", persist_dir=persist_dir)

    def get_or_create_collection(self, repo_full_name: str) -> chromadb.Collection:
        """Return an existing collection or create a new one for *repo_full_name*.

        Args:
            repo_full_name: Repository slug (e.g. ``"pallets/flask"``).

        Returns:
            ChromaDB Collection with the local embedding function attached.
        """
        collection_name = _sanitise_collection_name(repo_full_name)
        try:
            collection = self._client.get_or_create_collection(
                name=collection_name,
                embedding_function=self._embedding_fn,
                metadata={"repo": repo_full_name, "hnsw:space": "cosine"},
            )
            logger.debug(
                "collection_ready",
                name=collection_name,
                count=collection.count(),
            )
            return collection
        except Exception as exc:
            raise IndexingError(
                f"Failed to get/create ChromaDB collection for {repo_full_name!r}",
                details=str(exc),
            ) from exc

    def upsert_chunks(self, repo_full_name: str, chunks: list[CodeChunk]) -> int:
        """Upsert a list of ``CodeChunk`` objects into the repository's collection.

        Chunks are batched into groups of 500 to avoid ChromaDB batch limits.

        Args:
            repo_full_name: Repository slug used to identify the collection.
            chunks: List of ``CodeChunk`` objects to index.

        Returns:
            Total number of chunks upserted.

        Raises:
            IndexingError: If the upsert operation fails.
        """
        if not chunks:
            return 0

        collection = self.get_or_create_collection(repo_full_name)
        batch_size = 500
        total_upserted = 0

        for batch_start in range(0, len(chunks), batch_size):
            batch = chunks[batch_start : batch_start + batch_size]
            try:
                collection.upsert(
                    ids=[chunk.document_id for chunk in batch],
                    documents=[chunk.text for chunk in batch],
                    metadatas=[chunk.to_metadata() for chunk in batch],
                )
                total_upserted += len(batch)
                logger.debug(
                    "batch_upserted",
                    repo=repo_full_name,
                    batch_start=batch_start,
                    batch_size=len(batch),
                )
            except Exception as exc:
                raise IndexingError(
                    f"Failed to upsert chunk batch at offset {batch_start}",
                    details=str(exc),
                ) from exc

        logger.info(
            "indexing_complete",
            repo=repo_full_name,
            total_chunks=total_upserted,
        )
        return total_upserted

    def query(
        self,
        repo_full_name: str,
        query_text: str,
        n_results: int = 10,
    ) -> list[dict]:  # type: ignore[type-arg]
        """Perform a semantic similarity search against the repository index.

        Args:
            repo_full_name: Repository slug identifying the collection to search.
            query_text: The search query (issue title, description, keywords).
            n_results: Maximum number of results to return.

        Returns:
            List of dicts, each with keys: ``text``, ``file_path``, ``language``,
            ``chunk_index``, ``distance``.

        Raises:
            SearchError: If the query fails.
        """
        collection = self.get_or_create_collection(repo_full_name)

        actual_count = collection.count()
        if actual_count == 0:
            logger.warning("collection_empty", repo=repo_full_name)
            return []

        # Clamp n_results to available documents
        n_results = min(n_results, actual_count)

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise SearchError(
                f"Semantic search failed for repo {repo_full_name!r}",
                details=str(exc),
            ) from exc

        output: list[dict] = []  # type: ignore[type-arg]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            output.append(
                {
                    "text": doc,
                    "file_path": meta.get("file_path", ""),
                    "language": meta.get("language", "unknown"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "distance": round(float(dist), 4),
                }
            )

        return output

    def collection_exists(self, repo_full_name: str) -> bool:
        """Return True if a collection for *repo_full_name* has been indexed."""
        collection_name = _sanitise_collection_name(repo_full_name)
        try:
            col = self._client.get_collection(
                name=collection_name,
                embedding_function=self._embedding_fn,
            )
            return col.count() > 0
        except Exception:
            return False

    def delete_collection(self, repo_full_name: str) -> None:
        """Delete the collection for *repo_full_name* (useful for re-indexing)."""
        collection_name = _sanitise_collection_name(repo_full_name)
        try:
            self._client.delete_collection(name=collection_name)
            logger.info("collection_deleted", repo=repo_full_name, name=collection_name)
        except Exception as exc:
            logger.warning("collection_delete_failed", repo=repo_full_name, error=str(exc))
