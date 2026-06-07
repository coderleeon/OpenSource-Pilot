"""GitPython wrapper for repository clone and update operations.

All blocking GitPython calls are offloaded to a thread pool via
``asyncio.to_thread`` so they never block the event loop.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

import git

from app.core.exceptions import CloneError, RepoNotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Sanitise repo URL into a safe directory name: strip protocol, replace slashes/dots.
_SLUG_RE = re.compile(r"[^\w-]")


def _url_to_dirname(repo_url: str) -> str:
    """Convert a repo URL to a filesystem-safe directory name.

    Examples:
        ``https://github.com/pallets/flask`` → ``github.com_pallets_flask``
    """
    url = repo_url.rstrip("/")
    # Remove scheme (https://, git://, etc.)
    url = re.sub(r"^[a-zA-Z][a-zA-Z0-9+\-.]*://", "", url)
    # Replace non-word characters with underscores
    return _SLUG_RE.sub("_", url)


class GitTool:
    """Async wrapper around GitPython for cloning and updating repositories.

    Args:
        clone_base_dir: Base directory under which repositories are cloned.
            Each repo gets its own sub-directory named from the sanitised URL.
    """

    def __init__(self, clone_base_dir: str) -> None:
        self._base = Path(clone_base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def _repo_dir(self, repo_url: str) -> Path:
        """Return the local directory path for *repo_url*."""
        return self._base / _url_to_dirname(repo_url)

    async def clone_or_pull(self, repo_url: str) -> Path:
        """Clone a repository or pull the latest commits if already cloned.

        Args:
            repo_url: HTTPS or SSH URL of the repository to clone.

        Returns:
            Absolute ``Path`` to the cloned repository on disk.

        Raises:
            RepoNotFoundError: If the repository does not exist or is inaccessible.
            CloneError: If the clone / pull operation fails for another reason.
        """
        repo_dir = self._repo_dir(repo_url)

        if repo_dir.exists() and (repo_dir / ".git").exists():
            logger.info("pulling_existing_repo", path=str(repo_dir), url=repo_url)
            return await asyncio.to_thread(self._pull, repo_dir, repo_url)
        else:
            logger.info("cloning_repo", path=str(repo_dir), url=repo_url)
            return await asyncio.to_thread(self._clone, repo_url, repo_dir)

    def _clone(self, repo_url: str, repo_dir: Path) -> Path:
        """Synchronous clone operation (runs in thread pool)."""
        try:
            repo_dir.mkdir(parents=True, exist_ok=True)
            git.Repo.clone_from(
                repo_url,
                str(repo_dir),
                depth=1,  # shallow clone — faster, sufficient for analysis
                no_single_branch=True,
            )
            logger.info("clone_complete", path=str(repo_dir))
            return repo_dir
        except git.exc.GitCommandError as exc:
            error_msg = str(exc).lower()
            if "not found" in error_msg or "repository" in error_msg and "exist" in error_msg:
                raise RepoNotFoundError(
                    f"Repository not found: {repo_url}",
                    details=str(exc),
                ) from exc
            raise CloneError(
                f"Failed to clone repository: {repo_url}",
                details=str(exc),
            ) from exc
        except Exception as exc:
            raise CloneError(
                f"Unexpected error cloning {repo_url}",
                details=str(exc),
            ) from exc

    def _pull(self, repo_dir: Path, repo_url: str) -> Path:
        """Synchronous pull operation (runs in thread pool)."""
        try:
            repo = git.Repo(str(repo_dir))
            origin = repo.remotes.origin
            origin.pull(depth=1)
            logger.info("pull_complete", path=str(repo_dir))
            return repo_dir
        except git.exc.GitCommandError as exc:
            logger.warning(
                "pull_failed_using_cached",
                path=str(repo_dir),
                error=str(exc),
            )
            # Fall back to cached version rather than failing the entire request.
            return repo_dir
        except Exception as exc:
            logger.warning(
                "pull_unexpected_error_using_cached",
                path=str(repo_dir),
                error=str(exc),
            )
            return repo_dir

    def get_local_path(self, repo_url: str) -> Path | None:
        """Return the local path if the repo is already cloned, else ``None``."""
        repo_dir = self._repo_dir(repo_url)
        if repo_dir.exists() and (repo_dir / ".git").exists():
            return repo_dir
        return None
