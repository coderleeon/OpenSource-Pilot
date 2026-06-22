"""PyGithub wrapper providing structured access to GitHub API data.

All PyGithub calls are synchronous; they are offloaded to a thread pool
via ``asyncio.to_thread`` to keep the event loop non-blocking.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone

from github import Auth, Github, GithubException, UnknownObjectException
from github.Repository import Repository as GHRepository

from app.core.exceptions import GitHubAPIError, IssueNotFoundError, RepoNotFoundError
from app.core.logging import get_logger
from app.models.issue import GitHubIssue

logger = get_logger(__name__)

# Match https://github.com/owner/repo or github.com/owner/repo
_GITHUB_URL_RE = re.compile(
    r"(?:https?://)?github\.com/([^/]+)/([^/\s]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


def _parse_repo_slug(repo_url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL.

    Raises:
        GitHubAPIError: If the URL does not match the expected pattern.
    """
    m = _GITHUB_URL_RE.match(repo_url.strip())
    if not m:
        raise GitHubAPIError(
            f"Invalid GitHub URL: {repo_url!r}",
            details="Expected format: https://github.com/owner/repo",
        )
    return m.group(1), m.group(2)


def _utc(dt: datetime) -> datetime:
    """Ensure a datetime is UTC-aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class GitHubAPITool:
    """Structured async access to the GitHub REST API via PyGithub.

    Args:
        github_token: Personal access token. If empty, unauthenticated
            access is used (60 req/hr limit).
    """

    def __init__(self, github_token: str = "") -> None:
        if github_token:
            auth = Auth.Token(github_token)
            self._gh = Github(auth=auth)
        else:
            self._gh = Github()
        logger.info(
            "github_tool_initialised",
            authenticated=bool(github_token),
        )

    # ------------------------------------------------------------------
    # Public async interface
    # ------------------------------------------------------------------

    async def get_gh_repo(self, repo_url: str) -> GHRepository:
        """Return the PyGithub Repository object for *repo_url*.

        Raises:
            RepoNotFoundError: Repository does not exist or is private.
            GitHubAPIError: Any other GitHub API failure.
        """
        owner, repo = _parse_repo_slug(repo_url)
        return await asyncio.to_thread(self._get_repo_sync, owner, repo, repo_url)

    async def get_issues(
        self,
        repo_url: str,
        state: str = "open",
        labels: list[str] | None = None,
        limit: int = 50,
    ) -> list[GitHubIssue]:
        """Retrieve open issues from the repository.

        Args:
            repo_url: GitHub repository URL.
            state: ``"open"``, ``"closed"``, or ``"all"``.
            labels: Optional list of label names to filter by.
            limit: Maximum number of issues to return.

        Returns:
            List of ``GitHubIssue`` dataclass instances.

        Raises:
            RepoNotFoundError: Repository does not exist.
            GitHubAPIError: API call failed.
        """
        gh_repo = await self.get_gh_repo(repo_url)
        return await asyncio.to_thread(
            self._get_issues_sync, gh_repo, state, labels or [], limit
        )

    async def get_issue(self, repo_url: str, issue_number: int) -> GitHubIssue:
        """Retrieve a single issue by number.

        Raises:
            IssueNotFoundError: The issue number does not exist.
            RepoNotFoundError: Repository does not exist.
            GitHubAPIError: API call failed.
        """
        gh_repo = await self.get_gh_repo(repo_url)
        return await asyncio.to_thread(self._get_issue_sync, gh_repo, issue_number)

    async def get_file_content(self, repo_url: str, file_path: str) -> str | None:
        """Retrieve decoded text content of a file from the default branch.

        Returns ``None`` if the file does not exist or is binary/too large.
        """
        gh_repo = await self.get_gh_repo(repo_url)
        return await asyncio.to_thread(self._get_file_sync, gh_repo, file_path)

    async def search_issues(
        self,
        query: str,
        limit: int = 30,
    ) -> list[dict]:
        """Search issues globally on GitHub.

        Returns:
            List of dictionaries containing the GitHubIssue and repository metadata.
        """
        return await asyncio.to_thread(self._search_issues_sync, query, limit)

    # ------------------------------------------------------------------
    # Synchronous helpers (run in thread pool)
    # ------------------------------------------------------------------

    def _get_repo_sync(self, owner: str, repo: str, repo_url: str) -> GHRepository:
        try:
            return self._gh.get_repo(f"{owner}/{repo}")
        except UnknownObjectException as exc:
            raise RepoNotFoundError(
                f"Repository not found: {repo_url}",
                details=str(exc),
            ) from exc
        except GithubException as exc:
            raise GitHubAPIError(
                f"GitHub API error accessing {repo_url}",
                details=str(exc),
            ) from exc

    def _get_issues_sync(
        self,
        gh_repo: GHRepository,
        state: str,
        labels: list[str],
        limit: int,
    ) -> list[GitHubIssue]:
        try:
            kwargs: dict = {"state": state}
            if labels:
                kwargs["labels"] = labels

            issues = gh_repo.get_issues(**kwargs)
            result: list[GitHubIssue] = []
            for issue in issues[:limit]:
                # PyGithub returns PRs in issue list; filter them out
                if issue.pull_request:
                    continue
                result.append(self._map_issue(issue))
            return result
        except GithubException as exc:
            raise GitHubAPIError(
                "Failed to retrieve issues",
                details=str(exc),
            ) from exc

    def _get_issue_sync(self, gh_repo: GHRepository, number: int) -> GitHubIssue:
        try:
            issue = gh_repo.get_issue(number)
            return self._map_issue(issue)
        except UnknownObjectException as exc:
            raise IssueNotFoundError(
                f"Issue #{number} was not found in this repository.",
                details=str(exc),
            ) from exc
        except GithubException as exc:
            raise GitHubAPIError(
                f"Failed to retrieve issue #{number}",
                details=str(exc),
            ) from exc

    def _get_file_sync(self, gh_repo: GHRepository, file_path: str) -> str | None:
        try:
            content_file = gh_repo.get_contents(file_path)
            if isinstance(content_file, list):
                return None  # It's a directory
            if content_file.encoding != "base64":
                return None
            decoded = content_file.decoded_content
            return decoded.decode("utf-8", errors="replace")
        except UnknownObjectException:
            return None
        except GithubException as exc:
            logger.warning("file_content_fetch_failed", path=file_path, error=str(exc))
            return None

    def _search_issues_sync(self, query: str, limit: int) -> list[dict]:
        try:
            issues = self._gh.search_issues(query)
            result: list[dict] = []
            for issue in issues:
                if len(result) >= limit:
                    break
                # PyGithub returns PRs in issue list; filter them out
                if issue.pull_request:
                    continue
                try:
                    repo = issue.repository
                    try:
                        topics = list(repo.get_topics())
                    except Exception:
                        topics = []
                    
                    repo_dict = {
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "description": repo.description,
                        "url": repo.html_url,
                        "stars": repo.stargazers_count,
                        "forks": repo.forks_count,
                        "open_issues_count": repo.open_issues_count,
                        "primary_language": repo.language,
                        "topics": topics,
                    }
                    mapped_issue = self._map_issue(issue)
                    result.append({
                        "issue": mapped_issue,
                        "repository": repo_dict
                    })
                except Exception as e:
                    logger.warning("failed_mapping_search_issue", error=str(e))
                    continue
            return result
        except GithubException as exc:
            raise GitHubAPIError(
                f"Failed to search issues with query: {query}",
                details=str(exc),
            ) from exc

    @staticmethod
    def _map_issue(issue: object) -> GitHubIssue:  # type: ignore[type-arg]
        """Map a PyGithub Issue object to our domain ``GitHubIssue``."""
        return GitHubIssue(
            number=issue.number,  # type: ignore[attr-defined]
            title=issue.title,  # type: ignore[attr-defined]
            body=issue.body,  # type: ignore[attr-defined]
            labels=[lbl.name for lbl in issue.labels],  # type: ignore[attr-defined]
            state=issue.state,  # type: ignore[attr-defined]
            created_at=_utc(issue.created_at),  # type: ignore[attr-defined]
            updated_at=_utc(issue.updated_at),  # type: ignore[attr-defined]
            url=issue.html_url,  # type: ignore[attr-defined]
            comments_count=issue.comments,  # type: ignore[attr-defined]
            author=issue.user.login if issue.user else "",  # type: ignore[attr-defined]
        )
