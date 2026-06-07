"""Planning Agent: generates structured contribution plans using an LLM.

Plan type is chosen based on the classified issue type:

- ``bug`` / ``feature_request`` / ``documentation``
  → ``_contribution_plan()`` — implementation steps + files to modify
- ``question`` / ``discussion``
  → ``_answer_plan()`` — explanation + key questions + resources
- ``unknown``
  → ``_contribution_plan()`` (safest fallback)
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.llm.base import LLMClient
from app.models.issue import ContributionPlan, GitHubIssue, IssueType
from app.models.repo import RepoMetadata

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_CONTRIBUTION_SYSTEM = """\
You are an expert software engineer and experienced open-source contributor.
Your role is to help new contributors tackle GitHub issues with concrete,
actionable implementation plans.

Guidelines:
- Be specific — name actual files, functions, and patterns from the code snippets
- Order implementation steps chronologically and logically
- Be honest about effort; don't over-promise
- Respond ONLY with the JSON object, no other text
"""

_ANSWER_SYSTEM = """\
You are a senior software engineer helping community members understand a project.
Your role is to provide clear, helpful answers to questions and discussion threads.

Guidelines:
- Explain concepts clearly without jargon where possible
- Reference specific parts of the codebase when relevant
- Suggest further reading and related documentation
- Respond ONLY with the JSON object, no other text
"""

# ---------------------------------------------------------------------------
# JSON schemas embedded in prompts
# ---------------------------------------------------------------------------

_CONTRIBUTION_SCHEMA = """\
{
  "problem_explanation": "Clear, jargon-free explanation of what the issue is about and why it matters",
  "root_cause_hypothesis": "Your best hypothesis about the underlying cause or missing functionality",
  "implementation_steps": [
    "Step 1: ...",
    "Step 2: ...",
    "..."
  ],
  "files_to_modify": [
    "relative/path/to/file.py",
    "..."
  ],
  "relevant_concepts": [
    "Concept a contributor needs to understand",
    "..."
  ],
  "estimated_effort": "e.g. '1-2 hours', 'half day', '1-2 days'",
  "references": [
    "Optional: URLs to docs, related issues, or relevant code"
  ]
}"""

_ANSWER_SCHEMA = """\
{
  "problem_explanation": "Neutral summary of what is being asked or discussed",
  "answer_explanation": "Your full answer or explanation — as many paragraphs as needed",
  "key_questions": [
    "Follow-up question or aspect worth clarifying",
    "..."
  ],
  "suggested_resources": [
    "URL to relevant documentation, tutorial, or example",
    "..."
  ],
  "references": [
    "Optional: related issues, PRs, or discussions"
  ]
}"""

# ---------------------------------------------------------------------------
# Shared prompt builder helpers
# ---------------------------------------------------------------------------


def _format_code_context(relevant_code: list[dict]) -> str:  # type: ignore[type-arg]
    sections: list[str] = []
    seen: set[str] = set()
    for result in relevant_code[:8]:
        fp = result.get("file_path", "unknown")
        text = result.get("text", "")
        lang = result.get("language", "")
        if fp not in seen:
            seen.add(fp)
        sections.append(
            f"### File: `{fp}` (language: {lang})\n```\n{text[:800]}\n```"
        )
    return "\n\n".join(sections) if sections else "No code context available."


def _repo_context(repo_metadata: RepoMetadata) -> str:
    tech = repo_metadata.tech_stack
    return (
        f"**Repository:** {repo_metadata.full_name}\n"
        f"**Description:** {repo_metadata.description or 'No description'}\n"
        f"**Primary Language:** {repo_metadata.primary_language or 'Unknown'}\n"
        f"**Tech Stack:** {tech.to_summary()}"
    )


def _issue_header(issue: GitHubIssue) -> str:
    labels_str = ", ".join(issue.labels) if issue.labels else "none"
    return (
        f"## Issue #{issue.number}: {issue.title}\n\n"
        f"**Labels:** {labels_str}  "
        f"**Comments:** {issue.comments_count}  "
        f"**URL:** {issue.url}\n\n"
        f"**Description:**\n{issue.body or 'No description provided.'}"
    )


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def _build_contribution_prompt(
    issue: GitHubIssue,
    repo_metadata: RepoMetadata,
    relevant_code: list[dict],  # type: ignore[type-arg]
    issue_type: IssueType,
) -> str:
    code_context = _format_code_context(relevant_code)
    contributing_snippet = ""
    if repo_metadata.contributing_content:
        snippet = repo_metadata.contributing_content[:1000]
        contributing_snippet = f"\n## Contributing Guide (excerpt)\n{snippet}\n"

    type_instruction = {
        IssueType.BUG: (
            "This is a **bug report**. Focus on diagnosing the root cause and providing "
            "concrete steps to reproduce, locate, and fix the issue."
        ),
        IssueType.FEATURE_REQUEST: (
            "This is a **feature request**. Focus on where to add the new functionality, "
            "what API changes are needed, and how to implement it cleanly."
        ),
        IssueType.DOCUMENTATION: (
            "This is a **documentation issue**. Focus on which doc files need updating, "
            "what examples or explanations to add, and how to verify the result."
        ),
    }.get(
        issue_type,
        "Provide a practical implementation plan for this issue.",
    )

    return f"""# GitHub Issue Analysis — Contribution Plan

{_repo_context(repo_metadata)}

{_issue_header(issue)}
{contributing_snippet}
## Task Context

{type_instruction}

## Relevant Code (from semantic search)

{code_context}

---

Return a JSON contribution plan following this exact schema:

{_CONTRIBUTION_SCHEMA}

Respond with ONLY the JSON object."""


def _build_answer_prompt(
    issue: GitHubIssue,
    repo_metadata: RepoMetadata,
    relevant_code: list[dict],  # type: ignore[type-arg]
    issue_type: IssueType,
) -> str:
    code_context = _format_code_context(relevant_code)

    type_instruction = {
        IssueType.QUESTION: (
            "This is a **question**. Provide a clear, accurate, and complete answer. "
            "Reference relevant code or documentation where helpful."
        ),
        IssueType.DISCUSSION: (
            "This is a **discussion or RFC**. Summarise the proposal, list pros/cons "
            "or considerations, and suggest how the community might proceed."
        ),
    }.get(
        issue_type,
        "Provide a helpful explanation or answer for this issue.",
    )

    return f"""# GitHub Issue Analysis — Answer / Explanation Plan

{_repo_context(repo_metadata)}

{_issue_header(issue)}

## Task Context

{type_instruction}

## Relevant Code (for context)

{code_context}

---

Return a JSON answer plan following this exact schema:

{_ANSWER_SCHEMA}

Respond with ONLY the JSON object."""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class PlanningAgent(BaseAgent):
    """Generates structured plans for GitHub issues using an LLM.

    Plan type (contribution vs answer) is selected based on the classified
    ``IssueType`` before the LLM call.

    Args:
        llm_client: An ``LLMClient`` instance (OpenRouter, OpenAI, or Anthropic).
    """

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__()
        self._llm = llm_client

    async def generate_plan(
        self,
        issue: GitHubIssue,
        repo_metadata: RepoMetadata,
        relevant_code: list[dict],  # type: ignore[type-arg]
        issue_type: IssueType = IssueType.UNKNOWN,
    ) -> ContributionPlan:
        """Generate a plan appropriate for the issue type.

        Dispatches to either ``_contribution_plan()`` or ``_answer_plan()``
        based on ``issue_type``.

        Args:
            issue: The GitHub issue to analyse.
            repo_metadata: Repository context.
            relevant_code: Semantically relevant code snippets from ChromaDB.
            issue_type: Pre-classified issue type (from ``IssueAgent.classify``).

        Returns:
            A populated ``ContributionPlan`` with ``plan_type`` set appropriately.

        Raises:
            LLMError: If the LLM call fails.
            LLMParseError: If the response cannot be parsed as JSON.
        """
        self.logger.info(
            "generating_plan",
            repo=repo_metadata.full_name,
            issue=issue.number,
            issue_type=issue_type.value,
            plan_type="answer" if issue_type.needs_answer_plan else "contribution",
        )

        if issue_type.needs_answer_plan:
            return await self._answer_plan(issue, repo_metadata, relevant_code, issue_type)
        return await self._contribution_plan(issue, repo_metadata, relevant_code, issue_type)

    async def _contribution_plan(
        self,
        issue: GitHubIssue,
        repo_metadata: RepoMetadata,
        relevant_code: list[dict],  # type: ignore[type-arg]
        issue_type: IssueType,
    ) -> ContributionPlan:
        """Generate a contribution plan (implementation steps + files to modify)."""
        prompt = _build_contribution_prompt(issue, repo_metadata, relevant_code, issue_type)
        raw = await self._llm.complete_json(
            prompt=prompt,
            system=_CONTRIBUTION_SYSTEM,
            temperature=0.2,
            max_tokens=3000,
        )
        self.logger.info(
            "contribution_plan_generated",
            repo=repo_metadata.full_name,
            issue=issue.number,
            steps=len(raw.get("implementation_steps", [])),
        )
        return ContributionPlan(
            plan_type="contribution",
            issue_type=issue_type.value,
            problem_explanation=raw.get("problem_explanation", ""),
            root_cause_hypothesis=raw.get("root_cause_hypothesis", ""),
            implementation_steps=raw.get("implementation_steps", []),
            files_to_modify=raw.get("files_to_modify", []),
            relevant_concepts=raw.get("relevant_concepts", []),
            estimated_effort=raw.get("estimated_effort", ""),
            references=raw.get("references", []),
        )

    async def _answer_plan(
        self,
        issue: GitHubIssue,
        repo_metadata: RepoMetadata,
        relevant_code: list[dict],  # type: ignore[type-arg]
        issue_type: IssueType,
    ) -> ContributionPlan:
        """Generate an answer/explanation plan (no code changes expected)."""
        prompt = _build_answer_prompt(issue, repo_metadata, relevant_code, issue_type)
        raw = await self._llm.complete_json(
            prompt=prompt,
            system=_ANSWER_SYSTEM,
            temperature=0.3,
            max_tokens=2000,
        )
        self.logger.info(
            "answer_plan_generated",
            repo=repo_metadata.full_name,
            issue=issue.number,
            issue_type=issue_type.value,
        )
        return ContributionPlan(
            plan_type="answer",
            issue_type=issue_type.value,
            problem_explanation=raw.get("problem_explanation", ""),
            answer_explanation=raw.get("answer_explanation", ""),
            key_questions=raw.get("key_questions", []),
            suggested_resources=raw.get("suggested_resources", []),
            references=raw.get("references", []),
            # Explicitly empty for answer plans
            implementation_steps=[],
            files_to_modify=[],
            root_cause_hypothesis="",
            relevant_concepts=[],
            estimated_effort="",
        )

    async def summarize_repo(
        self,
        repo_metadata: RepoMetadata,
    ) -> dict[str, str]:  # type: ignore[type-arg]
        """Generate a human-readable summary of the repository.

        Args:
            repo_metadata: Full repository metadata including README content.

        Returns:
            Dict with keys ``readme_summary`` and ``contribution_guide_summary``.
        """
        tech = repo_metadata.tech_stack
        readme_snippet = self._truncate(repo_metadata.readme_content, max_chars=4000)
        contributing_snippet = self._truncate(repo_metadata.contributing_content, max_chars=2000)

        prompt = f"""Summarise the following open-source repository for a new contributor.

**Repository:** {repo_metadata.full_name}
**Description:** {repo_metadata.description or 'No description'}
**Primary Language:** {repo_metadata.primary_language or 'Unknown'}
**Tech Stack:** {tech.to_summary()}
**Stars:** {repo_metadata.stars:,}

## README (excerpt)
{readme_snippet or 'No README found.'}

## Contributing Guide (excerpt)
{contributing_snippet or 'No contributing guide found.'}

Return a JSON object with exactly these keys:
{{
  "readme_summary": "2-3 sentence summary of what the project does and its main features",
  "contribution_guide_summary": "2-3 sentences on how to contribute (setup, PR process, coding style)"
}}

Respond with ONLY the JSON object."""

        self.logger.info("summarizing_repo", repo=repo_metadata.full_name)
        raw = await self._llm.complete_json(
            prompt=prompt,
            system="You are a concise technical writer. Summarise open-source projects clearly.",
            temperature=0.2,
        )

        return {
            "readme_summary": raw.get("readme_summary", ""),
            "contribution_guide_summary": raw.get("contribution_guide_summary", ""),
        }

    async def generate_architecture_summary(
        self,
        repo_metadata: RepoMetadata,
    ) -> str:
        """Generate a concise architecture overview of the repository.

        Uses the top-level directory structure, tech stack, and README snippet
        to let the LLM infer the architectural pattern and summarise it.

        Args:
            repo_metadata: Full repository metadata.

        Returns:
            A 2-4 sentence plain-English architecture summary.
        """
        tech = repo_metadata.tech_stack
        key_dirs = repo_metadata.file_tree.get_key_directories()
        readme_snippet = self._truncate(repo_metadata.readme_content, max_chars=2000)

        slim = repo_metadata.file_tree.to_slim_dict(max_depth=2)
        top_level_items = ", ".join(
            f"{'📁' if c.get('is_dir') else '📄'} {c['name']}"
            for c in slim.get("children", [])
        )

        prompt = f"""Analyse this open-source repository and describe its software architecture in 2-4 sentences.

**Repository:** {repo_metadata.full_name}
**Description:** {repo_metadata.description or 'No description'}
**Primary Language:** {repo_metadata.primary_language or 'Unknown'}
**Tech Stack:** {tech.to_summary()}

**Top-level project structure:**
{top_level_items or '(no items)'}

**Key directories:** {', '.join(key_dirs) if key_dirs else 'none detected'}

**README excerpt:**
{readme_snippet or 'No README available.'}

Describe:
1. The overall architectural pattern (e.g. MVC, layered, plugin-based, microservices, library).
2. What each major directory section is responsible for.
3. Any notable design choices visible from the structure.

Return a JSON object with a single key:
{{
  "architecture_summary": "Your 2-4 sentence architecture description here"
}}

Respond with ONLY the JSON object."""

        self.logger.info("generating_architecture_summary", repo=repo_metadata.full_name)
        raw = await self._llm.complete_json(
            prompt=prompt,
            system=(
                "You are a senior software architect. Describe project architectures concisely "
                "and accurately based on directory structure and tech stack clues."
            ),
            temperature=0.2,
            max_tokens=512,
        )

        return raw.get("architecture_summary", "")
