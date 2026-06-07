"""Issue Agent: retrieves and ranks GitHub issues for contribution suitability."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.models.issue import GitHubIssue, IssueRanking, IssueType
from app.tools.github_api_tool import GitHubAPITool

# ---------------------------------------------------------------------------
# Type classification — label maps
# ---------------------------------------------------------------------------

_BUG_LABELS = {
    "bug", "defect", "regression", "crash", "error", "fix", "broken",
    "incorrect", "wrong", "failure", "fault", "issue",
}
_FEATURE_LABELS = {
    "enhancement", "feature", "feature request", "feature-request",
    "new feature", "improvement", "request",
}
_DOCS_LABELS = {
    "documentation", "docs", "readme", "wiki", "doc",
}
_QUESTION_LABELS = {
    "question", "help", "support", "how-to", "faq",
}
_DISCUSSION_LABELS = {
    "discussion", "rfc", "proposal", "brainstorm", "ideas", "wontfix",
    "design", "feedback", "explore",
}

# Prefixes that signal a question title regardless of labels
_QUESTION_TITLE_PREFIXES = (
    "how ", "how to", "what ", "when ", "why ", "where ",
    "can ", "could ", "would ", "should ", "is it ", "is there ",
    "does ", "do ", "will ", "are ",
)
_DISCUSSION_TITLE_PREFIXES = (
    "rfc:", "proposal:", "discussion:", "[rfc]", "[proposal]", "[discussion]",
    "brainstorm:", "idea:", "thoughts on",
)


def classify_issue_type(issue: GitHubIssue) -> IssueType:
    """Classify a GitHub issue by intent using rule-based heuristics.

    The classification priority is:

    1. Label-based matching (highest confidence).
    2. Title prefix / keyword analysis (fallback).
    3. Body keyword analysis (last resort).
    4. ``IssueType.UNKNOWN`` if no signal is found.

    Args:
        issue: The issue to classify.

    Returns:
        The most likely ``IssueType``.
    """
    lower_labels = {lbl.lower() for lbl in issue.labels}
    title_lower = issue.title.lower().strip()
    body_lower = (issue.body or "").lower()
    combined = f"{title_lower} {body_lower}"

    # --- 1. Label-based (exact or substring match) --------------------------
    def _label_matches(label_set: set[str]) -> bool:
        return any(
            any(tag in lbl for tag in label_set)
            for lbl in lower_labels
        )

    if _label_matches(_QUESTION_LABELS):
        return IssueType.QUESTION
    if _label_matches(_DISCUSSION_LABELS):
        return IssueType.DISCUSSION
    if _label_matches(_DOCS_LABELS):
        return IssueType.DOCUMENTATION
    if _label_matches(_BUG_LABELS):
        return IssueType.BUG
    if _label_matches(_FEATURE_LABELS):
        return IssueType.FEATURE_REQUEST

    # --- 2. Title-prefix analysis -------------------------------------------
    for prefix in _DISCUSSION_TITLE_PREFIXES:
        if title_lower.startswith(prefix):
            return IssueType.DISCUSSION

    if title_lower.endswith("?") or any(
        title_lower.startswith(p) for p in _QUESTION_TITLE_PREFIXES
    ):
        return IssueType.QUESTION

    # --- 3. Body / title keyword analysis -----------------------------------
    if "?" in title_lower and len(title_lower) < 120:
        return IssueType.QUESTION

    if any(kw in combined for kw in ("fix ", "fixed ", "fixes ", "crash", "broken", "not working", "regression")):
        return IssueType.BUG

    if any(kw in combined for kw in ("add ", "implement ", "support ", "feature ", "new ", "would be great")):
        return IssueType.FEATURE_REQUEST

    if any(kw in combined for kw in ("document", "readme", " docs ", "clarif", "explain", "example")):
        return IssueType.DOCUMENTATION

    # --- 4. Fallback --------------------------------------------------------
    return IssueType.UNKNOWN


# Labels that indicate a beginner-friendly issue (case-insensitive substring match)
_BEGINNER_LABELS = {
    "good first issue",
    "beginner",
    "starter",
    "easy",
    "newbie",
    "good-first-issue",
    "first-timers-only",
    "good first bug",
    "beginner friendly",
}

# Labels that indicate help is requested (medium difficulty)
_HELP_WANTED_LABELS = {
    "help wanted",
    "help-wanted",
    "contributions welcome",
    "contribution welcome",
}

# Labels that indicate higher complexity
_HARD_LABELS = {
    "performance",
    "architecture",
    "refactor",
    "design",
    "security",
    "breaking change",
    "rfc",
    "epic",
    "complex",
}


def _score_issue(issue: GitHubIssue) -> tuple[float, str, bool, list[str]]:
    """Score an issue for contribution suitability.

    Returns:
        Tuple of (score, difficulty_estimate, beginner_friendly, matching_labels).
        Score is in range [0, 10]; higher = more suitable for new contributors.
    """
    score = 5.0  # neutral baseline
    lower_labels = {lbl.lower() for lbl in issue.labels}
    matching: list[str] = []
    beginner_friendly = False

    # Beginner-friendly labels boost score significantly
    for lbl in lower_labels:
        for tag in _BEGINNER_LABELS:
            if tag in lbl:
                score += 3.0
                beginner_friendly = True
                matching.append(lbl)
                break

    # Help-wanted gives a moderate boost
    for lbl in lower_labels:
        for tag in _HELP_WANTED_LABELS:
            if tag in lbl:
                score += 1.5
                matching.append(lbl)
                break

    # Bug label — slightly accessible (concrete problem)
    if "bug" in lower_labels:
        score += 0.5
        matching.append("bug")

    # Documentation — usually easy
    if "documentation" in lower_labels or "docs" in lower_labels:
        score += 1.0
        matching.append("documentation")

    # High comment count means lots of discussion — harder to navigate
    if issue.comments_count > 20:
        score -= 1.5
    elif issue.comments_count > 10:
        score -= 0.75

    # Hard labels reduce score
    for lbl in lower_labels:
        for tag in _HARD_LABELS:
            if tag in lbl:
                score -= 2.0
                break

    # Very long body often means complex issue
    body_len = len(issue.body or "")
    if body_len > 3000:
        score -= 0.5
    elif body_len < 100:
        score += 0.25  # short, well-defined issue

    # Clamp
    score = max(0.0, min(10.0, score))

    # Difficulty estimate
    if beginner_friendly or score >= 7.5:
        difficulty = "easy"
    elif score >= 5.0:
        difficulty = "medium"
    else:
        difficulty = "hard"

    return round(score, 2), difficulty, beginner_friendly, list(set(matching))


def _infer_skills(issue: GitHubIssue) -> list[str]:
    """Heuristically infer required skills from labels and issue text."""
    skills: set[str] = set()
    combined = " ".join([issue.title, issue.body or ""] + issue.labels).lower()

    skill_keywords = {
        "Python": ["python", ".py", "pytest"],
        "JavaScript": ["javascript", "js", "node"],
        "TypeScript": ["typescript", "ts"],
        "Testing": ["test", "unittest", "pytest", "spec"],
        "Documentation": ["docs", "documentation", "readme"],
        "CI/CD": ["github actions", "ci", "docker", "workflow"],
        "Database": ["database", "sql", "migration", "orm"],
        "API": ["api", "endpoint", "rest", "graphql"],
        "Frontend": ["frontend", "ui", "css", "html"],
        "Performance": ["performance", "optimization", "memory", "speed"],
        "Security": ["security", "vulnerability", "auth", "token"],
        "Async": ["async", "await", "concurrency", "threading"],
    }

    for skill, keywords in skill_keywords.items():
        if any(kw in combined for kw in keywords):
            skills.add(skill)

    return sorted(skills)


class IssueAgent(BaseAgent):
    """Retrieves and ranks GitHub issues for contribution suitability.

    Args:
        github_tool: Configured ``GitHubAPITool`` instance.
    """

    def __init__(self, github_tool: GitHubAPITool) -> None:
        super().__init__()
        self._github = github_tool

    async def list_issues(
        self,
        repo_url: str,
        limit: int = 50,
    ) -> list[IssueRanking]:
        """Retrieve and rank open issues by contribution suitability.

        Args:
            repo_url: GitHub repository URL.
            limit: Maximum number of issues to retrieve.

        Returns:
            List of ``IssueRanking`` objects sorted by score descending.
        """
        self.logger.info("fetching_issues", url=repo_url, limit=limit)
        issues = await self._github.get_issues(repo_url, state="open", limit=limit)
        self.logger.info("issues_fetched", count=len(issues))

        rankings: list[IssueRanking] = []
        for issue in issues:
            score, difficulty, beginner_friendly, matching = _score_issue(issue)
            skills = _infer_skills(issue)
            issue_type = classify_issue_type(issue)
            rankings.append(
                IssueRanking(
                    issue=issue,
                    difficulty_estimate=difficulty,
                    score=score,
                    beginner_friendly=beginner_friendly,
                    required_skills=skills,
                    matching_labels=matching,
                    issue_type=issue_type,
                )
            )

        # Sort by score descending
        rankings.sort(key=lambda r: r.score, reverse=True)
        return rankings

    async def get_issue(self, repo_url: str, issue_number: int) -> GitHubIssue:
        """Retrieve a single issue by number.

        Args:
            repo_url: GitHub repository URL.
            issue_number: Issue number to retrieve.

        Returns:
            The ``GitHubIssue`` domain object.

        Raises:
            IssueNotFoundError: If the issue does not exist.
        """
        self.logger.info("fetching_issue", url=repo_url, number=issue_number)
        return await self._github.get_issue(repo_url, issue_number)

    def classify(self, issue: GitHubIssue) -> IssueType:
        """Classify a single issue by intent.

        Delegates to the module-level ``classify_issue_type`` function.
        Exposed as a method for easy mocking and service-layer use.

        Args:
            issue: The issue to classify.

        Returns:
            The classified ``IssueType``.
        """
        issue_type = classify_issue_type(issue)
        self.logger.debug(
            "issue_classified",
            number=issue.number,
            title=issue.title[:60],
            issue_type=issue_type.value,
        )
        return issue_type
