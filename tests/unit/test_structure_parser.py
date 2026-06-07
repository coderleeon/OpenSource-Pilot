"""Unit tests for StructureParser."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.models.repo import FileNode, TechStack
from app.tools.structure_parser import StructureParser


@pytest.fixture()
def parser() -> StructureParser:
    return StructureParser(max_depth=4, max_children=50)


@pytest.fixture()
def simple_repo(tmp_path: Path) -> Path:
    """Create a minimal fake repository on disk."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_hello(): pass")
    (tmp_path / "README.md").write_text("# My Project")
    (tmp_path / "requirements.txt").write_text("flask>=2.0\npytest>=7.0\n")
    (tmp_path / "Dockerfile").write_text("FROM python:3.11")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "workflows").mkdir()
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("on: push")
    return tmp_path


class TestStructureParser:
    def test_parse_returns_root_node(self, parser: StructureParser, simple_repo: Path) -> None:
        tree = parser.parse(simple_repo)
        assert tree.is_dir is True
        assert tree.path == ""

    def test_parse_detects_children(self, parser: StructureParser, simple_repo: Path) -> None:
        tree = parser.parse(simple_repo)
        child_names = {child.name for child in tree.children}
        # src, tests, README.md, requirements.txt, Dockerfile should be present
        assert "src" in child_names
        assert "tests" in child_names
        assert "README.md" in child_names

    def test_parse_detects_language(self, parser: StructureParser, simple_repo: Path) -> None:
        tree = parser.parse(simple_repo)
        src_node = next(c for c in tree.children if c.name == "src")
        main_py = next(c for c in src_node.children if c.name == "main.py")
        assert main_py.language == "Python"
        assert main_py.is_dir is False

    def test_parse_skips_git_dir(self, parser: StructureParser, simple_repo: Path) -> None:
        (simple_repo / ".git").mkdir()
        (simple_repo / ".git" / "config").write_text("[core]")
        tree = parser.parse(simple_repo)
        child_names = {child.name for child in tree.children}
        assert ".git" not in child_names

    def test_parse_nonexistent_raises(self, parser: StructureParser, tmp_path: Path) -> None:
        from app.core.exceptions import StructureParseError

        with pytest.raises(StructureParseError):
            parser.parse(tmp_path / "does_not_exist")

    def test_to_dict_is_json_serialisable(
        self, parser: StructureParser, simple_repo: Path
    ) -> None:
        import json

        tree = parser.parse(simple_repo)
        d = tree.to_dict()
        # Should not raise
        json.dumps(d)

    def test_detect_tech_stack_languages(
        self, parser: StructureParser, simple_repo: Path
    ) -> None:
        stack: TechStack = parser.detect_tech_stack(simple_repo)
        assert "Python" in stack.languages

    def test_detect_tech_stack_frameworks(
        self, parser: StructureParser, simple_repo: Path
    ) -> None:
        stack: TechStack = parser.detect_tech_stack(simple_repo)
        # requirements.txt contains "flask" so Flask should be detected
        assert "Flask" in stack.frameworks
        assert "Pytest" in stack.frameworks

    def test_detect_tech_stack_tools(
        self, parser: StructureParser, simple_repo: Path
    ) -> None:
        stack: TechStack = parser.detect_tech_stack(simple_repo)
        assert "Docker" in stack.tools

    def test_detect_package_managers(
        self, parser: StructureParser, simple_repo: Path
    ) -> None:
        stack: TechStack = parser.detect_tech_stack(simple_repo)
        assert "pip" in stack.package_managers

    def test_max_depth_respected(self, tmp_path: Path) -> None:
        """Directories beyond max_depth should not be traversed."""
        deep = tmp_path
        for name in ["a", "b", "c", "d", "e", "f"]:
            deep = deep / name
            deep.mkdir(parents=True)
        (deep / "deep.py").write_text("x = 1")

        parser = StructureParser(max_depth=2)
        tree = parser.parse(tmp_path)

        def max_depth_of(node: FileNode, depth: int = 0) -> int:
            if not node.children:
                return depth
            return max(max_depth_of(c, depth + 1) for c in node.children)

        assert max_depth_of(tree) <= 3  # root + max_depth children

    def test_tech_stack_summary_non_empty(
        self, parser: StructureParser, simple_repo: Path
    ) -> None:
        stack = parser.detect_tech_stack(simple_repo)
        summary = stack.to_summary()
        assert "Python" in summary
