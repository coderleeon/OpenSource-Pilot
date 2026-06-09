"""Contribution Workflow Service orchestrating the complete contributor workflow."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from app.agents.code_analysis_agent import CodeAnalysisAgent
from app.agents.contribution_workflow_agent import ContributionWorkflowAgent
from app.agents.issue_agent import IssueAgent, _score_issue
from app.agents.repo_agent import RepoAgent
from app.core.exceptions import OpenSourcePilotError, StructureParseError
from app.core.logging import get_logger
from app.models.issue import IssueType

logger = get_logger(__name__)


class ContributionWorkflowService:
    """Orchestrates the end-to-end contributor workflow.

    This service coordinates:
    1. Repository metadata fetching & structure parsing (RepoAgent)
    2. GitHub issue fetching & suitability ranking (IssueAgent)
    3. Issue classification (IssueAgent)
    4. Code indexing & semantic search (CodeAnalysisAgent - contribution plans only)
    5. Agent-based plan, test, and PR generation (ContributionWorkflowAgent)
    6. Performance timing and structured logging.
    """

    def __init__(
        self,
        repo_agent: RepoAgent,
        issue_agent: IssueAgent,
        code_analysis_agent: CodeAnalysisAgent,
        workflow_agent: ContributionWorkflowAgent,
    ) -> None:
        self._repo_agent = repo_agent
        self._issue_agent = issue_agent
        self._code_agent = code_analysis_agent
        self._workflow_agent = workflow_agent

    async def run_complete_workflow(self, repo_url: str, issue_number: int) -> dict:  # type: ignore[type-arg]
        """Orchestrate and execute the complete workflow for the given repository and issue.

        Args:
            repo_url: GitHub repository URL.
            issue_number: The GitHub issue number.

        Returns:
            A structured dict mapped to CompleteWorkflowResponse.
        """
        start_time = time.perf_counter()
        started_at = datetime.now(timezone.utc)
        started_at_iso = started_at.isoformat()

        logger.info(
            "complete_workflow_start",
            repo_url=repo_url,
            issue_number=issue_number,
            started_at=started_at_iso,
        )

        errors: list[str] = []
        status = "completed"

        try:
            # Step 1: Ensure repository is cloned and parse metadata
            logger.info("complete_workflow_fetching_repo", repo_url=repo_url)
            repo_metadata = await self._repo_agent.analyze(repo_url)

            # Check for empty repository
            if repo_metadata.file_tree.count_files() == 0:
                raise StructureParseError(
                    f"Repository {repo_url} is empty.",
                    details="No source files found in the directory tree.",
                )

            # Step 2: Fetch specific issue
            logger.info("complete_workflow_fetching_issue", repo_url=repo_url, issue_number=issue_number)
            issue = await self._issue_agent.get_issue(repo_url, issue_number)

            # Step 3: Classify issue
            logger.info("complete_workflow_classifying_issue", issue_number=issue_number)
            issue_type = self._issue_agent.classify(issue)

            # Compute issue score details
            score, difficulty, beginner_friendly, _matching = _score_issue(issue)

            search_results = []
            if issue_type.needs_contribution_plan:
                logger.info("complete_workflow_indexing_repo", repo=repo_metadata.full_name)
                # Step 4: Index repository if needed
                await self._code_agent.index_repo(repo_metadata)

                # Step 5: Semantic Code Search
                logger.info("complete_workflow_semantic_search", query=issue.title[:60])
                search_query = issue.full_text[:500]
                search_results = await self._code_agent.search(
                    repo_full_name=repo_metadata.full_name,
                    query=search_query,
                    n_results=10,
                )
            else:
                logger.info(
                    "complete_workflow_skipping_search",
                    issue_type=issue_type.value,
                    reason="Issue is a question/discussion; skipping semantic search and indexing.",
                )

            # Step 6: Invoke workflow agent (plan, test gen, PR draft gen)
            logger.info("complete_workflow_agent_execution", issue_number=issue_number)
            agent_results = await self._workflow_agent.execute_workflow(
                issue=issue,
                repo_metadata=repo_metadata,
                relevant_code=search_results,
                issue_type=issue_type,
            )

            plan = agent_results["contribution_plan"]
            generated_tests = agent_results["generated_tests"]
            pr_draft = agent_results["pr_draft"]

            completed_at = datetime.now(timezone.utc)
            duration_seconds = time.perf_counter() - start_time

            logger.info(
                "complete_workflow_success",
                repo=repo_metadata.full_name,
                issue_number=issue_number,
                issue_type=issue_type.value,
                duration_seconds=duration_seconds,
            )

            return {
                "repository": {
                    "name": repo_metadata.name,
                    "full_name": repo_metadata.full_name,
                    "description": repo_metadata.description,
                    "url": repo_metadata.url,
                    "primary_language": repo_metadata.primary_language,
                    "default_branch": repo_metadata.default_branch,
                },
                "issue": {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "labels": issue.labels,
                    "state": issue.state,
                    "url": issue.url,
                    "comments_count": issue.comments_count,
                    "author": issue.author,
                    "created_at": issue.created_at.isoformat(),
                },
                "classification": {
                    "issue_type": issue_type.value,
                    "issue_type_display": issue_type.display_name,
                    "difficulty_estimate": difficulty,
                    "suitability_score": score,
                    "beginner_friendly": beginner_friendly,
                },
                "relevant_files": list(dict.fromkeys(r["file_path"] for r in search_results)),
                "search_results": [
                    {
                        "file_path": r["file_path"],
                        "language": r["language"],
                        "snippet": r["text"][:800],
                        "relevance_distance": r["distance"],
                    }
                    for r in search_results
                ],
                "contribution_plan": {
                    "plan_type": plan.plan_type,
                    "issue_type": plan.issue_type,
                    "problem_explanation": plan.problem_explanation,
                    "root_cause_hypothesis": plan.root_cause_hypothesis,
                    "implementation_steps": plan.implementation_steps,
                    "files_to_modify": plan.files_to_modify,
                    "relevant_concepts": plan.relevant_concepts,
                    "estimated_effort": plan.estimated_effort,
                    "references": plan.references,
                    "answer_explanation": plan.answer_explanation,
                    "key_questions": plan.key_questions,
                    "suggested_resources": plan.suggested_resources,
                },
                "generated_tests": {
                    "framework": generated_tests.framework,
                    "test_file_path": generated_tests.test_file_path,
                    "unit_tests": generated_tests.unit_tests,
                    "integration_tests": generated_tests.integration_tests,
                    "edge_cases": generated_tests.edge_cases,
                    "dependencies": generated_tests.dependencies,
                    "setup_notes": generated_tests.setup_notes,
                } if generated_tests else None,
                "pr_draft": {
                    "title": pr_draft.title,
                    "summary": pr_draft.summary,
                    "testing_checklist": pr_draft.testing_checklist,
                    "reviewer_notes": pr_draft.reviewer_notes,
                    "labels_suggested": pr_draft.labels_suggested,
                    "draft_body": pr_draft.draft_body,
                } if pr_draft else None,
                "estimated_effort": plan.estimated_effort if plan.plan_type == "contribution" else None,
                "metadata": {
                    "status": status,
                    "started_at": started_at_iso,
                    "completed_at": completed_at.isoformat(),
                    "duration_seconds": round(duration_seconds, 3),
                    "errors": errors,
                },
            }

        except Exception as exc:
            duration_seconds = time.perf_counter() - start_time
            logger.exception(
                "complete_workflow_failed",
                repo_url=repo_url,
                issue_number=issue_number,
                duration_seconds=duration_seconds,
                error=str(exc),
            )
            # Re-raise standard OpenSourcePilot errors directly so middleware handles them correctly.
            if isinstance(exc, OpenSourcePilotError):
                raise exc
            # Otherwise wrap unexpected errors in standard exception.
            raise OpenSourcePilotError(
                "An unexpected error occurred during the workflow execution.",
                details=str(exc),
            ) from exc
