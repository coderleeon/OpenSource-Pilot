"""Unit tests for RadarAgent opportunity discovery and repository radar evaluation."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.radar_agent import RadarAgent
from app.models.issue import GitHubIssue


@pytest.fixture()
def mock_github_tool_search(sample_issue: GitHubIssue) -> AsyncMock:
    tool = AsyncMock()
    
    # Mock search issues response
    repo_dict = {
        "name": "flask",
        "full_name": "pallets/flask",
        "description": "The Python micro framework.",
        "url": "https://github.com/pallets/flask",
        "stars": 67000,
        "forks": 16000,
        "open_issues_count": 40,
        "primary_language": "Python",
        "topics": ["flask", "python"],
    }
    tool.search_issues = AsyncMock(return_value=[{
        "issue": sample_issue,
        "repository": repo_dict
    }])
    
    # Mock repo response for direct endpoints
    mock_repo = MagicMock()
    mock_repo.name = "flask"
    mock_repo.description = "The Python micro framework."
    mock_repo.language = "Python"
    mock_repo.stargazers_count = 67000
    mock_repo.forks_count = 16000
    mock_repo.open_issues_count = 40
    mock_repo.get_topics = MagicMock(return_value=["flask", "python"])
    tool.get_gh_repo = AsyncMock(return_value=mock_repo)
    tool.get_file_content = AsyncMock(return_value="# Readme Content")
    
    return tool


@pytest.fixture()
def mock_llm_client_radar() -> AsyncMock:
    client = AsyncMock()
    client.complete_json = AsyncMock(return_value={
        # Flat health keys (for direct health query)
        "maintainer_activity": 90,
        "release_frequency": 80,
        "open_issue_trends": "Stable",
        "contribution_velocity": 85,
        "community_engagement": 90,
        "health_explanation": "Healthy project.",
        
        # Flat feature keys (for direct missing features query)
        "missing_features": [
            {
                "feature_name": "Export chats",
                "description": "Export feature.",
                "reasoning": "Standard user request."
            }
        ],
        
        # Nested keys (for composite opportunity discover queries)
        "fit_analysis": {
            "fit_score": 95,
            "difficulty": "Easy",
            "learning_value": "High",
            "reason": "Matches background perfectly."
        },
        "merge_probability": {
            "merge_probability": 85,
            "confidence": "High",
            "explanation": "High maintainer responsiveness."
        },
        "repo_health": {
            "maintainer_activity": 90,
            "release_frequency": 80,
            "open_issue_trends": "Stable",
            "contribution_velocity": 85,
            "community_engagement": 90,
            "health_explanation": "Healthy project."
        }
    })
    return client


@pytest.fixture()
def radar_agent(mock_github_tool_search: AsyncMock, mock_llm_client_radar: AsyncMock) -> RadarAgent:
    return RadarAgent(github_tool=mock_github_tool_search, llm_client=mock_llm_client_radar)  # type: ignore[arg-type]


async def test_discover_opportunities(
    radar_agent: RadarAgent,
    mock_github_tool_search: AsyncMock,
    mock_llm_client_radar: AsyncMock,
) -> None:
    results = await radar_agent.discover_opportunities(
        skills=["Python"],
        technologies=["FastAPI"],
        interests=["Database"],
        experience_level="beginner",
    )
    
    assert len(results) == 1
    opp = results[0]
    
    # Assert opportunity structure
    assert opp["repository"]["name"] == "flask"
    assert opp["issue"]["number"] == 5420
    assert opp["fit_analysis"]["fit_score"] == 95
    assert opp["merge_probability"]["merge_probability"] == 85
    assert opp["repo_health"]["maintainer_activity"] == 90
    assert len(opp["missing_features"]) == 1
    
    # Verify mock invocations
    mock_github_tool_search.search_issues.assert_called_once()
    mock_llm_client_radar.complete_json.assert_called_once()


async def test_get_missing_features(
    radar_agent: RadarAgent,
    mock_github_tool_search: AsyncMock,
    mock_llm_client_radar: AsyncMock,
) -> None:
    features = await radar_agent.get_missing_features("https://github.com/pallets/flask")
    
    assert len(features) == 1
    assert features[0]["feature_name"] == "Export chats"
    
    mock_github_tool_search.get_gh_repo.assert_called_once()
    mock_github_tool_search.get_file_content.assert_called_once()
    mock_llm_client_radar.complete_json.assert_called_once()


async def test_get_repo_health(
    radar_agent: RadarAgent,
    mock_github_tool_search: AsyncMock,
    mock_llm_client_radar: AsyncMock,
) -> None:
    health = await radar_agent.get_repo_health("https://github.com/pallets/flask")
    
    assert health["maintainer_activity"] == 90
    assert health["release_frequency"] == 80
    assert health["open_issue_trends"] == "Stable"
    
    mock_github_tool_search.get_gh_repo.assert_called_once()
    mock_llm_client_radar.complete_json.assert_called_once()
