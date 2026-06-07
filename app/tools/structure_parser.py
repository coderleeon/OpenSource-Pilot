"""Repository directory structure parser and technology stack detector.

Walks a cloned repository directory, builds a ``FileNode`` tree, and
detects the tech stack from file patterns and dependency manifests.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.core.exceptions import StructureParseError
from app.core.logging import get_logger
from app.models.repo import FileNode, TechStack

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Extension → language mapping
# ---------------------------------------------------------------------------

EXTENSION_LANGUAGE: dict[str, str] = {
    ".py": "Python",
    ".pyw": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".cpp": "C++",
    ".cxx": "C++",
    ".cc": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".r": "R",
    ".sh": "Shell",
    ".bash": "Bash",
    ".zsh": "Zsh",
    ".fish": "Fish",
    ".ps1": "PowerShell",
    ".sql": "SQL",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".xml": "XML",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".dart": "Dart",
    ".lua": "Lua",
    ".zig": "Zig",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".clj": "Clojure",
    ".hs": "Haskell",
    ".ml": "OCaml",
    ".tf": "Terraform",
    ".proto": "Protobuf",
}

# Source code extensions (used for tech-stack language detection)
_SOURCE_EXTENSIONS = {
    ext
    for ext, lang in EXTENSION_LANGUAGE.items()
    if lang
    not in {
        "Markdown",
        "reStructuredText",
        "YAML",
        "JSON",
        "TOML",
        "XML",
        "HTML",
        "CSS",
        "SCSS",
        "Sass",
        "Less",
    }
}

# Directories to always skip when walking
_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    "target",    # Rust / Maven
    ".idea",
    ".vscode",
    ".DS_Store",
    "coverage",
    ".coverage",
    "htmlcov",
    "eggs",
    "*.egg-info",
}

# ---------------------------------------------------------------------------
# Framework / tool detection via indicator files
# ---------------------------------------------------------------------------

# Maps framework name → list of strings to look for in manifests
_FRAMEWORK_INDICATORS: dict[str, list[str]] = {
    # Python
    "Flask": ["flask"],
    "Django": ["django"],
    "FastAPI": ["fastapi"],
    "SQLAlchemy": ["sqlalchemy"],
    "Pydantic": ["pydantic"],
    "Celery": ["celery"],
    "Pytest": ["pytest"],
    # JavaScript / Node
    "React": ['"react"'],
    "Vue.js": ['"vue"'],
    "Angular": ['"@angular/core"'],
    "Next.js": ['"next"'],
    "Express": ['"express"'],
    "NestJS": ['"@nestjs/core"'],
    "Vite": ['"vite"'],
    # Rust
    "Axum": ['axum'],
    "Actix-web": ['actix-web'],
    "Tokio": ['tokio'],
    # Go
    "Gin": ["github.com/gin-gonic/gin"],
    "Echo": ["github.com/labstack/echo"],
    # Java / Kotlin
    "Spring": ["spring-boot"],
    "Quarkus": ["quarkus"],
}

_TOOL_INDICATORS: dict[str, str] = {
    "Docker": "Dockerfile",
    "Docker Compose": "docker-compose.yml",
    "GitHub Actions": ".github/workflows",
    "Makefile": "Makefile",
    "Pre-commit": ".pre-commit-config.yaml",
}

_PACKAGE_MANAGER_FILES: dict[str, str] = {
    "pip": "requirements.txt",
    "pip (pyproject)": "pyproject.toml",
    "poetry": "poetry.lock",
    "npm": "package.json",
    "yarn": "yarn.lock",
    "pnpm": "pnpm-lock.yaml",
    "cargo": "Cargo.toml",
    "go modules": "go.mod",
    "maven": "pom.xml",
    "gradle": "build.gradle",
    "bundler": "Gemfile",
    "composer": "composer.json",
}

_MANIFEST_FILES = {
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "Gemfile",
    "composer.json",
}


class StructureParser:
    """Parses a cloned repository's directory tree and detects its tech stack.

    Args:
        max_depth: Maximum directory depth to traverse (prevents runaway recursion).
        max_children: Maximum children to include per directory node.
    """

    def __init__(self, max_depth: int = 6, max_children: int = 200) -> None:
        self._max_depth = max_depth
        self._max_children = max_children

    def parse(self, root: Path) -> FileNode:
        """Build a ``FileNode`` tree for the repository rooted at *root*.

        Args:
            root: Absolute path to the cloned repository root.

        Returns:
            Root ``FileNode`` with children populated up to ``max_depth``.

        Raises:
            StructureParseError: If the root path does not exist.
        """
        if not root.exists():
            raise StructureParseError(
                f"Repository root does not exist: {root}",
            )
        try:
            return self._build_node(root, root, depth=0)
        except StructureParseError:
            raise
        except Exception as exc:
            raise StructureParseError(
                f"Failed to parse repository structure: {root}",
                details=str(exc),
            ) from exc

    def detect_tech_stack(self, root: Path) -> TechStack:
        """Detect languages, frameworks, tools, and package managers.

        Args:
            root: Absolute path to the cloned repository root.

        Returns:
            A populated ``TechStack`` instance.
        """
        languages = self._detect_languages(root)
        frameworks = self._detect_frameworks(root)
        tools = self._detect_tools(root)
        package_managers = self._detect_package_managers(root)

        logger.debug(
            "tech_stack_detected",
            languages=languages,
            frameworks=frameworks,
            tools=tools,
        )
        return TechStack(
            languages=languages,
            frameworks=frameworks,
            tools=tools,
            package_managers=package_managers,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_node(self, path: Path, root: Path, depth: int) -> FileNode:
        rel = path.relative_to(root)
        node = FileNode(
            name=path.name or root.name,
            path=str(rel).replace("\\", "/") if str(rel) != "." else "",
            is_dir=path.is_dir(),
        )

        if path.is_file():
            node.language = EXTENSION_LANGUAGE.get(path.suffix.lower())
            try:
                node.size_bytes = path.stat().st_size
            except OSError:
                node.size_bytes = None
            return node

        # Directory — recurse if within depth limit
        if depth >= self._max_depth:
            return node

        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return node

        count = 0
        for entry in entries:
            if count >= self._max_children:
                break
            # Skip hidden dirs and known noisy dirs
            if entry.is_dir() and (entry.name.startswith(".") or entry.name in _SKIP_DIRS):
                continue
            if entry.is_file() and entry.name.startswith(".") and entry.name not in {
                ".env.example",
                ".gitignore",
                ".editorconfig",
            }:
                continue
            child = self._build_node(entry, root, depth + 1)
            node.children.append(child)
            count += 1

        return node

    def _detect_languages(self, root: Path) -> list[str]:
        """Count source file extensions and return languages by frequency."""
        counts: dict[str, int] = {}
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune directories in-place
            dirnames[:] = [
                d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")
            ]
            for filename in filenames:
                ext = Path(filename).suffix.lower()
                if ext in _SOURCE_EXTENSIONS:
                    lang = EXTENSION_LANGUAGE[ext]
                    counts[lang] = counts.get(lang, 0) + 1

        # Return sorted by frequency (most common first), top 10
        return [
            lang
            for lang, _ in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        ][:10]

    def _detect_frameworks(self, root: Path) -> list[str]:
        """Detect frameworks by inspecting dependency manifest content."""
        # Gather manifest file contents
        manifest_content = ""
        for manifest in _MANIFEST_FILES:
            manifest_path = root / manifest
            if manifest_path.exists():
                try:
                    manifest_content += manifest_path.read_text(
                        encoding="utf-8", errors="replace"
                    ).lower()
                except OSError:
                    continue

        detected: list[str] = []
        for framework, indicators in _FRAMEWORK_INDICATORS.items():
            if any(ind.lower() in manifest_content for ind in indicators):
                detected.append(framework)
        return detected

    def _detect_tools(self, root: Path) -> list[str]:
        """Detect build tools / CI by checking for indicator files."""
        detected: list[str] = []
        for tool, indicator in _TOOL_INDICATORS.items():
            if (root / indicator).exists():
                detected.append(tool)
        return detected

    def _detect_package_managers(self, root: Path) -> list[str]:
        """Detect package managers by presence of lock/manifest files."""
        detected: list[str] = []
        for manager, indicator in _PACKAGE_MANAGER_FILES.items():
            if (root / indicator).exists():
                detected.append(manager)
        return detected
