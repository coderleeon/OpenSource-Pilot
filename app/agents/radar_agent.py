"""Radar Agent: discovers and evaluates open-source contribution opportunities."""

from __future__ import annotations

import asyncio
from datetime import datetime
from app.agents.base import BaseAgent
from app.llm.base import LLMClient
from app.models.issue import GitHubIssue
from app.tools.github_api_tool import GitHubAPITool
from app.core.logging import get_logger

logger = get_logger(__name__)

_RADAR_SYSTEM_PROMPT = """\
You are an advanced open-source repository analyst. Your task is to evaluate a GitHub issue and its repository context to generate:
1. Contributor Fit Score: Evaluate compatibility with user's skills/experience.
2. Merge Probability: Predict acceptance likelihood based on repository activity and history.
3. Repository Health: Gauge activity metrics.
4. Missing Feature Detection: Suggest potential valuable capabilities missing in the repository based on description.

Respond with a JSON object matching this exact schema:
{
  "fit_analysis": {
    "fit_score": 91,
    "difficulty": "Easy",
    "learning_value": "High",
    "reason": "Matches Python and FastAPI experience."
  },
  "merge_probability": {
    "merge_probability": 82,
    "confidence": "Medium",
    "explanation": "Maintainers are moderately active, but there is an open PR backlog."
  },
  "repo_health": {
    "maintainer_activity": 85,
    "release_frequency": 70,
    "open_issue_trends": "Stable",
    "contribution_velocity": 75,
    "community_engagement": 80,
    "health_explanation": "Strong community engagement with weekly releases."
  },
  "missing_features": [
    {
      "feature_name": "Export chats",
      "description": "Add support for exporting chatbot conversations in JSON or CSV formats.",
      "reasoning": "Since this is a chatbot, users will naturally need to export logs for backup."
    }
  ]
}

Respond with ONLY the JSON object, no other text."""


class RadarAgent(BaseAgent):
    """Discovers, ranks, and analyzes contribution opportunities."""

    def __init__(self, github_tool: GitHubAPITool, llm_client: LLMClient) -> None:
        super().__init__()
        self._github = github_tool
        self._llm = llm_client

    async def discover_opportunities(
        self,
        skills: list[str],
        technologies: list[str],
        interests: list[str],
        experience_level: str = "beginner",
        limit: int = 5,
    ) -> list[dict]:
        """Query GitHub for relevant issues and rank them by suitability."""
        keywords = []
        for lst in [skills, technologies, interests]:
            for item in lst:
                if item and item.strip():
                    keywords.append(item.strip())

        query_parts = ["is:issue", "is:open"]
        if experience_level.lower() == "beginner":
            query_parts.append('(label:"good first issue" OR label:easy OR label:beginner OR label:"good-first-issue")')
        elif experience_level.lower() == "intermediate":
            query_parts.append('(label:"help wanted" OR label:help-wanted OR label:"contributions welcome")')

        if keywords:
            query_parts.append(" ".join(f'"{kw}"' for kw in keywords))

        query = " ".join(query_parts)
        self.logger.info("searching_github_opportunities", query=query)

        # Retrieve a candidate pool (up to 15 issues to rank/filter)
        raw_results = await self._github.search_issues(query=query, limit=15)
        if not raw_results and keywords:
            # Fallback search without label constraints if no results
            fallback_query = "is:issue is:open " + " ".join(f'"{kw}"' for kw in keywords)
            self.logger.info("no_results_falling_back", fallback_query=fallback_query)
            raw_results = await self._github.search_issues(query=fallback_query, limit=15)

        if not raw_results:
            return []

        # Heuristic scoring
        scored_candidates = []
        for opp in raw_results:
            issue = opp["issue"]
            repo = opp["repository"]

            # 1. Freshness Score (up to 2.5 points)
            age_days = issue.age_days
            freshness = max(0.0, 2.5 - (age_days / 120.0))

            # 2. Repo Activity Score (up to 2.5 points)
            stars = repo["stars"]
            forks = repo["forks"]
            activity = min(2.5, (stars / 5000.0) + (forks / 1000.0))

            # 3. Community Health Score (up to 2.5 points)
            open_issues = repo["open_issues_count"]
            health = 2.5 if open_issues < 150 else max(0.5, 2.5 - (open_issues / 800.0))

            # 4. Friendliness Score (up to 2.5 points)
            labels_lower = [lbl.lower() for lbl in issue.labels]
            friendliness = 0.5
            if any(lbl in ["good first issue", "easy", "beginner", "good-first-issue", "first-timers-only"] for lbl in labels_lower):
                friendliness += 2.0
            elif any(lbl in ["help wanted", "help-wanted", "contributions welcome"] for lbl in labels_lower):
                friendliness += 1.0

            rank_score = freshness + activity + health + friendliness
            scored_candidates.append((rank_score, opp))

        # Sort candidate pool and take top N
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        top_candidates = [opp for score, opp in scored_candidates[:limit]]

        # Perform parallel LLM analysis
        tasks = [
            self._analyze_single_opportunity(opp, skills, technologies, interests, experience_level)
            for opp in top_candidates
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        opportunities = []
        for opp, res in zip(top_candidates, results):
            issue = opp["issue"]
            if not isinstance(issue, dict):
                # Safely map attributes to dictionary.
                # GitHubIssue properties: number, title, body, labels, url, comments_count, author, created_at, age_days
                created_at_val = getattr(issue, "created_at", None)
                if created_at_val is not None:
                    if hasattr(created_at_val, "isoformat"):
                        created_at_str = created_at_val.isoformat()
                    else:
                        created_at_str = str(created_at_val)
                else:
                    created_at_str = ""

                age_days_val = getattr(issue, "age_days", 0)

                issue_dict = {
                    "number": getattr(issue, "number", 0),
                    "title": getattr(issue, "title", ""),
                    "body": getattr(issue, "body", ""),
                    "labels": getattr(issue, "labels", []),
                    "url": getattr(issue, "url", ""),
                    "comments_count": getattr(issue, "comments_count", 0),
                    "author": getattr(issue, "author", ""),
                    "created_at": created_at_str,
                    "age_days": age_days_val,
                }
            else:
                issue_dict = issue

            opp_dict = {
                "repository": opp["repository"],
                "issue": issue_dict,
            }

            if isinstance(res, Exception):
                self.logger.warning("llm_evaluation_failed", error=str(res))
                # Fallback default analysis values
                opp_dict.update({
                    "fit_analysis": {
                        "fit_score": 70,
                        "difficulty": "Medium",
                        "learning_value": "Medium",
                        "reason": "Unable to contact evaluation service. Estimated average fit."
                    },
                    "merge_probability": {
                        "merge_probability": 75,
                        "confidence": "Medium",
                        "explanation": "Standard check skipped due to timeout."
                    },
                    "repo_health": {
                        "maintainer_activity": 80,
                        "release_frequency": 75,
                        "open_issue_trends": "Stable",
                        "contribution_velocity": 70,
                        "community_engagement": 75,
                        "health_explanation": "Healthy baseline repository."
                    },
                    "missing_features": []
                })
            else:
                opp_dict.update(res)
            opportunities.append(opp_dict)

        return opportunities

    async def get_missing_features(self, repo_url: str) -> list[dict]:
        """Detect missing features from a repository description/README."""
        repo = await self._github.get_gh_repo(repo_url)
        topics = list(repo.get_topics()) if hasattr(repo, "get_topics") else []
        
        # Fetch README summary or README content to pass to LLM
        readme = await self._github.get_file_content(repo_url, "README.md")
        if not readme:
            readme = await self._github.get_file_content(repo_url, "readme.md")
        
        readme_snippet = readme[:3000] if readme else "No README file found."

        prompt = f"""Identify 4 potential missing features or enhancement capabilities for this repository.
        
        Repository Name: {repo.name}
        Description: {repo.description or 'No description provided.'}
        Primary Language: {repo.language}
        Topics: {', '.join(topics)}
        
        README Context:
        {readme_snippet}
        
        Return a JSON object matching this schema:
        {{
          "missing_features": [
            {{
              "feature_name": "Feature Title",
              "description": "What the feature does",
              "reasoning": "Why this would benefit the repository users"
            }}
          ]
        }}
        Respond with ONLY the JSON object, no other text."""

        try:
            res = await self._llm.complete_json(prompt=prompt, temperature=0.3)
            return res.get("missing_features", [])
        except Exception as exc:
            self.logger.warning("llm_missing_features_failed", error=str(exc))
            return []

    async def get_repo_health(self, repo_url: str) -> dict:
        """Evaluate repository health scores and return visual insights."""
        repo = await self._github.get_gh_repo(repo_url)
        
        prompt = f"""Analyze the repository health and activity metrics.
        
        Repository Name: {repo.name}
        Description: {repo.description or 'No description provided.'}
        Stars: {repo.stargazers_count}
        Forks: {repo.forks_count}
        Open Issues Count: {repo.open_issues_count}
        
        Return a JSON object matching this schema:
        {{
          "maintainer_activity": integer (0-100),
          "release_frequency": integer (0-100),
          "open_issue_trends": "Improving" | "Stable" | "Degrading",
          "contribution_velocity": integer (0-100),
          "community_engagement": integer (0-100),
          "health_explanation": "Technical summary explanation of the health of the community and repository activity."
        }}
        Respond with ONLY the JSON object, no other text."""

        try:
            return await self._llm.complete_json(prompt=prompt, temperature=0.2)
        except Exception as exc:
            self.logger.warning("llm_repo_health_failed", error=str(exc))
            return {
                "maintainer_activity": 80,
                "release_frequency": 75,
                "open_issue_trends": "Stable",
                "contribution_velocity": 70,
                "community_engagement": 80,
                "health_explanation": "Default baseline health metrics applied due to processing timeout."
            }

    async def _analyze_single_opportunity(
        self,
        opp: dict,
        skills: list[str],
        technologies: list[str],
        interests: list[str],
        experience_level: str,
    ) -> dict:
        """Call LLM to get detailed fit, merge probability, health, and features."""
        issue = opp["issue"]
        repo = opp["repository"]

        user_profile = f"""Skills: {', '.join(skills)}
        Technologies: {', '.join(technologies)}
        Interests: {', '.join(interests)}
        Experience Level: {experience_level}"""

        repo_context = f"""Name: {repo['full_name']}
        Description: {repo['description']}
        Language: {repo['primary_language']}
        Stars: {repo['stars']} | Forks: {repo['forks']} | Open Issues: {repo['open_issues_count']}
        Topics: {', '.join(repo['topics'])}"""

        issue_context = f"""Title: {issue.title}
        Body: {issue.body or 'No description provided.'}
        Labels: {', '.join(issue.labels)}
        Comments Count: {issue.comments_count}
        Age: {issue.age_days} days"""

        prompt = f"""Evaluate this open source opportunity:
        
        USER PROFILE:
        {user_profile}
        
        REPOSITORY CONTEXT:
        {repo_context}
        
        ISSUE CONTEXT:
        {issue_context}
        
        Evaluate each required score and output a JSON response matching the schema.
        Respond with ONLY the JSON object."""

        return await self._llm.complete_json(
            prompt=prompt,
            system=_RADAR_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=800,
        )
