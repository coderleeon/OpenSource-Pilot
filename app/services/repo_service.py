"""Repository Service: orchestrates the full repository analysis workflow."""

from __future__ import annotations

import uuid

from app.agents.code_analysis_agent import CodeAnalysisAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.repo_agent import RepoAgent
from app.core.logging import get_logger

logger = get_logger(__name__)


class RepoService:
    """Orchestrates repository cloning, indexing, and summarisation.

    This service is the single entry point for the ``POST /analyze-repo``
    endpoint.  It chains the ``RepoAgent``, ``CodeAnalysisAgent``, and
    ``PlanningAgent`` to produce a complete analysis result.

    Args:
        repo_agent: Handles cloning and metadata extraction.
        code_analysis_agent: Handles code chunking and vector indexing.
        planning_agent: Handles LLM-based summarisation.
    """

    def __init__(
        self,
        repo_agent: RepoAgent,
        code_analysis_agent: CodeAnalysisAgent,
        planning_agent: PlanningAgent,
    ) -> None:
        self._repo = repo_agent
        self._code = code_analysis_agent
        self._planner = planning_agent

    async def analyze(
        self,
        repo_url: str,
        index_code: bool = True,
    ) -> dict:  # type: ignore[type-arg]
        """Run the complete repository analysis workflow.

        Steps:
        1. ``RepoAgent.analyze`` — clone + parse structure + GitHub metadata
        2. ``CodeAnalysisAgent.index_repo`` — chunk + embed source files (optional)
        3. ``PlanningAgent.summarize_repo`` — LLM README / CONTRIBUTING summary
        4. ``PlanningAgent.generate_architecture_summary`` — LLM architecture overview

        Args:
            repo_url: GitHub repository URL.
            index_code: If False, skip the ChromaDB indexing step.

        Returns:
            Analysis result dict compatible with the API response schema.
        """
        analysis_id = str(uuid.uuid4())
        logger.info("repo_analysis_start", url=repo_url, analysis_id=analysis_id)

        # Step 1: Clone + parse
        repo_metadata = await self._repo.analyze(repo_url)

        # Step 2: Index code (optional, can be slow for large repos)
        total_indexed = 0
        if index_code:
            total_indexed = await self._code.index_repo(repo_metadata)

        # Step 3: LLM summarisation (README + contributing guide)
        summaries = await self._planner.summarize_repo(repo_metadata)

        # Step 4: LLM architecture summary (uses slim tree + tech stack)
        architecture_summary = await self._planner.generate_architecture_summary(repo_metadata)

        # Compute file/dir counts from the full internal tree
        total_files_count = repo_metadata.file_tree.count_files()
        total_dirs_count = repo_metadata.file_tree.count_dirs()
        key_directories = repo_metadata.file_tree.get_key_directories()

        logger.info(
            "repo_analysis_complete",
            repo=repo_metadata.full_name,
            analysis_id=analysis_id,
            total_indexed=total_indexed,
            total_files=total_files_count,
            total_dirs=total_dirs_count,
        )

        return {
            "analysis_id": analysis_id,
            "repo_name": repo_metadata.name,
            "full_name": repo_metadata.full_name,
            "description": repo_metadata.description,
            "url": repo_metadata.url,
            "primary_language": repo_metadata.primary_language,
            "topics": repo_metadata.topics,
            "stars": repo_metadata.stars,
            "forks": repo_metadata.forks,
            "open_issues_count": repo_metadata.open_issues_count,
            "license_name": repo_metadata.license_name,
            "has_readme": repo_metadata.has_readme,
            "has_contributing_guide": repo_metadata.has_contributing_guide,
            # Depth-2 slim tree for the API — full tree kept internally for indexing
            "directory_structure": repo_metadata.file_tree.to_slim_dict(max_depth=2),
            "total_files_count": total_files_count,
            "total_directories_count": total_dirs_count,
            "key_directories": key_directories,
            "tech_stack": {
                "languages": repo_metadata.tech_stack.languages,
                "frameworks": repo_metadata.tech_stack.frameworks,
                "tools": repo_metadata.tech_stack.tools,
                "package_managers": repo_metadata.tech_stack.package_managers,
            },
            "readme_summary": summaries.get("readme_summary", ""),
            "contribution_guide_summary": summaries.get("contribution_guide_summary", ""),
            "architecture_summary": architecture_summary,
            "total_files_indexed": total_indexed,
        }
