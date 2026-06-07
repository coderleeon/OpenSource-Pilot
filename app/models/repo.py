"""Domain models representing repository data.

These are pure Python dataclasses — no database ORM, no HTTP schema.
They serve as the internal contract between agents and services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FileNode:
    """A node in the repository directory tree.

    Attributes:
        name: File or directory base name.
        path: Path relative to the repository root.
        is_dir: True if this node represents a directory.
        children: Child nodes (non-empty only when ``is_dir`` is True).
        language: Detected programming language (files only).
        size_bytes: File size in bytes (files only).
    """

    name: str
    path: str
    is_dir: bool
    children: list[FileNode] = field(default_factory=list)
    language: str | None = None
    size_bytes: int | None = None

    def to_dict(self) -> dict:  # type: ignore[type-arg]
        """Recursively convert the full node tree to a plain dict (JSON-safe).

        Used internally for indexing context. For API responses use
        ``to_slim_dict`` which limits depth to avoid large payloads.
        """
        result: dict = {  # type: ignore[type-arg]
            "name": self.name,
            "path": self.path,
            "is_dir": self.is_dir,
        }
        if self.is_dir:
            result["children"] = [c.to_dict() for c in self.children]
        else:
            result["language"] = self.language
            result["size_bytes"] = self.size_bytes
        return result

    def to_slim_dict(self, max_depth: int = 2) -> dict:  # type: ignore[type-arg]
        """Return a depth-limited dict for API responses.

        Only traverses up to *max_depth* levels so the payload stays small
        and human-readable. Directories beyond the limit get an empty children
        list plus ``"truncated": true`` to indicate hidden content.

        Args:
            max_depth: Maximum levels to expand (0 = root only, no children).
        """
        return self._slim(depth=0, max_depth=max_depth)

    def _slim(self, depth: int, max_depth: int) -> dict:  # type: ignore[type-arg]
        result: dict = {  # type: ignore[type-arg]
            "name": self.name,
            "path": self.path,
            "is_dir": self.is_dir,
        }
        if self.is_dir:
            if depth < max_depth:
                result["children"] = [c._slim(depth + 1, max_depth) for c in self.children]
            else:
                result["children"] = []
                if self.children:
                    result["truncated"] = True  # signals hidden content
        else:
            result["language"] = self.language
            result["size_bytes"] = self.size_bytes
        return result

    def count_files(self) -> int:
        """Return the total number of file nodes in this subtree."""
        if not self.is_dir:
            return 1
        return sum(child.count_files() for child in self.children)

    def count_dirs(self) -> int:
        """Return the total number of directory nodes in this subtree (excluding self)."""
        if not self.is_dir:
            return 0
        return sum(1 + child.count_dirs() for child in self.children if child.is_dir)

    def get_key_directories(self) -> list[str]:
        """Return paths of immediate child *directories* (top-level only).

        These represent the primary structural sections of the project
        (e.g. ``src``, ``tests``, ``docs``) and are useful for LLM prompts
        and API consumers without exposing the entire tree.
        """
        return [child.path for child in self.children if child.is_dir]


@dataclass
class TechStack:
    """Detected technology stack for a repository.

    Attributes:
        languages: Programming languages detected (e.g. ``["Python", "JavaScript"]``).
        frameworks: Frameworks / libraries detected (e.g. ``["FastAPI", "React"]``).
        tools: Build tools / configuration systems (e.g. ``["Docker", "pytest"]``).
        package_managers: Package managers found (e.g. ``["pip", "npm"]``).
    """

    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)

    def to_summary(self) -> str:
        """Return a concise one-line summary for use in LLM prompts."""
        parts: list[str] = []
        if self.languages:
            parts.append(f"Languages: {', '.join(self.languages)}")
        if self.frameworks:
            parts.append(f"Frameworks: {', '.join(self.frameworks)}")
        if self.tools:
            parts.append(f"Tools: {', '.join(self.tools)}")
        return " | ".join(parts) if parts else "Unknown"


@dataclass
class RepoMetadata:
    """Complete metadata for an analysed repository.

    Attributes:
        name: Short repository name (e.g. ``"flask"``).
        full_name: Owner/repo slug (e.g. ``"pallets/flask"``).
        description: Repository description from GitHub.
        url: HTML URL of the repository.
        clone_url: Git clone URL.
        default_branch: Default branch name (e.g. ``"main"``).
        primary_language: Most-used language according to GitHub.
        topics: GitHub topic tags.
        stars: Star count.
        forks: Fork count.
        open_issues_count: Number of open issues.
        license_name: SPDX license name or ``None``.
        has_contributing_guide: True if a CONTRIBUTING file exists.
        has_readme: True if a README file exists.
        local_path: Absolute path to the cloned repository on disk.
        file_tree: Root ``FileNode`` of the directory tree.
        tech_stack: Detected technology stack.
        readme_content: Raw text of the README (may be truncated).
        contributing_content: Raw text of the CONTRIBUTING guide.
    """

    name: str
    full_name: str
    description: str | None
    url: str
    clone_url: str
    default_branch: str
    primary_language: str | None
    topics: list[str]
    stars: int
    forks: int
    open_issues_count: int
    license_name: str | None
    has_contributing_guide: bool
    has_readme: bool
    local_path: str
    file_tree: FileNode
    tech_stack: TechStack
    readme_content: str = ""
    contributing_content: str = ""

    @property
    def local_path_obj(self) -> Path:
        """Return ``local_path`` as a ``pathlib.Path``."""
        return Path(self.local_path)
