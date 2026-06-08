"""FastAPI application factory and lifespan management.

This module wires together the entire dependency graph:

    Settings → Tools → Agents → Services → app.state

All long-lived objects (ChromaTool, LLMClient, …) are created once during
the application lifespan and stored on ``app.state``.  FastAPI dependency
providers in ``app.api.deps`` read from ``app.state`` via the ``Request``
object, keeping the wiring here and nowhere else.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.code_analysis_agent import CodeAnalysisAgent
from app.agents.issue_agent import IssueAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.pr_agent import PRAgent
from app.agents.repo_agent import RepoAgent
from app.agents.test_generation_agent import TestGenerationAgent
from app.api.router import router
from app.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIDMiddleware, register_exception_handlers
from app.llm.factory import create_llm_client_from_settings
from app.services.issue_service import IssueService
from app.services.repo_service import RepoService
from app.services.search_service import SearchService
from app.tools.chroma_tool import ChromaTool
from app.tools.code_chunker import CodeChunker
from app.tools.git_tool import GitTool
from app.tools.github_api_tool import GitHubAPITool
from app.tools.structure_parser import StructureParser


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: build dependency graph, store on app.state, teardown."""
    settings: Settings = get_settings()

    # ------------------------------------------------------------------ Logging
    configure_logging(log_level=settings.log_level, log_format=settings.log_format)
    logger = get_logger(__name__)
    logger.info(
        "opensourcepilot_starting",
        llm_provider=settings.llm_provider,
        llm_model=settings.effective_model,
        log_level=settings.log_level,
    )

    # ------------------------------------------------------------------ Tools
    git_tool = GitTool(clone_base_dir=settings.clone_base_dir)

    github_tool = GitHubAPITool(github_token=settings.github_token)

    structure_parser = StructureParser()

    code_chunker = CodeChunker(
        chunk_size=settings.chunk_size_chars,
        overlap=settings.chunk_overlap_chars,
        max_file_size_kb=settings.max_file_size_kb,
    )

    chroma_tool = ChromaTool(
        persist_dir=settings.chroma_persist_dir,
        embedding_model=settings.embedding_model,
    )

    llm_client = create_llm_client_from_settings(settings)

    # ------------------------------------------------------------------ Agents
    repo_agent = RepoAgent(
        git_tool=git_tool,
        github_tool=github_tool,
        structure_parser=structure_parser,
    )

    issue_agent = IssueAgent(github_tool=github_tool)

    code_analysis_agent = CodeAnalysisAgent(
        chroma_tool=chroma_tool,
        code_chunker=code_chunker,
        max_files=settings.max_files_to_index,
    )

    planning_agent = PlanningAgent(llm_client=llm_client)
    test_generation_agent = TestGenerationAgent(llm_client=llm_client)
    pr_agent = PRAgent(llm_client=llm_client)

    # ------------------------------------------------------------------ Services
    repo_service = RepoService(
        repo_agent=repo_agent,
        code_analysis_agent=code_analysis_agent,
        planning_agent=planning_agent,
    )

    issue_service = IssueService(
        repo_agent=repo_agent,
        issue_agent=issue_agent,
        code_analysis_agent=code_analysis_agent,
        planning_agent=planning_agent,
        test_generation_agent=test_generation_agent,
        pr_agent=pr_agent,
    )

    search_service = SearchService(
        repo_agent=repo_agent,
        code_analysis_agent=code_analysis_agent,
    )

    # ------------------------------------------------------------------ State
    app.state.settings = settings
    app.state.repo_service = repo_service
    app.state.issue_service = issue_service
    app.state.search_service = search_service

    logger.info("opensourcepilot_ready")

    yield

    # ------------------------------------------------------------------ Shutdown
    logger.info("opensourcepilot_shutting_down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A fully configured ``FastAPI`` instance ready to serve requests.
    """
    app = FastAPI(
        title="OpenSourcePilot",
        description=(
            "AI-powered open-source contribution assistant.\n\n"
            "Given a GitHub repository URL, this API analyses the codebase, "
            "discovers suitable issues, and generates structured contribution plans."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ------------------------------------------------------------------ Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)

    # ------------------------------------------------------------------ Exception handlers
    register_exception_handlers(app)

    # ------------------------------------------------------------------ Routes
    app.include_router(router, prefix="/api/v1")

    # Health-check endpoint
    @app.get("/health", tags=["Health"], summary="Health check")
    async def health() -> dict:  # type: ignore[type-arg]
        return {"status": "ok", "service": "opensourcepilot", "version": "0.1.0"}

    return app


# Module-level app instance — used by uvicorn
app = create_app()
