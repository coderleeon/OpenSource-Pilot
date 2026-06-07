"""Unit tests for issue type classification (classify_issue_type)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.agents.issue_agent import IssueAgent, classify_issue_type
from app.models.issue import GitHubIssue, IssueType


def _issue(
    title: str = "Test issue",
    body: str | None = None,
    labels: list[str] | None = None,
) -> GitHubIssue:
    """Factory for lightweight test issues."""
    return GitHubIssue(
        number=1,
        title=title,
        body=body,
        labels=labels or [],
        state="open",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        url="https://github.com/org/repo/issues/1",
        comments_count=0,
        author="tester",
    )


# ---------------------------------------------------------------------------
# Label-based classification
# ---------------------------------------------------------------------------


class TestLabelBasedClassification:
    def test_bug_label(self) -> None:
        assert classify_issue_type(_issue(labels=["bug"])) == IssueType.BUG

    def test_defect_label(self) -> None:
        assert classify_issue_type(_issue(labels=["defect"])) == IssueType.BUG

    def test_regression_label(self) -> None:
        assert classify_issue_type(_issue(labels=["regression"])) == IssueType.BUG

    def test_enhancement_label(self) -> None:
        assert classify_issue_type(_issue(labels=["enhancement"])) == IssueType.FEATURE_REQUEST

    def test_feature_request_label(self) -> None:
        assert classify_issue_type(_issue(labels=["feature request"])) == IssueType.FEATURE_REQUEST

    def test_feature_request_hyphenated(self) -> None:
        assert classify_issue_type(_issue(labels=["feature-request"])) == IssueType.FEATURE_REQUEST

    def test_documentation_label(self) -> None:
        assert classify_issue_type(_issue(labels=["documentation"])) == IssueType.DOCUMENTATION

    def test_docs_label(self) -> None:
        assert classify_issue_type(_issue(labels=["docs"])) == IssueType.DOCUMENTATION

    def test_question_label(self) -> None:
        assert classify_issue_type(_issue(labels=["question"])) == IssueType.QUESTION

    def test_support_label(self) -> None:
        assert classify_issue_type(_issue(labels=["support"])) == IssueType.QUESTION

    def test_discussion_label(self) -> None:
        assert classify_issue_type(_issue(labels=["discussion"])) == IssueType.DISCUSSION

    def test_rfc_label(self) -> None:
        assert classify_issue_type(_issue(labels=["rfc"])) == IssueType.DISCUSSION

    def test_proposal_label(self) -> None:
        assert classify_issue_type(_issue(labels=["proposal"])) == IssueType.DISCUSSION

    def test_question_takes_priority_over_bug(self) -> None:
        """Question label should win over bug label (question checked first)."""
        result = classify_issue_type(_issue(labels=["question", "bug"]))
        assert result == IssueType.QUESTION

    def test_mixed_case_label(self) -> None:
        """Label matching is case-insensitive."""
        assert classify_issue_type(_issue(labels=["Bug"])) == IssueType.BUG

    def test_uppercase_label(self) -> None:
        assert classify_issue_type(_issue(labels=["ENHANCEMENT"])) == IssueType.FEATURE_REQUEST

    def test_empty_labels_no_crash(self) -> None:
        """Empty label list should not raise."""
        result = classify_issue_type(_issue(labels=[]))
        assert isinstance(result, IssueType)


# ---------------------------------------------------------------------------
# Title-prefix classification (no labels)
# ---------------------------------------------------------------------------


class TestTitlePrefixClassification:
    def test_how_prefix_question(self) -> None:
        assert classify_issue_type(_issue(title="how to configure the session timeout?")) == IssueType.QUESTION

    def test_what_prefix_question(self) -> None:
        assert classify_issue_type(_issue(title="what is the recommended approach?")) == IssueType.QUESTION

    def test_why_prefix_question(self) -> None:
        assert classify_issue_type(_issue(title="why does the cache invalidate early")) == IssueType.QUESTION

    def test_can_prefix_question(self) -> None:
        assert classify_issue_type(_issue(title="can we support async views?")) == IssueType.QUESTION

    def test_title_ends_with_question_mark(self) -> None:
        assert classify_issue_type(_issue(title="Is this still maintained?")) == IssueType.QUESTION

    def test_rfc_prefix_discussion(self) -> None:
        assert classify_issue_type(_issue(title="RFC: new plugin system")) == IssueType.DISCUSSION

    def test_proposal_prefix_discussion(self) -> None:
        assert classify_issue_type(_issue(title="Proposal: deprecate the old API")) == IssueType.DISCUSSION

    def test_discussion_prefix_discussion(self) -> None:
        assert classify_issue_type(_issue(title="Discussion: future direction of the project")) == IssueType.DISCUSSION

    def test_bracket_rfc_discussion(self) -> None:
        assert classify_issue_type(_issue(title="[RFC] Change the session backend")) == IssueType.DISCUSSION


# ---------------------------------------------------------------------------
# Body keyword fallback
# ---------------------------------------------------------------------------


class TestBodyKeywordClassification:
    def test_crash_in_body(self) -> None:
        issue = _issue(title="Unexpected error", body="The app crashes when I call foo().")
        assert classify_issue_type(issue) == IssueType.BUG

    def test_not_working_in_body(self) -> None:
        issue = _issue(title="Problem found", body="The timeout is not working as expected.")
        assert classify_issue_type(issue) == IssueType.BUG

    def test_regression_in_body(self) -> None:
        issue = _issue(title="Problem", body="This is a regression from v2.0.")
        assert classify_issue_type(issue) == IssueType.BUG

    def test_implement_in_body(self) -> None:
        issue = _issue(title="Suggestion", body="We should implement support for OAuth.")
        assert classify_issue_type(issue) == IssueType.FEATURE_REQUEST

    def test_add_in_body(self) -> None:
        issue = _issue(title="New capability", body="Add a new flag to the CLI.")
        assert classify_issue_type(issue) == IssueType.FEATURE_REQUEST


# ---------------------------------------------------------------------------
# Fallback to UNKNOWN
# ---------------------------------------------------------------------------


class TestUnknownFallback:
    def test_no_signals_returns_unknown(self) -> None:
        issue = _issue(title="Lorem ipsum", body="Dolor sit amet.")
        result = classify_issue_type(issue)
        assert result == IssueType.UNKNOWN


# ---------------------------------------------------------------------------
# IssueType properties
# ---------------------------------------------------------------------------


class TestIssueTypeProperties:
    def test_bug_needs_contribution_plan(self) -> None:
        assert IssueType.BUG.needs_contribution_plan is True

    def test_feature_request_needs_contribution_plan(self) -> None:
        assert IssueType.FEATURE_REQUEST.needs_contribution_plan is True

    def test_documentation_needs_contribution_plan(self) -> None:
        assert IssueType.DOCUMENTATION.needs_contribution_plan is True

    def test_question_needs_answer_plan(self) -> None:
        assert IssueType.QUESTION.needs_answer_plan is True

    def test_discussion_needs_answer_plan(self) -> None:
        assert IssueType.DISCUSSION.needs_answer_plan is True

    def test_unknown_does_not_need_answer_plan(self) -> None:
        assert IssueType.UNKNOWN.needs_answer_plan is False

    def test_display_names_are_human_readable(self) -> None:
        assert IssueType.BUG.display_name == "Bug Report"
        assert IssueType.FEATURE_REQUEST.display_name == "Feature Request"
        assert IssueType.QUESTION.display_name == "Question"
        assert IssueType.DISCUSSION.display_name == "Discussion"
        assert IssueType.DOCUMENTATION.display_name == "Documentation"

    def test_is_str_enum_value(self) -> None:
        """IssueType values should serialize as plain strings."""
        assert IssueType.BUG == "bug"
        assert IssueType.QUESTION == "question"
