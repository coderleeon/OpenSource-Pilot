"""Code chunker: splits source files into overlapping text chunks for indexing.

Chunks are character-based with configurable size and overlap. The chunker
respects blank lines as natural split boundaries when they fall near a chunk
boundary, producing more semantically coherent chunks.

Binary files, files exceeding the size limit, and files with unreadable
encodings are skipped gracefully.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.core.logging import get_logger
from app.tools.structure_parser import EXTENSION_LANGUAGE, _SKIP_DIRS

logger = get_logger(__name__)

# Extensions that are definitely source/text and worth indexing
_INDEXABLE_EXTENSIONS = set(EXTENSION_LANGUAGE.keys())

# Extensions to explicitly skip even if they appear in EXTENSION_LANGUAGE
_SKIP_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".xml", ".lock"}


@dataclass
class CodeChunk:
    """A fragment of a source file ready for embedding.

    Attributes:
        text: The raw text content of the chunk.
        file_path: Repository-relative path of the source file.
        language: Detected programming language or ``None``.
        chunk_index: Zero-based index of this chunk within its file.
        total_chunks: Total number of chunks for the file.
        start_char: Start character offset within the file.
        end_char: End character offset within the file.
    """

    text: str
    file_path: str
    language: str | None
    chunk_index: int
    total_chunks: int
    start_char: int
    end_char: int

    @property
    def document_id(self) -> str:
        """Unique identifier for this chunk suitable for ChromaDB."""
        # Replace path separators for a clean ID
        safe_path = self.file_path.replace("/", "__").replace("\\", "__")
        return f"{safe_path}__chunk_{self.chunk_index}"

    def to_metadata(self) -> dict:  # type: ignore[type-arg]
        """Return a flat dict of metadata for ChromaDB storage."""
        return {
            "file_path": self.file_path,
            "language": self.language or "unknown",
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "start_char": self.start_char,
            "end_char": self.end_char,
        }


class CodeChunker:
    """Splits repository source files into overlapping ``CodeChunk`` objects.

    Args:
        chunk_size: Target chunk size in characters.
        overlap: Overlap between adjacent chunks in characters.
        max_file_size_kb: Maximum file size to process. Larger files are skipped.
    """

    def __init__(
        self,
        chunk_size: int = 2000,
        overlap: int = 200,
        max_file_size_kb: int = 512,
    ) -> None:
        if overlap >= chunk_size:
            raise ValueError(f"overlap ({overlap}) must be less than chunk_size ({chunk_size})")
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._max_bytes = max_file_size_kb * 1024

    def chunk_file(self, file_path: Path, repo_root: Path) -> list[CodeChunk]:
        """Split a single file into ``CodeChunk`` objects.

        Args:
            file_path: Absolute path to the source file.
            repo_root: Absolute path to the repository root (for relative path calculation).

        Returns:
            List of chunks. Empty list if the file should be skipped.
        """
        if not self._is_indexable(file_path):
            return []

        try:
            size = file_path.stat().st_size
        except OSError:
            return []

        if size > self._max_bytes:
            logger.debug(
                "file_too_large_skipped",
                path=str(file_path),
                size_kb=size // 1024,
            )
            return []

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.debug("file_read_error", path=str(file_path), error=str(exc))
            return []

        if not content.strip():
            return []

        rel_path = str(file_path.relative_to(repo_root)).replace("\\", "/")
        language = EXTENSION_LANGUAGE.get(file_path.suffix.lower())

        return self._split_text(content, rel_path, language)

    def chunk_directory(
        self,
        repo_root: Path,
        max_files: int = 500,
    ) -> list[CodeChunk]:
        """Walk a repository and chunk all indexable source files.

        Args:
            repo_root: Absolute path to the repository root.
            max_files: Maximum number of files to process.

        Returns:
            Flat list of all ``CodeChunk`` objects across all files.
        """
        all_chunks: list[CodeChunk] = []
        files_processed = 0

        for dirpath, dirnames, filenames in os.walk(repo_root):
            # Prune unwanted directories in-place
            dirnames[:] = [
                d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")
            ]

            for filename in sorted(filenames):
                if files_processed >= max_files:
                    logger.info(
                        "indexing_limit_reached",
                        limit=max_files,
                        total_chunks=len(all_chunks),
                    )
                    return all_chunks

                file_path = Path(dirpath) / filename
                chunks = self.chunk_file(file_path, repo_root)
                if chunks:
                    all_chunks.extend(chunks)
                    files_processed += 1

        logger.info(
            "directory_chunked",
            files=files_processed,
            chunks=len(all_chunks),
            root=str(repo_root),
        )
        return all_chunks

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_indexable(self, path: Path) -> bool:
        """Return True if the file should be indexed."""
        if not path.is_file():
            return False
        suffix = path.suffix.lower()
        return suffix in _INDEXABLE_EXTENSIONS and suffix not in _SKIP_EXTENSIONS

    def _split_text(
        self,
        content: str,
        rel_path: str,
        language: str | None,
    ) -> list[CodeChunk]:
        """Split *content* into overlapping chunks with blank-line boundary snapping."""
        chunks: list[CodeChunk] = []
        content_len = len(content)
        start = 0

        while start < content_len:
            end = min(start + self._chunk_size, content_len)

            # Snap end to a nearby blank line for cleaner boundaries
            if end < content_len:
                end = self._snap_to_boundary(content, end)

            chunk_text = content[start:end].strip()
            if chunk_text:
                chunks.append(
                    CodeChunk(
                        text=chunk_text,
                        file_path=rel_path,
                        language=language,
                        chunk_index=len(chunks),
                        total_chunks=0,  # filled in after
                        start_char=start,
                        end_char=end,
                    )
                )

            if end >= content_len:
                break

            start = max(end - self._overlap, start + 1)

        # Back-fill total_chunks
        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total

        return chunks

    def _snap_to_boundary(self, content: str, pos: int, window: int = 200) -> int:
        """Try to find a blank line within *window* chars before *pos*.

        Returns the adjusted position, or the original *pos* if none found.
        """
        search_start = max(0, pos - window)
        segment = content[search_start:pos]
        # Look for a double newline (blank line)
        blank_idx = segment.rfind("\n\n")
        if blank_idx != -1:
            return search_start + blank_idx + 2  # position after the blank line
        # Fall back to last newline
        newline_idx = segment.rfind("\n")
        if newline_idx != -1:
            return search_start + newline_idx + 1
        return pos
