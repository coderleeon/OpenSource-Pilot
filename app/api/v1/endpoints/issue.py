"""Issue analysis API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_issue_service
from app.api.v1.schemas.issue import (
    IssueAnalyzeRequest,
    IssueAnalyzeResponse,
    IssueListRequest,
    IssueListResponse,
    PRDraftRequest,
    PRDraftResponseEnvelope,
    TestGenerationRequest,
    TestGenerationResponse,
)
from app.services.issue_service import IssueService

router = APIRouter(prefix="/issue", tags=["Issue Analysis"])


@router.post(
    "/analyze",
    response_model=IssueAnalyzeResponse,
    summary="Analyse a specific GitHub issue",
    description=(
        "Fetches the issue, performs semantic code search to find relevant files, "
        "and generates a detailed LLM contribution plan including implementation "
        "steps, files to modify, and effort estimate."
    ),
)
async def analyze_issue(
    request: IssueAnalyzeRequest,
    service: Annotated[IssueService, Depends(get_issue_service)],
) -> IssueAnalyzeResponse:
    """Run a full issue analysis and return the contribution plan."""
    result = await service.analyze_issue(
        repo_url=request.repo_url,
        issue_number=request.issue_number,
    )
    return IssueAnalyzeResponse(**result)


@router.post(
    "/list",
    response_model=IssueListResponse,
    summary="List and rank open issues for a repository",
    description=(
        "Retrieves open issues from the repository and ranks them by contribution "
        "suitability (based on labels, complexity, and comment count)."
    ),
)
async def list_issues(
    request: IssueListRequest,
    service: Annotated[IssueService, Depends(get_issue_service)],
) -> IssueListResponse:
    """Return a ranked list of open issues."""
    result = await service.list_issues(
        repo_url=request.repo_url,
        limit=request.limit,
    )
    return IssueListResponse(**result)


@router.post(
    "/generate-tests",
    response_model=TestGenerationResponse,
    summary="Generate a test suite for a GitHub issue contribution",
    description=(
        "Analyses the issue and its contribution plan, then generates unit tests, "
        "integration tests, and edge-case scenarios using the repository's testing "
        "framework. Returns complete, runnable test source code."
    ),
)
async def generate_tests(
    request: TestGenerationRequest,
    service: Annotated[IssueService, Depends(get_issue_service)],
) -> TestGenerationResponse:
    """Generate unit, integration, and edge-case tests for a contribution."""
    result = await service.generate_tests(
        repo_url=request.repo_url,
        issue_number=request.issue_number,
    )
    return TestGenerationResponse(**result)


@router.post(
    "/generate-pr-draft",
    response_model=PRDraftResponseEnvelope,
    summary="Generate a pull request draft for a GitHub issue contribution",
    description=(
        "Analyses the issue and its contribution plan, then generates a structured "
        "PR draft including title (conventional commit format), summary, testing "
        "checklist, reviewer notes, suggested labels, and a fully assembled PR body."
    ),
)
async def generate_pr_draft(
    request: PRDraftRequest,
    service: Annotated[IssueService, Depends(get_issue_service)],
) -> PRDraftResponseEnvelope:
    """Generate a PR draft for a contribution."""
    result = await service.generate_pr_draft(
        repo_url=request.repo_url,
        issue_number=request.issue_number,
    )
    return PRDraftResponseEnvelope(**result)
