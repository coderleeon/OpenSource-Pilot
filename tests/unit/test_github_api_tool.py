"""Unit tests for GitHubAPITool URL parsing and error mapping."""

from __future__ import annotations

import pytest

from app.core.exceptions import GitHubAPIError
from app.tools.github_api_tool import _parse_repo_slug


class TestParseRepoSlug:
    """Tests for the URL parsing utility."""

    def test_standard_https_url(self) -> None:
        owner, repo = _parse_repo_slug("https://github.com/pallets/flask")
        assert owner == "pallets"
        assert repo == "flask"

    def test_url_with_trailing_slash(self) -> None:
        owner, repo = _parse_repo_slug("https://github.com/pallets/flask/")
        assert owner == "pallets"
        assert repo == "flask"

    def test_url_with_git_suffix(self) -> None:
        owner, repo = _parse_repo_slug("https://github.com/pallets/flask.git")
        assert owner == "pallets"
        assert repo == "flask"

    def test_url_without_scheme(self) -> None:
        owner, repo = _parse_repo_slug("github.com/pallets/flask")
        assert owner == "pallets"
        assert repo == "flask"

    def test_url_http(self) -> None:
        owner, repo = _parse_repo_slug("http://github.com/org/repo")
        assert owner == "org"
        assert repo == "repo"

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(GitHubAPIError, match="Invalid GitHub URL"):
            _parse_repo_slug("https://gitlab.com/org/repo")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(GitHubAPIError):
            _parse_repo_slug("")

    def test_non_url_raises(self) -> None:
        with pytest.raises(GitHubAPIError):
            _parse_repo_slug("not a url at all")

    def test_hyphenated_org(self) -> None:
        owner, repo = _parse_repo_slug("https://github.com/my-org/my-repo")
        assert owner == "my-org"
        assert repo == "my-repo"

    def test_numeric_names(self) -> None:
        owner, repo = _parse_repo_slug("https://github.com/org123/repo456")
        assert owner == "org123"
        assert repo == "repo456"
