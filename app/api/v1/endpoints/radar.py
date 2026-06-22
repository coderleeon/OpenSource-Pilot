"""Radar API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_radar_service
from app.api.v1.schemas.radar import (
    DiscoverRequest,
    DiscoverResponse,
    MissingFeaturesRequest,
    MissingFeaturesResponse,
    RepoHealthDetailResponse,
    RepoHealthRequest,
)
from app.services.radar_service import RadarService

router = APIRouter(prefix="/radar", tags=["Open Source Radar"])


@router.post(
    "/discover",
    response_model=DiscoverResponse,
    summary="Discover open source contribution opportunities",
    description=(
        "Searches GitHub for issues matching user skills, technologies, interests, "
        "and experience level. Heuristically ranks them and runs a parallel LLM "
        "compatibility fit score, merge probability, and repo health assessment."
    ),
)
async def discover_opportunities(
    request: DiscoverRequest,
    service: Annotated[RadarService, Depends(get_radar_service)],
) -> DiscoverResponse:
    """Find and rank suitable open source opportunities."""
    result = await service.discover(
        skills=request.skills,
        technologies=request.technologies,
        interests=request.interests,
        experience_level=request.experience_level,
    )
    return DiscoverResponse(opportunities=result)


@router.post(
    "/missing-features",
    response_model=MissingFeaturesResponse,
    summary="Detect missing capabilities in a repository",
    description=(
        "Analyzes repository metadata, topics, and README contents "
        "to suggest missing features or enhancement recommendations."
    ),
)
async def detect_missing_features(
    request: MissingFeaturesRequest,
    service: Annotated[RadarService, Depends(get_radar_service)],
) -> MissingFeaturesResponse:
    """Evaluate repository and return recommended missing feature candidates."""
    result = await service.get_missing_features(repo_url=request.repo_url)
    return MissingFeaturesResponse(**result)


@router.post(
    "/repo-health",
    response_model=RepoHealthDetailResponse,
    summary="Generate repository health insights",
    description="Evaluate repository activity, release cycles, and maintainer engagement.",
)
async def get_repository_health(
    request: RepoHealthRequest,
    service: Annotated[RadarService, Depends(get_radar_service)],
) -> RepoHealthDetailResponse:
    """Generate repository health scores and summaries."""
    result = await service.get_repo_health(repo_url=request.repo_url)
    return RepoHealthDetailResponse(**result)
