"""Test Generation Agent: produces LLM-generated test suites for contribution plans.

Given a GitHub issue, its contribution plan, and relevant code snippets, this
agent generates three blocks of tests:

- **Unit tests** — isolated tests for individual functions/methods, using mocks
  where needed.
- **Integration tests** — tests that exercise how components interact.
- **Edge-case scenarios** — boundary conditions, error paths, and unexpected inputs.

The output is framework-aware: the prompt adapts based on the primary language
detected from ``RepoMetadata.tech_stack`` (Python → pytest, JavaScript/TypeScript
→ Jest, etc.).
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.llm.base import LLMClient
from app.models.issue import ContributionPlan, GeneratedTests, GitHubIssue
from app.models.repo import RepoMetadata

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM = """\
You are a senior software engineer who writes clean, production-quality tests.
Your role is to generate comprehensive test suites for open-source contributions.

Guidelines:
- Write real, runnable test code — not pseudocode or placeholders
- Use the framework appropriate for the repository language
- Cover happy paths, sad paths, and boundary conditions
- Prefer small, focused tests with descriptive names
- Add meaningful assertions, not just "assert result is not None"
- Include necessary imports at the top of each test block
- Respond ONLY with the JSON object, no other text
"""

# ---------------------------------------------------------------------------
# JSON schema
# ---------------------------------------------------------------------------

_SCHEMA = """\
{
  "unit_tests": "Complete Python/JS/etc unit test source code with imports",
  "integration_tests": "Complete integration test source code with imports",
  "edge_cases": "Complete edge-case / error-path test source code with imports",
  "test_file_path": "Suggested relative path for the test file, e.g. tests/test_sessions.py",
  "framework": "e.g. 'pytest', 'unittest', 'jest', 'mocha'",
  "dependencies": ["e.g. pytest-mock", "httpx"],
  "setup_notes": "Any setup steps or env config needed to run the tests"
}"""


def _detect_framework(repo_metadata: RepoMetadata) -> str:
    """Infer the most appropriate testing framework from the tech stack."""
    langs = {l.lower() for l in repo_metadata.tech_stack.languages}
    tools = {t.lower() for t in repo_metadata.tech_stack.tools}
    frameworks = {f.lower() for f in repo_metadata.tech_stack.frameworks}

    if "javascript" in langs or "typescript" in langs:
        if "jest" in tools or "jest" in frameworks:
            return "Jest"
        return "Jest"  # de-facto standard for JS/TS

    if "go" in langs:
        return "testing (Go standard library)"

    if "rust" in langs:
        return "Rust built-in test harness"

    if "java" in langs:
        return "JUnit 5"

    # Default: Python → pytest
    return "pytest"


def _format_plan_context(plan: ContributionPlan) -> str:
    """Format the contribution plan as a concise LLM-readable block."""
    if plan.plan_type == "answer":
        return "This issue is a question/discussion; no implementation tests needed."

    steps = "\n".join(f"  {i + 1}. {s}" for i, s in enumerate(plan.implementation_steps))
    files = "\n".join(f"  - {f}" for f in plan.files_to_modify)
    return (
        f"**Root Cause:** {plan.root_cause_hypothesis}\n\n"
        f"**Implementation Steps:**\n{steps or '  (none listed)'}\n\n"
        f"**Files to Modify:**\n{files or '  (none listed)'}\n\n"
        f"**Relevant Concepts:** {', '.join(plan.relevant_concepts) or 'none'}"
    )


def _format_code_context(relevant_code: list[dict]) -> str:  # type: ignore[type-arg]
    """Format relevant code snippets for the prompt."""
    if not relevant_code:
        return "No relevant code snippets available."
    sections: list[str] = []
    seen: set[str] = set()
    for r in relevant_code[:6]:
        fp = r.get("file_path", "unknown")
        if fp in seen:
            continue
        seen.add(fp)
        text = r.get("text", "")[:600]
        lang = r.get("language", "")
        sections.append(f"### `{fp}` ({lang})\n```\n{text}\n```")
    return "\n\n".join(sections)


class TestGenerationAgent(BaseAgent):
    """Generates unit, integration, and edge-case tests for a GitHub contribution.

    Args:
        llm_client: An ``LLMClient`` instance (OpenRouter, OpenAI, or Anthropic).
    """

    __test__ = False

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__()
        self._llm = llm_client

    async def generate_tests(
        self,
        issue: GitHubIssue,
        plan: ContributionPlan,
        relevant_code: list[dict],  # type: ignore[type-arg]
        repo_metadata: RepoMetadata,
    ) -> GeneratedTests:
        """Generate a comprehensive test suite for a contribution.

        Args:
            issue: The GitHub issue being addressed.
            plan: The contribution plan (provides files to modify + steps).
            relevant_code: Semantically relevant code snippets from ChromaDB.
            repo_metadata: Repository metadata (tech stack, language, etc.).

        Returns:
            A ``GeneratedTests`` instance with unit, integration, and edge-case tests.

        Raises:
            LLMError: If the LLM call fails.
            LLMParseError: If the response cannot be parsed as JSON.
        """
        framework = _detect_framework(repo_metadata)
        tech = repo_metadata.tech_stack

        self.logger.info(
            "generating_tests",
            repo=repo_metadata.full_name,
            issue=issue.number,
            framework=framework,
            plan_type=plan.plan_type,
        )

        prompt = f"""# Test Generation for GitHub Issue #{issue.number}

## Repository Context
**Repository:** {repo_metadata.full_name}
**Description:** {repo_metadata.description or 'No description'}
**Primary Language:** {repo_metadata.primary_language or 'Unknown'}
**Tech Stack:** {tech.to_summary()}
**Testing Framework:** {framework}

## Issue
**Title:** {issue.title}
**Labels:** {', '.join(issue.labels) if issue.labels else 'none'}
**Description:**
{self._truncate(issue.body or 'No description provided.', max_chars=800)}

## Contribution Plan
{_format_plan_context(plan)}

## Relevant Existing Code (for reference)
{_format_code_context(relevant_code)}

---

Generate a comprehensive test suite using **{framework}** that covers:

1. **Unit tests**: Test each function/method in isolation. Mock external dependencies.
2. **Integration tests**: Test how the changed components interact with the rest of the system.
3. **Edge cases**: Test boundary conditions, empty inputs, invalid data, error paths, and race conditions.

Return a JSON object following this exact schema:

{_SCHEMA}

Important:
- Each test block must be **complete, runnable source code** with all imports included.
- Test names must be descriptive (e.g. `test_session_expires_after_timeout_with_utc_datetime`).
- Do NOT use placeholder comments like `# TODO: implement`.

Respond with ONLY the JSON object."""

        raw = await self._llm.complete_json(
            prompt=prompt,
            system=_SYSTEM,
            temperature=0.2,
            max_tokens=4000,
        )

        result = GeneratedTests(
            unit_tests=raw.get("unit_tests", ""),
            integration_tests=raw.get("integration_tests", ""),
            edge_cases=raw.get("edge_cases", ""),
            test_file_path=raw.get("test_file_path", "tests/test_generated.py"),
            framework=raw.get("framework", framework),
            dependencies=raw.get("dependencies", []),
            setup_notes=raw.get("setup_notes", ""),
        )

        self.logger.info(
            "tests_generated",
            repo=repo_metadata.full_name,
            issue=issue.number,
            framework=result.framework,
            test_file=result.test_file_path,
        )
        return result
