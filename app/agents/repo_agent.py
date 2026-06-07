"""Repository Agent: clones, parses, and builds metadata for a GitHub repository."""

from __future__ import annotations

from pathlib import Path

from app.agents.base import BaseAgent
from app.models.repo import FileNode, RepoMetadata, TechStack
from app.tools.git_tool import GitTool
from app.tools.github_api_tool import GitHubAPITool
from app.tools.structure_parser import StructureParser


class RepoAgent(BaseAgent):
    """Orchestrates repository cloning, structure parsing, and metadata assembly.

    This agent is responsible for producing a complete ``RepoMetadata`` object
    from a raw GitHub URL.  It delegates:
    - Cloning / pulling to ``GitTool``
    - GitHub metadata to ``GitHubAPITool``
    - Directory tree building to ``StructureParser``

    Args:
        git_tool: Configured ``GitTool`` instance.
        github_tool: Configured ``GitHubAPITool`` instance.
        structure_parser: Configured ``StructureParser`` instance.
    """

    def __init__(
        self,
        git_tool: GitTool,
        github_tool: GitHubAPITool,
        structure_parser: StructureParser,
    ) -> None:
        super().__init__()
        self._git = git_tool
        self._github = github_tool
        self._parser = structure_parser

    async def analyze(self, repo_url: str) -> RepoMetadata:
        """Analyse a GitHub repository and return comprehensive metadata.

        Steps:
        1. Fetch repository metadata from the GitHub API.
        2. Clone or pull the repository locally.
        3. Parse the directory structure.
        4. Detect the technology stack.
        5. Retrieve README and CONTRIBUTING guide content.

        Args:
            repo_url: GitHub repository URL (HTTPS).

        Returns:
            A fully populated ``RepoMetadata`` instance.

        Raises:
            RepoNotFoundError: If the repository does not exist.
            CloneError: If cloning fails.
            GitHubAPIError: If GitHub API calls fail.
        """
        self.logger.info("repo_agent_analyzing", url=repo_url)

        # 1. Fetch GitHub metadata (name, stars, language, license…)
        gh_repo = await self._github.get_gh_repo(repo_url)

        # 2. Clone or pull
        local_path: Path = await self._git.clone_or_pull(gh_repo.clone_url)
        self.logger.info("repo_cloned", path=str(local_path))

        # 3. Parse directory structure
        file_tree: FileNode = self._parser.parse(local_path)

        # 4. Detect tech stack
        tech_stack: TechStack = self._parser.detect_tech_stack(local_path)

        # 5. Fetch README and CONTRIBUTING guide text (best-effort)
        readme_content = self._read_local_file(local_path, "README.md") or \
                         self._read_local_file(local_path, "README.rst") or \
                         self._read_local_file(local_path, "README") or ""

        contributing_content = (
            self._read_local_file(local_path, "CONTRIBUTING.md")
            or self._read_local_file(local_path, "CONTRIBUTING.rst")
            or self._read_local_file(local_path, "CONTRIBUTING")
            or ""
        )

        # Determine license name
        license_name: str | None = None
        if gh_repo.license:
            license_name = gh_repo.license.name

        metadata = RepoMetadata(
            name=gh_repo.name,
            full_name=gh_repo.full_name,
            description=gh_repo.description,
            url=gh_repo.html_url,
            clone_url=gh_repo.clone_url,
            default_branch=gh_repo.default_branch,
            primary_language=gh_repo.language,
            topics=list(gh_repo.get_topics()),
            stars=gh_repo.stargazers_count,
            forks=gh_repo.forks_count,
            open_issues_count=gh_repo.open_issues_count,
            license_name=license_name,
            has_contributing_guide=bool(contributing_content),
            has_readme=bool(readme_content),
            local_path=str(local_path),
            file_tree=file_tree,
            tech_stack=tech_stack,
            readme_content=self._truncate(readme_content, max_chars=8000),
            contributing_content=self._truncate(contributing_content, max_chars=4000),
        )

        self.logger.info(
            "repo_agent_complete",
            repo=metadata.full_name,
            language=metadata.primary_language,
            topics=metadata.topics,
        )
        return metadata

    @staticmethod
    def _read_local_file(root: Path, filename: str) -> str | None:
        """Read a file from the repository root. Returns ``None`` if not found."""
        path = root / filename
        if path.exists() and path.is_file():
            try:
                return path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return None
        return None
