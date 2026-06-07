"""Unit tests for CodeChunker."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.tools.code_chunker import CodeChunk, CodeChunker


@pytest.fixture()
def chunker() -> CodeChunker:
    return CodeChunker(chunk_size=200, overlap=20, max_file_size_kb=1)


@pytest.fixture()
def small_py_file(tmp_path: Path) -> Path:
    code = "\n".join(
        [f"def function_{i}():" + "\n    pass\n" for i in range(20)]
    )
    f = tmp_path / "sample.py"
    f.write_text(code, encoding="utf-8")
    return f


@pytest.fixture()
def large_file(tmp_path: Path) -> Path:
    """File larger than max_file_size_kb (1 KB)."""
    f = tmp_path / "large.py"
    f.write_bytes(b"x = 1\n" * 200)  # ~1.2 KB
    return f


@pytest.fixture()
def binary_file(tmp_path: Path) -> Path:
    f = tmp_path / "image.png"
    f.write_bytes(bytes(range(256)))
    return f


@pytest.fixture()
def json_file(tmp_path: Path) -> Path:
    f = tmp_path / "data.json"
    f.write_text('{"key": "value"}')
    return f


class TestCodeChunker:
    def test_chunk_file_produces_chunks(
        self, chunker: CodeChunker, small_py_file: Path, tmp_path: Path
    ) -> None:
        chunks = chunker.chunk_file(small_py_file, tmp_path)
        assert len(chunks) > 0
        assert all(isinstance(c, CodeChunk) for c in chunks)

    def test_chunk_language_detected(
        self, chunker: CodeChunker, small_py_file: Path, tmp_path: Path
    ) -> None:
        chunks = chunker.chunk_file(small_py_file, tmp_path)
        assert chunks[0].language == "Python"

    def test_chunk_file_path_is_relative(
        self, chunker: CodeChunker, small_py_file: Path, tmp_path: Path
    ) -> None:
        chunks = chunker.chunk_file(small_py_file, tmp_path)
        assert chunks[0].file_path == "sample.py"

    def test_chunk_indices_sequential(
        self, chunker: CodeChunker, small_py_file: Path, tmp_path: Path
    ) -> None:
        chunks = chunker.chunk_file(small_py_file, tmp_path)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_total_chunks_backfilled(
        self, chunker: CodeChunker, small_py_file: Path, tmp_path: Path
    ) -> None:
        chunks = chunker.chunk_file(small_py_file, tmp_path)
        expected_total = len(chunks)
        assert all(c.total_chunks == expected_total for c in chunks)

    def test_document_id_unique(
        self, chunker: CodeChunker, small_py_file: Path, tmp_path: Path
    ) -> None:
        chunks = chunker.chunk_file(small_py_file, tmp_path)
        ids = [c.document_id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_large_file_skipped(
        self, chunker: CodeChunker, large_file: Path, tmp_path: Path
    ) -> None:
        chunks = chunker.chunk_file(large_file, tmp_path)
        assert chunks == []

    def test_binary_file_skipped(
        self, chunker: CodeChunker, binary_file: Path, tmp_path: Path
    ) -> None:
        chunks = chunker.chunk_file(binary_file, tmp_path)
        assert chunks == []

    def test_json_file_skipped(
        self, chunker: CodeChunker, json_file: Path, tmp_path: Path
    ) -> None:
        """JSON is in the skip-extensions list."""
        chunks = chunker.chunk_file(json_file, tmp_path)
        assert chunks == []

    def test_chunk_directory(self, tmp_path: Path) -> None:
        """chunk_directory should aggregate chunks from multiple files."""
        (tmp_path / "a.py").write_text("x = 1\n" * 30)
        (tmp_path / "b.py").write_text("y = 2\n" * 30)
        chunker = CodeChunker(chunk_size=100, overlap=10, max_file_size_kb=10)
        chunks = chunker.chunk_directory(tmp_path, max_files=10)
        file_paths = {c.file_path for c in chunks}
        assert "a.py" in file_paths
        assert "b.py" in file_paths

    def test_chunk_directory_respects_max_files(self, tmp_path: Path) -> None:
        for i in range(5):
            (tmp_path / f"file_{i}.py").write_text("x = 1\n" * 10)
        chunker = CodeChunker(chunk_size=50, overlap=5, max_file_size_kb=10)
        chunks = chunker.chunk_directory(tmp_path, max_files=2)
        file_paths = {c.file_path for c in chunks}
        assert len(file_paths) <= 2

    def test_overlap_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="overlap"):
            CodeChunker(chunk_size=100, overlap=100)

    def test_to_metadata_flat_dict(
        self, chunker: CodeChunker, small_py_file: Path, tmp_path: Path
    ) -> None:
        chunks = chunker.chunk_file(small_py_file, tmp_path)
        meta = chunks[0].to_metadata()
        assert isinstance(meta, dict)
        assert "file_path" in meta
        assert "language" in meta
        assert "chunk_index" in meta
