"""Top-level API router aggregating all versioned sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.issue import router as issue_router
from app.api.v1.endpoints.repo import router as repo_router

router = APIRouter()

# Mount v1 endpoints under /api/v1 (the prefix is set in main.py)
router.include_router(repo_router)
router.include_router(issue_router)
