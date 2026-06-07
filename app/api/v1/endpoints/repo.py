"""Repository analysis API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_repo_service
from app.api.v1.schemas.repo import RepoAnalyzeRequest, RepoAnalyzeResponse
from app.services.repo_service import RepoService

router = APIRouter(prefix="/repo", tags=["Repository Analysis"])


@router.post(
    "/analyze",
    response_model=RepoAnalyzeResponse,
    summary="Analyse a GitHub repository",
    description=(
        "Clones the repository, parses its directory structure, detects the "
        "technology stack, indexes source files into ChromaDB, and generates "
        "an LLM summary of the README and contribution guide."
    ),
)
async def analyze_repo(
    request: RepoAnalyzeRequest,
    service: Annotated[RepoService, Depends(get_repo_service)],
) -> RepoAnalyzeResponse:
    """Run a full repository analysis and return the structured result."""
    result = await service.analyze(
        repo_url=request.repo_url,
        index_code=request.index_code,
    )
    return RepoAnalyzeResponse(**result)
