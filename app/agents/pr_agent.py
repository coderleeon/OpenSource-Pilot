"""PR Agent: generates a structured pull request draft from a contribution plan.

Given a GitHub issue and its contribution plan, this agent produces:

- A concise PR **title** in conventional-commit style
- A markdown **summary** explaining what changed and why
- A **testing checklist** for the reviewer to verify
- **Reviewer notes** covering design decisions, trade-offs, and risk areas
- Suggested **labels** based on the issue type and affected areas
- A fully assembled **draft body** combining all sections
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.llm.base import LLMClient
from app.models.issue import ContributionPlan, GitHubIssue, PRDraft
from app.models.repo import RepoMetadata

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM = """\
You are an experienced open-source maintainer and contributor.
Your role is to write clear, professional pull request descriptions that help
reviewers understand the change, its motivation, and how to verify it.

Guidelines:
- PR titles should follow conventional commit format: type(scope): description
  Examples: fix(sessions): handle timezone-aware datetime expiry
            feat(cli): add --format flag to output command
- Summaries should be written in present tense ("Fix ...", "Add ...")
- Testing checklists should be specific and verifiable — no vague items
- Reviewer notes should flag non-obvious decisions and potential risks
- Respond ONLY with the JSON object, no other text
"""

# ---------------------------------------------------------------------------
# JSON schema
# ---------------------------------------------------------------------------

_SCHEMA = """\
{
  "title": "Concise PR title in conventional commit format",
  "summary": "Markdown paragraph(s) describing what changed, why, and how",
  "testing_checklist": [
    "Specific, verifiable item the reviewer should check",
    "..."
  ],
  "reviewer_notes": "Markdown paragraph covering design decisions, trade-offs, or risks",
  "labels_suggested": ["e.g. bug", "needs-review"],
  "draft_body": "Full PR body markdown combining summary + checklist + notes"
}"""


def _format_plan_for_pr(plan: ContributionPlan) -> str:
    """Format the contribution plan as a concise context block for the PR prompt."""
    if plan.plan_type == "answer":
        return "This is a documentation/question issue; the PR may add documentation or examples."

    steps = "\n".join(f"  {i + 1}. {s}" for i, s in enumerate(plan.implementation_steps))
    files = ", ".join(plan.files_to_modify) or "none listed"
    return (
        f"**Problem:** {plan.problem_explanation}\n\n"
        f"**Root Cause:** {plan.root_cause_hypothesis}\n\n"
        f"**Implementation Steps:**\n{steps or '  (none listed)'}\n\n"
        f"**Files Changed:** {files}\n\n"
        f"**Estimated Effort:** {plan.estimated_effort or 'not specified'}"
    )


class PRAgent(BaseAgent):
    """Generates a structured GitHub pull request draft for a contribution.

    Args:
        llm_client: An ``LLMClient`` instance (OpenRouter, OpenAI, or Anthropic).
    """

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__()
        self._llm = llm_client

    async def generate_pr_draft(
        self,
        issue: GitHubIssue,
        plan: ContributionPlan,
        repo_metadata: RepoMetadata,
    ) -> PRDraft:
        """Generate a complete pull request draft for a contribution.

        Args:
            issue: The GitHub issue being resolved.
            plan: The contribution plan describing the implementation.
            repo_metadata: Repository context (name, language, contributing guide).

        Returns:
            A ``PRDraft`` with title, summary, checklist, reviewer notes, labels,
            and a fully assembled ``draft_body``.

        Raises:
            LLMError: If the LLM call fails.
            LLMParseError: If the response cannot be parsed as JSON.
        """
        self.logger.info(
            "generating_pr_draft",
            repo=repo_metadata.full_name,
            issue=issue.number,
            issue_type=plan.issue_type,
        )

        contributing_snippet = ""
        if repo_metadata.contributing_content:
            snip = self._truncate(repo_metadata.contributing_content, max_chars=800)
            contributing_snippet = f"\n## Contributing Guide (excerpt)\n{snip}\n"

        prompt = f"""# Pull Request Draft Generation

## Repository
**Repository:** {repo_metadata.full_name}
**Description:** {repo_metadata.description or 'No description'}
**Primary Language:** {repo_metadata.primary_language or 'Unknown'}
**Tech Stack:** {repo_metadata.tech_stack.to_summary()}
{contributing_snippet}
## Related Issue
**Issue #{issue.number}:** {issue.title}
**Labels:** {', '.join(issue.labels) if issue.labels else 'none'}
**URL:** {issue.url}

**Issue Description:**
{self._truncate(issue.body or 'No description provided.', max_chars=600)}

## Contribution Plan
{_format_plan_for_pr(plan)}

---

Generate a professional pull request description for this contribution.

Return a JSON object following this exact schema:

{_SCHEMA}

The `draft_body` field must be a complete, well-formatted markdown PR body that:
1. Starts with a "## Summary" section
2. Includes a "## Changes" section with the key modifications
3. Includes a "## Testing" section with the checklist as markdown checkboxes (- [ ] item)
4. Ends with a "## Notes for Reviewers" section
5. Includes a footer line: "Closes #{issue.number}"

Respond with ONLY the JSON object."""

        raw = await self._llm.complete_json(
            prompt=prompt,
            system=_SYSTEM,
            temperature=0.3,
            max_tokens=1000,
        )

        # Assemble draft_body if LLM didn't provide it (fallback)
        draft_body = raw.get("draft_body") or _assemble_draft_body(
            title=raw.get("title", ""),
            summary=raw.get("summary", ""),
            checklist=raw.get("testing_checklist", []),
            notes=raw.get("reviewer_notes", ""),
            issue_number=issue.number,
        )

        result = PRDraft(
            title=raw.get("title", f"fix: resolve issue #{issue.number}"),
            summary=raw.get("summary", ""),
            testing_checklist=raw.get("testing_checklist", []),
            reviewer_notes=raw.get("reviewer_notes", ""),
            labels_suggested=raw.get("labels_suggested", []),
            draft_body=draft_body,
        )

        self.logger.info(
            "pr_draft_generated",
            repo=repo_metadata.full_name,
            issue=issue.number,
            title=result.title,
            checklist_items=len(result.testing_checklist),
        )
        return result


def _assemble_draft_body(
    title: str,
    summary: str,
    checklist: list[str],
    notes: str,
    issue_number: int,
) -> str:
    """Fallback PR body assembler when the LLM omits the draft_body field."""
    checklist_md = "\n".join(f"- [ ] {item}" for item in checklist)
    return f"""## Summary

{summary}

## Testing

{checklist_md or '- [ ] All existing tests pass'}

## Notes for Reviewers

{notes}

---

Closes #{issue_number}"""
