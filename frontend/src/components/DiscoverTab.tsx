"use client";

import React, { useState } from "react";
import {
  Search,
  Sparkles,
  GitBranch,
  Star,
  Activity,
  Flame,
  Zap,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  Bookmark,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  AlertCircle
} from "lucide-react";

interface Opportunity {
  repository: {
    name: string;
    full_name: string;
    description: string | null;
    url: string;
    stars: number;
    forks: number;
    open_issues_count: number;
    primary_language: string | null;
    topics: string[];
  };
  issue: {
    number: number;
    title: string;
    body: string | null;
    labels: string[];
    url: string;
    comments_count: number;
    author: string;
    created_at: string;
    age_days: number;
  };
  fit_analysis: {
    fit_score: number;
    difficulty: string;
    learning_value: string;
    reason: string;
  };
  merge_probability: {
    merge_probability: number;
    confidence: string;
    explanation: string;
  };
  repo_health: {
    maintainer_activity: number;
    release_frequency: number;
    open_issue_trends: string;
    contribution_velocity: number;
    community_engagement: number;
    health_explanation: string;
  };
  missing_features: Array<{
    feature_name: string;
    description: string;
    reasoning: string;
  }>;
}

interface DiscoverTabProps {
  onAnalyzeRepo: (url: string) => void;
  onContribute: (url: string, issueNumber: number) => void;
  onSaveOpportunity: (opp: Opportunity) => void;
  savedIds: string[];
}

export default function DiscoverTab({
  onAnalyzeRepo,
  onContribute,
  onSaveOpportunity,
  savedIds
}: DiscoverTabProps) {
  const [skills, setSkills] = useState("");
  const [technologies, setTechnologies] = useState("");
  const [interests, setInterests] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("beginner");
  const [isLoading, setIsLoading] = useState(false);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expandedIssueId, setExpandedIssueId] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setOpportunities([]);

    const backendBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const endpoint = `${backendBaseUrl}/api/v1/radar/discover`;

    const skillsArray = skills.split(",").map(s => s.trim()).filter(Boolean);
    const techArray = technologies.split(",").map(t => t.trim()).filter(Boolean);
    const interestsArray = interests.split(",").map(i => i.trim()).filter(Boolean);

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          skills: skillsArray,
          technologies: techArray,
          interests: interestsArray,
          experience_level: experienceLevel,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to search opportunities. Please verify backend is running.");
      }

      const data = await response.json();
      setOpportunities(data.opportunities || []);
      if (data.opportunities?.length === 0) {
        setError("No matching opportunities found. Try adjusting or broadening your search filters.");
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to establish a connection to the OpenSourcePilot backend.");
    } finally {
      setIsLoading(false);
    }
  };

  const getDifficultyColor = (diff: string) => {
    switch (diff.toLowerCase()) {
      case "easy":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "medium":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      case "hard":
        return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      default:
        return "bg-slate-500/10 text-slate-400 border-slate-500/20";
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend.toLowerCase()) {
      case "improving":
        return <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />;
      case "degrading":
        return <TrendingDown className="w-3.5 h-3.5 text-rose-400" />;
      default:
        return <Activity className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  return (
    <div className="flex flex-col gap-8">
      {/* Search Header Form */}
      <div className="rounded-2xl glass-panel border border-white/10 p-6 shadow-xl">
        <form onSubmit={handleSearch} className="flex flex-col gap-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Skills */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">Skills</label>
              <input
                type="text"
                placeholder="Python, C++, TypeScript..."
                value={skills}
                onChange={e => setSkills(e.target.value)}
                className="w-full bg-slate-950/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-600"
              />
            </div>
            {/* Technologies */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">Technologies</label>
              <input
                type="text"
                placeholder="FastAPI, React, Pytest..."
                value={technologies}
                onChange={e => setTechnologies(e.target.value)}
                className="w-full bg-slate-950/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-600"
              />
            </div>
            {/* Interests */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">Interests</label>
              <input
                type="text"
                placeholder="LLMs, Vector Databases, UI..."
                value={interests}
                onChange={e => setInterests(e.target.value)}
                className="w-full bg-slate-950/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-600"
              />
            </div>
            {/* Experience Level */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">Experience Level</label>
              <select
                value={experienceLevel}
                onChange={e => setExperienceLevel(e.target.value)}
                className="w-full bg-slate-950 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
              >
                <option value="beginner">Beginner (Good First Issues)</option>
                <option value="intermediate">Intermediate (Help Wanted)</option>
                <option value="advanced">Advanced (All Issues)</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full md:w-fit px-8 py-3 bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 rounded-xl text-sm font-bold text-white shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Search className="w-4 h-4 animate-spin" />
                Scanning Repositories...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Scan Open Source Radar
              </>
            )}
          </button>
        </form>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <div className="relative w-16 h-16 flex items-center justify-center">
            <div className="absolute inset-0 border-4 border-indigo-500/20 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-t-indigo-400 rounded-full animate-spin"></div>
            <Zap className="w-6 h-6 text-indigo-400 animate-pulse" />
          </div>
          <div className="text-center">
            <h3 className="text-lg font-bold text-white">Scanning GitHub Universe</h3>
            <p className="text-sm text-slate-500 mt-1 max-w-sm">Retrieving issue queues, calculating community activity, and analyzing developer suitability...</p>
          </div>
        </div>
      )}

      {/* Error / Fallback message */}
      {error && (
        <div className="max-w-2xl mx-auto rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6 text-center flex flex-col items-center gap-3">
          <AlertCircle className="w-8 h-8 text-amber-400" />
          <div>
            <h3 className="text-md font-bold text-white">Discovery Query Information</h3>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {/* Results grid */}
      {opportunities.length > 0 && (
        <div className="flex flex-col gap-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-white">Recommended Opportunities ({opportunities.length})</h2>
            <span className="text-xs text-slate-500">Sorted by dynamic community fit score</span>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {opportunities.map((opp, idx) => {
              const uniqueId = `${opp.repository.full_name}#${opp.issue.number}`;
              const isSaved = savedIds.includes(uniqueId);
              const isExpanded = expandedIssueId === uniqueId;

              return (
                <div
                  key={idx}
                  className="rounded-2xl glass-panel border border-white/5 hover:border-white/10 transition-all flex flex-col overflow-hidden shadow-lg"
                >
                  {/* Top Header Section */}
                  <div className="p-6 border-b border-white/5 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                    {/* Title / Repo */}
                    <div className="flex flex-col gap-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="p-1 bg-white/5 rounded-md text-slate-300">
                          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.167 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.164 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
                          </svg>
                        </span>
                        <a
                          href={opp.repository.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-semibold text-indigo-400 hover:underline inline-flex items-center gap-1 text-sm"
                        >
                          {opp.repository.full_name}
                          <ExternalLink className="w-3.5 h-3.5 opacity-60" />
                        </a>
                        {opp.repository.primary_language && (
                          <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 text-[10px] font-bold border border-indigo-500/20">
                            {opp.repository.primary_language}
                          </span>
                        )}
                      </div>

                      <h3 className="text-lg font-bold text-white mt-1">
                        <a
                          href={opp.issue.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:text-indigo-300"
                        >
                          #{opp.issue.number}: {opp.issue.title}
                        </a>
                      </h3>

                      <div className="flex flex-wrap items-center gap-2 mt-1">
                        <span className="text-xs text-slate-400">Created by @{opp.issue.author}</span>
                        <span className="text-slate-700">&bull;</span>
                        <span className="text-xs text-slate-400">{opp.issue.age_days} days old</span>
                        <span className="text-slate-700">&bull;</span>
                        <span className="text-xs text-slate-400">{opp.issue.comments_count} comments</span>
                      </div>
                    </div>

                    {/* Fit & Merge Summary Badges */}
                    <div className="flex flex-wrap gap-4 items-center shrink-0">
                      {/* Fit Score Radial SVG */}
                      <div className="flex items-center gap-3 bg-white/[0.02] border border-white/5 p-3 rounded-xl">
                        <div className="relative w-11 h-11 flex items-center justify-center">
                          <svg className="w-11 h-11 transform -rotate-90">
                            <circle
                              cx="22"
                              cy="22"
                              r="18"
                              className="stroke-slate-800"
                              strokeWidth="3.5"
                              fill="transparent"
                            />
                            <circle
                              cx="22"
                              cy="22"
                              r="18"
                              className="stroke-indigo-400"
                              strokeWidth="3.5"
                              fill="transparent"
                              strokeDasharray={2 * Math.PI * 18}
                              strokeDashoffset={2 * Math.PI * 18 * (1 - opp.fit_analysis.fit_score / 100)}
                            />
                          </svg>
                          <div className="absolute inset-0 flex items-center justify-center text-[11px] font-black text-white font-mono">
                            {opp.fit_analysis.fit_score}%
                          </div>
                        </div>
                        <div className="flex flex-col">
                          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">Fit Score</span>
                          <span className={`text-[10px] font-bold rounded px-1.5 py-0.5 border mt-0.5 ${getDifficultyColor(opp.fit_analysis.difficulty)}`}>
                            {opp.fit_analysis.difficulty}
                          </span>
                        </div>
                      </div>

                      {/* Merge Probability */}
                      <div className="flex items-center gap-3 bg-white/[0.02] border border-white/5 p-3 rounded-xl">
                        <div className="flex flex-col text-right">
                          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">Merge Prob.</span>
                          <span className="text-sm font-black text-emerald-400 font-mono mt-0.5">{opp.merge_probability.merge_probability}%</span>
                        </div>
                        <span className="px-2 py-1 text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded">
                          {opp.merge_probability.confidence} Confidence
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Body Content / Visualizers */}
                  <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6 bg-slate-950/20">
                    {/* Fit & Merge explanation */}
                    <div className="flex flex-col gap-4">
                      <div>
                        <h4 className="text-xs font-semibold text-indigo-300 uppercase tracking-widest mb-1.5">Fit Explanation</h4>
                        <p className="text-xs text-slate-300 leading-relaxed bg-white/[0.01] border border-white/5 p-3 rounded-xl">
                          {opp.fit_analysis.reason}
                        </p>
                      </div>
                      <div>
                        <h4 className="text-xs font-semibold text-emerald-300 uppercase tracking-widest mb-1.5">Acceptance Factors</h4>
                        <p className="text-xs text-slate-300 leading-relaxed bg-white/[0.01] border border-white/5 p-3 rounded-xl">
                          {opp.merge_probability.explanation}
                        </p>
                      </div>
                    </div>

                    {/* Repository Health Grid */}
                    <div className="flex flex-col gap-3">
                      <h4 className="text-xs font-semibold text-indigo-300 uppercase tracking-widest">Community Health</h4>
                      <div className="grid grid-cols-2 gap-2">
                        {/* Maintainer Activity */}
                        <div className="bg-white/[0.02] border border-white/5 p-2.5 rounded-xl">
                          <span className="text-[10px] text-slate-500 block">Maintainer Activity</span>
                          <div className="flex items-center gap-1.5 mt-1">
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div
                                className="bg-indigo-400 h-full rounded-full"
                                style={{ width: `${opp.repo_health.maintainer_activity}%` }}
                              ></div>
                            </div>
                            <span className="text-xs font-mono text-white font-bold">{opp.repo_health.maintainer_activity}%</span>
                          </div>
                        </div>

                        {/* Release Frequency */}
                        <div className="bg-white/[0.02] border border-white/5 p-2.5 rounded-xl">
                          <span className="text-[10px] text-slate-500 block">Release Cadence</span>
                          <div className="flex items-center gap-1.5 mt-1">
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div
                                className="bg-indigo-400 h-full rounded-full"
                                style={{ width: `${opp.repo_health.release_frequency}%` }}
                              ></div>
                            </div>
                            <span className="text-xs font-mono text-white font-bold">{opp.repo_health.release_frequency}%</span>
                          </div>
                        </div>

                        {/* Contribution Velocity */}
                        <div className="bg-white/[0.02] border border-white/5 p-2.5 rounded-xl">
                          <span className="text-[10px] text-slate-500 block">Review Speed</span>
                          <div className="flex items-center gap-1.5 mt-1">
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div
                                className="bg-indigo-400 h-full rounded-full"
                                style={{ width: `${opp.repo_health.contribution_velocity}%` }}
                              ></div>
                            </div>
                            <span className="text-xs font-mono text-white font-bold">{opp.repo_health.contribution_velocity}%</span>
                          </div>
                        </div>

                        {/* Community Engagement */}
                        <div className="bg-white/[0.02] border border-white/5 p-2.5 rounded-xl">
                          <span className="text-[10px] text-slate-500 block">Engagement</span>
                          <div className="flex items-center gap-1.5 mt-1">
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div
                                className="bg-indigo-400 h-full rounded-full"
                                style={{ width: `${opp.repo_health.community_engagement}%` }}
                              ></div>
                            </div>
                            <span className="text-xs font-mono text-white font-bold">{opp.repo_health.community_engagement}%</span>
                          </div>
                        </div>
                      </div>

                      <div className="bg-indigo-500/5 border border-indigo-500/10 p-2.5 rounded-xl text-[11px] text-slate-400 leading-relaxed flex items-start gap-1.5 mt-1">
                        {getTrendIcon(opp.repo_health.open_issue_trends)}
                        <span>
                          <strong>Trend: {opp.repo_health.open_issue_trends}.</strong> {opp.repo_health.health_explanation}
                        </span>
                      </div>
                    </div>

                    {/* Missing Feature Suggestions */}
                    <div className="flex flex-col gap-2">
                      <h4 className="text-xs font-semibold text-indigo-300 uppercase tracking-widest">Radar feature suggestions</h4>
                      {opp.missing_features && opp.missing_features.length > 0 ? (
                        <div className="flex flex-col gap-2 max-h-[190px] overflow-y-auto pr-1">
                          {opp.missing_features.slice(0, 3).map((feat, fidx) => (
                            <div key={fidx} className="bg-white/[0.02] border border-white/5 p-2.5 rounded-xl group hover:bg-white/[0.04] transition-colors">
                              <span className="text-xs font-bold text-indigo-300 group-hover:text-indigo-200 block">{feat.feature_name}</span>
                              <span className="text-[10px] text-slate-400 leading-relaxed block mt-0.5">{feat.description}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <span className="text-xs text-slate-500 italic">No missing capabilities indexed.</span>
                      )}
                    </div>
                  </div>

                  {/* Expandable Issue Description and Action Bottom bar */}
                  <div className="p-4 bg-slate-950/40 border-t border-white/5 flex flex-col md:flex-row justify-between items-stretch md:items-center gap-4">
                    {/* Expand Issue Toggle */}
                    <button
                      onClick={() => setExpandedIssueId(isExpanded ? null : uniqueId)}
                      className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 self-start cursor-pointer hover:bg-white/5 rounded-lg"
                    >
                      {isExpanded ? (
                        <>
                          <ChevronUp className="w-4 h-4" />
                          Hide Issue Description
                        </>
                      ) : (
                        <>
                          <ChevronDown className="w-4 h-4" />
                          View Issue Description
                        </>
                      )}
                    </button>

                    {/* Actions button group */}
                    <div className="flex flex-wrap items-center gap-2 self-end md:self-auto">
                      <button
                        onClick={() => onSaveOpportunity(opp)}
                        className={`px-3 py-2 text-xs font-semibold rounded-xl border flex items-center gap-1.5 transition-all cursor-pointer ${
                          isSaved
                            ? "bg-indigo-500/20 border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/10"
                            : "bg-white/5 border-white/5 text-slate-300 hover:bg-white/10 hover:text-white"
                        }`}
                      >
                        <Bookmark className={`w-3.5 h-3.5 ${isSaved ? "fill-indigo-400 text-indigo-400" : ""}`} />
                        {isSaved ? "Saved" : "Save Opportunity"}
                      </button>

                      <button
                        onClick={() => onAnalyzeRepo(opp.repository.url)}
                        className="px-3 py-2 text-xs font-semibold bg-white/5 hover:bg-white/10 border border-white/5 text-slate-300 hover:text-white rounded-xl transition-all cursor-pointer"
                      >
                        Analyze Repo
                      </button>

                      <button
                        onClick={() => onContribute(opp.repository.url, opp.issue.number)}
                        className="px-4 py-2 text-xs font-bold bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl flex items-center gap-1.5 transition-all active:scale-[0.98] shadow-lg shadow-indigo-500/10 cursor-pointer"
                      >
                        <GitBranch className="w-3.5 h-3.5" />
                        Solve with Pilot
                      </button>
                    </div>
                  </div>

                  {/* Expanded Issue description panel */}
                  {isExpanded && (
                    <div className="p-6 bg-slate-950/60 border-t border-white/5">
                      <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">Issue Body</h4>
                      <div className="bg-slate-950/80 p-4 rounded-xl border border-white/5 max-h-[300px] overflow-y-auto">
                        <pre className="text-xs text-slate-300 font-sans whitespace-pre-wrap leading-relaxed">
                          {opp.issue.body || "No description body provided."}
                        </pre>
                      </div>
                      {opp.issue.labels && opp.issue.labels.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-3">
                          {opp.issue.labels.map((lbl, lidx) => (
                            <span
                              key={lidx}
                              className="px-2 py-0.5 rounded-md bg-white/5 border border-white/5 text-[10px] text-slate-400 font-medium"
                            >
                              {lbl}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
