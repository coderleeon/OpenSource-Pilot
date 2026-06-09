"""Contribution Workflow Agent orchestrating LLM-based agents.

Given repository context, classified issue type, and relevant code, this
agent coordinates the execution of downstream planning, test generation,
and PR drafting agents.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.pr_agent import PRAgent
from app.agents.test_generation_agent import TestGenerationAgent
from app.models.issue import (
    ContributionPlan,
    GeneratedTests,
    GitHubIssue,
    IssueType,
    PRDraft,
)
from app.models.repo import RepoMetadata


class ContributionWorkflowAgent(BaseAgent):
    """Orchestrates LLM-based agents for the contributor workflow.

    Delegates to individual specialized agents:
    - PlanningAgent for generating plans (contribution or answer)
    - TestGenerationAgent for generating test suites (contribution plans only)
    - PRAgent for generating PR descriptions (contribution plans only)
    """

    def __init__(
        self,
        planning_agent: PlanningAgent,
        test_generation_agent: TestGenerationAgent,
        pr_agent: PRAgent,
    ) -> None:
        super().__init__()
        self._planning_agent = planning_agent
        self._test_gen = test_generation_agent
        self._pr = pr_agent

    async def execute_workflow(
        self,
        issue: GitHubIssue,
        repo_metadata: RepoMetadata,
        relevant_code: list[dict],  # type: ignore[type-arg]
        issue_type: IssueType,
    ) -> dict:  # type: ignore[type-arg]
        """Run the LLM-based agents in sequence based on the issue type.

        Args:
            issue: The GitHub issue.
            repo_metadata: Metadata of the repository.
            relevant_code: Code snippets from semantic search.
            issue_type: Classified type of the issue.

        Returns:
            Dict containing:
            - "contribution_plan": ContributionPlan
            - "generated_tests": GeneratedTests | None
            - "pr_draft": PRDraft | None
        """
        self.logger.info(
            "workflow_agent_execution_start",
            issue=issue.number,
            issue_type=issue_type.value,
        )

        # 1. Generate Plan (contribution or answer)
        plan: ContributionPlan = await self._planning_agent.generate_plan(
            issue=issue,
            repo_metadata=repo_metadata,
            relevant_code=relevant_code,
            issue_type=issue_type,
        )

        generated_tests: GeneratedTests | None = None
        pr_draft: PRDraft | None = None

        # 2. If contribution-oriented, generate tests and PR draft
        if issue_type.needs_contribution_plan:
            self.logger.info("generating_tests_and_pr_draft", issue=issue.number)
            generated_tests = await self._test_gen.generate_tests(
                issue=issue,
                plan=plan,
                relevant_code=relevant_code,
                repo_metadata=repo_metadata,
            )

            pr_draft = await self._pr.generate_pr_draft(
                issue=issue,
                plan=plan,
                repo_metadata=repo_metadata,
            )
        else:
            self.logger.info(
                "skipping_tests_and_pr_draft",
                issue=issue.number,
                reason="Issue is classified as non-contribution (question/discussion)",
            )

        self.logger.info("workflow_agent_execution_complete", issue=issue.number)

        return {
            "contribution_plan": plan,
            "generated_tests": generated_tests,
            "pr_draft": pr_draft,
        }
