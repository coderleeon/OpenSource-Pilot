"""Issue Service: orchestrates the complete issue analysis workflow."""

from __future__ import annotations

from app.agents.code_analysis_agent import CodeAnalysisAgent
from app.agents.issue_agent import IssueAgent, IssueRanking, _score_issue
from app.agents.planning_agent import PlanningAgent
from app.agents.repo_agent import RepoAgent
from app.core.logging import get_logger
from app.models.issue import GitHubIssue, IssueType

logger = get_logger(__name__)


class IssueService:
    """Orchestrates issue retrieval, code search, and contribution plan generation.

    This service is the entry point for the ``POST /analyze-issue`` endpoint.
    It chains all four agents to produce a complete issue analysis.

    Args:
        repo_agent: Handles repository cloning and metadata.
        issue_agent: Handles GitHub issue retrieval and ranking.
        code_analysis_agent: Handles semantic code search.
        planning_agent: Handles LLM contribution plan generation.
    """

    def __init__(
        self,
        repo_agent: RepoAgent,
        issue_agent: IssueAgent,
        code_analysis_agent: CodeAnalysisAgent,
        planning_agent: PlanningAgent,
    ) -> None:
        self._repo = repo_agent
        self._issues = issue_agent
        self._code = code_analysis_agent
        self._planner = planning_agent

    async def analyze_issue(
        self,
        repo_url: str,
        issue_number: int,
    ) -> dict:  # type: ignore[type-arg]
        """Run the complete issue analysis workflow.

        Steps:
        1. ``RepoAgent.analyze`` — ensure repo is cloned and parsed.
        2. ``IssueAgent.get_issue`` — fetch the specific issue.
        2.5. ``IssueAgent.classify`` — classify issue type (bug / feature / question…).
        3. ``CodeAnalysisAgent.index_repo`` — index code if not already done.
        4. ``CodeAnalysisAgent.search`` — find relevant code snippets.
        5. ``PlanningAgent.generate_plan`` — produce a type-appropriate plan.

        Args:
            repo_url: GitHub repository URL.
            issue_number: Issue number to analyse.

        Returns:
            Issue analysis result dict compatible with the API response schema.
        """
        logger.info("issue_analysis_start", url=repo_url, issue=issue_number)

        # Step 1: Ensure repo is cloned and we have metadata
        repo_metadata = await self._repo.analyze(repo_url)

        # Step 2: Fetch the specific issue
        issue: GitHubIssue = await self._issues.get_issue(repo_url, issue_number)

        # Step 2.5: Classify the issue type
        issue_type: IssueType = self._issues.classify(issue)
        logger.info(
            "issue_classified",
            issue=issue_number,
            issue_type=issue_type.value,
            plan_type="answer" if issue_type.needs_answer_plan else "contribution",
        )

        # Step 3: Index if not already done
        await self._code.index_repo(repo_metadata)

        # Step 4: Semantic search using issue title + body as query
        search_query = issue.full_text[:500]  # keep query manageable
        relevant_code = await self._code.search(
            repo_full_name=repo_metadata.full_name,
            query=search_query,
            n_results=10,
        )

        # Step 5: Generate type-appropriate plan
        plan = await self._planner.generate_plan(
            issue=issue,
            repo_metadata=repo_metadata,
            relevant_code=relevant_code,
            issue_type=issue_type,
        )

        # Score / rank the issue for difficulty info
        score, difficulty, beginner_friendly, matching_labels = _score_issue(issue)

        logger.info(
            "issue_analysis_complete",
            repo=repo_metadata.full_name,
            issue=issue_number,
            issue_type=issue_type.value,
            difficulty=difficulty,
        )

        return {
            "repo_name": repo_metadata.full_name,
            "issue_type": issue_type.value,
            "issue_type_display": issue_type.display_name,
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
            "difficulty_estimate": difficulty,
            "beginner_friendly": beginner_friendly,
            "suitability_score": score,
            "relevant_files": list(
                dict.fromkeys(r["file_path"] for r in relevant_code)
            ),  # unique, order-preserving
            "relevant_code_snippets": [
                {
                    "file_path": r["file_path"],
                    "language": r["language"],
                    "snippet": r["text"][:600],
                    "relevance_distance": r["distance"],
                }
                for r in relevant_code[:5]
            ],
            "contribution_plan": {
                "plan_type": plan.plan_type,
                "issue_type": plan.issue_type,
                "problem_explanation": plan.problem_explanation,
                # Contribution-plan fields (empty for answer plans)
                "root_cause_hypothesis": plan.root_cause_hypothesis,
                "implementation_steps": plan.implementation_steps,
                "files_to_modify": plan.files_to_modify,
                "relevant_concepts": plan.relevant_concepts,
                "estimated_effort": plan.estimated_effort,
                "references": plan.references,
                # Answer-plan fields (empty for contribution plans)
                "answer_explanation": plan.answer_explanation,
                "key_questions": plan.key_questions,
                "suggested_resources": plan.suggested_resources,
            },
        }

    async def list_issues(
        self,
        repo_url: str,
        limit: int = 30,
    ) -> dict:  # type: ignore[type-arg]
        """List and rank open issues for a repository.

        Args:
            repo_url: GitHub repository URL.
            limit: Maximum number of issues to return.

        Returns:
            Dict with ranked issues list.
        """
        logger.info("listing_issues", url=repo_url, limit=limit)
        rankings = await self._issues.list_issues(repo_url, limit=limit)

        return {
            "repo_url": repo_url,
            "total_returned": len(rankings),
            "issues": [
                {
                    "number": r.issue.number,
                    "title": r.issue.title,
                    "labels": r.issue.labels,
                    "state": r.issue.state,
                    "url": r.issue.url,
                    "comments_count": r.issue.comments_count,
                    "difficulty_estimate": r.difficulty_estimate,
                    "suitability_score": r.score,
                    "beginner_friendly": r.beginner_friendly,
                    "required_skills": r.required_skills,
                    "issue_type": r.issue_type.value,
                    "issue_type_display": r.issue_type.display_name,
                }
                for r in rankings
            ],
        }
