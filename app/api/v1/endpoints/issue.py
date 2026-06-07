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
