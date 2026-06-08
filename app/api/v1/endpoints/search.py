"""Semantic code search API endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_search_service
from app.api.v1.schemas.search import CodeSearchRequest, CodeSearchResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Code Search"])


@router.post(
    "/code",
    response_model=CodeSearchResponse,
    summary="Semantic code search over a repository",
    description=(
        "Clones the repository (if not already cached), indexes it into ChromaDB "
        "(if not already indexed), and performs a semantic search returning the "
        "most relevant code snippets. Results are ordered by relevance."
    ),
)
async def search_code(
    request: CodeSearchRequest,
    service: Annotated[SearchService, Depends(get_search_service)],
) -> CodeSearchResponse:
    """Run a semantic search and return ranked code snippets."""
    result = await service.search_code(
        repo_url=request.repo_url,
        query=request.query,
        n_results=request.n_results,
    )
    return CodeSearchResponse(**result)
