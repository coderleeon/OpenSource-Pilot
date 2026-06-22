"""FastAPI dependency injection helpers.

All service and tool instances are stored on ``app.state`` during the
application lifespan and retrieved here via ``Request`` injection.
This avoids module-level singletons and keeps dependencies testable.
"""

from __future__ import annotations

from fastapi import Request

from app.services.contribution_workflow_service import ContributionWorkflowService
from app.services.issue_service import IssueService
from app.services.radar_service import RadarService
from app.services.repo_service import RepoService
from app.services.search_service import SearchService


def get_repo_service(request: Request) -> RepoService:
    """Retrieve the ``RepoService`` singleton from application state."""
    return request.app.state.repo_service  # type: ignore[no-any-return]


def get_issue_service(request: Request) -> IssueService:
    """Retrieve the ``IssueService`` singleton from application state."""
    return request.app.state.issue_service  # type: ignore[no-any-return]


def get_search_service(request: Request) -> SearchService:
    """Retrieve the ``SearchService`` singleton from application state."""
    return request.app.state.search_service  # type: ignore[no-any-return]


def get_contribution_workflow_service(request: Request) -> ContributionWorkflowService:
    """Retrieve the ``ContributionWorkflowService`` singleton from application state."""
    return request.app.state.contribution_workflow_service  # type: ignore[no-any-return]


def get_radar_service(request: Request) -> RadarService:
    """Retrieve the ``RadarService`` singleton from application state."""
    return request.app.state.radar_service  # type: ignore[no-any-return]
