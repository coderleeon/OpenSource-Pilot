"""Radar Service orchestrating opportunity discovery and repository radar features."""

from __future__ import annotations

from app.agents.radar_agent import RadarAgent
from app.core.logging import get_logger

logger = get_logger(__name__)


class RadarService:
    """Orchestrates global issue discovery, health analysis, and feature recommendations.

    Args:
        radar_agent: Configured RadarAgent instance.
    """

    def __init__(self, radar_agent: RadarAgent) -> None:
        self._radar_agent = radar_agent

    async def discover(
        self,
        skills: list[str],
        technologies: list[str],
        interests: list[str],
        experience_level: str = "beginner",
        limit: int = 5,
    ) -> list[dict]:
        """Perform discovery and return detailed contribution opportunities."""
        logger.info("radar_service_discover_start", skills=skills, technologies=technologies)
        return await self._radar_agent.discover_opportunities(
            skills=skills,
            technologies=technologies,
            interests=interests,
            experience_level=experience_level,
            limit=limit,
        )

    async def get_missing_features(self, repo_url: str) -> dict:
        """Fetch potential missing feature recommendations for a repository."""
        logger.info("radar_service_missing_features_start", repo_url=repo_url)
        features = await self._radar_agent.get_missing_features(repo_url)
        return {
            "repo_name": repo_url.split("/")[-1],
            "missing_features": features,
        }

    async def get_repo_health(self, repo_url: str) -> dict:
        """Evaluate repository activity and return health scores."""
        logger.info("radar_service_repo_health_start", repo_url=repo_url)
        health = await self._radar_agent.get_repo_health(repo_url)
        return {
            "repo_name": repo_url.split("/")[-1],
            "repo_health": health,
        }
