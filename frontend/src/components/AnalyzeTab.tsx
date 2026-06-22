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
  Folder,
  File,
  ChevronRight,
  HelpCircle,
  Shield,
  TrendingUp,
  TrendingDown,
  ExternalLink,
  BookOpen,
  Boxes,
  Terminal,
  RefreshCw,
  Heart
} from "lucide-react";

interface AnalyzeTabProps {
  onStartContribution: (url: string) => void;
  initialUrl?: string;
}

export default function AnalyzeTab({ onStartContribution, initialUrl = "" }: AnalyzeTabProps) {
  const [repoUrl, setRepoUrl] = useState(initialUrl);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [repoData, setRepoData] = useState<any>(null);
  const [healthData, setHealthData] = useState<any>(null);
  const [missingFeatures, setMissingFeatures] = useState<any[]>([]);

  const handleAnalyze = async (e?: React.FormEvent, urlOverride?: string) => {
    if (e) e.preventDefault();
    const targetUrl = urlOverride || repoUrl;
    if (!targetUrl) return;

    setIsLoading(true);
    setError(null);
    setRepoData(null);
    setHealthData(null);
    setMissingFeatures([]);

    const backendBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      // 1. Fetch Repository General Analysis
      const repoRes = await fetch(`${backendBaseUrl}/api/v1/repo/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: targetUrl, index_code: false }),
      });

      if (!repoRes.ok) {
        throw new Error("Failed to analyze repository. Verify the URL is correct.");
      }

      const repoJson = await repoRes.json();
      setRepoData(repoJson);

      // 2. Fetch Health and Features in Parallel
      const [healthRes, featuresRes] = await Promise.all([
        fetch(`${backendBaseUrl}/api/v1/radar/repo-health`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ repo_url: targetUrl }),
        }).then(r => (r.ok ? r.json() : null)).catch(() => null),
        
        fetch(`${backendBaseUrl}/api/v1/radar/missing-features`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ repo_url: targetUrl }),
        }).then(r => (r.ok ? r.json() : null)).catch(() => null),
      ]);

      if (healthRes) setHealthData(healthRes.repo_health);
      if (featuresRes) setMissingFeatures(featuresRes.missing_features || []);

    } catch (err: any) {
      console.error(err);
      setError(err.message || "An error occurred during repository analysis.");
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    if (initialUrl) {
      setRepoUrl(initialUrl);
      handleAnalyze(undefined, initialUrl);
    }
  }, [initialUrl]);

  // Recursively render folder structure node tree
  const renderFileNode = (node: any, depth = 0) => {
    if (!node) return null;
    return (
      <div key={node.path} style={{ paddingLeft: `${depth * 14}px` }} className="flex flex-col gap-1">
        <div className="flex items-center gap-1.5 py-1 text-slate-300 hover:text-white transition-colors select-none text-xs">
          {node.is_dir ? (
            <Folder className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
          ) : (
            <File className="w-3.5 h-3.5 text-slate-500 shrink-0" />
          )}
          <span className="font-mono">{node.name}</span>
          {node.truncated && (
            <span className="text-[9px] text-slate-600 font-semibold uppercase tracking-wider">(truncated)</span>
          )}
        </div>
        {node.children && node.children.map((child: any) => renderFileNode(child, depth + 1))}
      </div>
    );
  };

  const getTrendIcon = (trend: string) => {
    switch (trend?.toLowerCase()) {
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
      {/* Analyze Search Bar */}
      <div className="rounded-2xl glass-panel border border-white/10 p-6 shadow-xl">
        <form onSubmit={handleAnalyze} className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1 flex flex-col gap-1.5 w-full">
            <label className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">GitHub Repository URL</label>
            <input
              type="text"
              placeholder="e.g. https://github.com/pallets/flask"
              value={repoUrl}
              onChange={e => setRepoUrl(e.target.value)}
              className="w-full bg-slate-950/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-600"
              required
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full md:w-fit px-8 py-3 bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 rounded-xl text-sm font-bold text-white shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Analyzing Repository...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Analyze Repository
              </>
            )}
          </button>
        </form>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <div className="relative w-16 h-16 flex items-center justify-center">
            <div className="absolute inset-0 border-4 border-indigo-500/20 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-t-indigo-400 rounded-full animate-spin"></div>
            <Terminal className="w-6 h-6 text-indigo-400 animate-pulse" />
          </div>
          <div className="text-center">
            <h3 className="text-lg font-bold text-white">Exploring Code Architecture</h3>
            <p className="text-sm text-slate-500 mt-1 max-w-sm">Cloning workspace modules, evaluating readme dependencies, and generating tech layouts...</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="max-w-2xl mx-auto rounded-2xl border border-rose-500/20 bg-rose-500/5 p-6 text-center flex flex-col items-center gap-3">
          <HelpCircle className="w-8 h-8 text-rose-400" />
          <div>
            <h3 className="text-md font-bold text-white">Analysis Failed</h3>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {/* Dashboard display */}
      {repoData && (
        <div className="flex flex-col gap-6 animate-fade-in">
          {/* Header metadata summary */}
          <div className="rounded-2xl glass-panel border border-white/10 p-6 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center gap-2">
                <span className="p-1 bg-white/5 rounded-md text-slate-300">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.167 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.164 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
                  </svg>
                </span>
                <span className="text-sm font-semibold text-slate-400 font-mono">{repoData.full_name}</span>
              </div>
              <h2 className="text-2xl font-bold text-white tracking-tight">{repoData.repo_name}</h2>
              <p className="text-sm text-slate-400 max-w-2xl leading-relaxed mt-1">{repoData.description}</p>

              <div className="flex flex-wrap gap-2.5 mt-2">
                <div className="flex items-center gap-1 text-xs text-slate-400 bg-white/5 border border-white/5 px-2 py-0.5 rounded-lg">
                  <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                  <span>{repoData.stars.toLocaleString()} Stars</span>
                </div>
                <div className="flex items-center gap-1 text-xs text-slate-400 bg-white/5 border border-white/5 px-2 py-0.5 rounded-lg">
                  <GitBranch className="w-3.5 h-3.5 text-slate-400" />
                  <span>{repoData.forks.toLocaleString()} Forks</span>
                </div>
                <div className="flex items-center gap-1 text-xs text-slate-400 bg-white/5 border border-white/5 px-2 py-0.5 rounded-lg">
                  <Activity className="w-3.5 h-3.5 text-indigo-400" />
                  <span>{repoData.open_issues_count} Open Issues</span>
                </div>
                {repoData.license_name && (
                  <div className="flex items-center gap-1 text-xs text-slate-400 bg-white/5 border border-white/5 px-2 py-0.5 rounded-lg font-mono">
                    <Shield className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{repoData.license_name}</span>
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={() => onStartContribution(repoData.url)}
              className="px-6 py-3 bg-indigo-500 hover:bg-indigo-600 text-white font-bold rounded-xl text-sm shadow-lg shadow-indigo-500/10 transition-all cursor-pointer shrink-0 self-stretch lg:self-auto text-center"
            >
              Solve Issue in Repo
            </button>
          </div>

          {/* Grid Layout: Main Columns */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left/Middle Column (Colspan 2): Summaries & Architecture */}
            <div className="lg:col-span-2 flex flex-col gap-6">
              {/* Project Summaries */}
              <div className="rounded-xl glass-panel p-5 border border-white/5 flex flex-col gap-4">
                <div className="flex items-center gap-2 text-indigo-300 font-semibold border-b border-white/5 pb-2.5">
                  <BookOpen className="w-4 h-4" />
                  <h3 className="text-sm font-semibold uppercase tracking-wider">Project Summary</h3>
                </div>
                <div className="flex flex-col gap-4">
                  <div>
                    <h4 className="text-xs text-slate-500 font-bold mb-1">README Overview</h4>
                    <p className="text-sm text-slate-300 leading-relaxed">{repoData.readme_summary}</p>
                  </div>
                  <div>
                    <h4 className="text-xs text-slate-500 font-bold mb-1">Contributing Guide Summary</h4>
                    <p className="text-sm text-slate-300 leading-relaxed">{repoData.contribution_guide_summary}</p>
                  </div>
                </div>
              </div>

              {/* Architecture Summary */}
              <div className="rounded-xl glass-panel p-5 border border-white/5 flex flex-col gap-4">
                <div className="flex items-center gap-2 text-indigo-300 font-semibold border-b border-white/5 pb-2.5">
                  <Boxes className="w-4 h-4" />
                  <h3 className="text-sm font-semibold uppercase tracking-wider">Software Architecture</h3>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed bg-slate-950/20 p-4 rounded-xl border border-white/5 font-mono">
                  {repoData.architecture_summary}
                </p>
              </div>

              {/* Missing Features suggestions */}
              {missingFeatures.length > 0 && (
                <div className="rounded-xl glass-panel p-5 border border-white/5 flex flex-col gap-4">
                  <div className="flex items-center gap-2 text-indigo-300 font-semibold border-b border-white/5 pb-2.5">
                    <Sparkles className="w-4 h-4 text-indigo-400" />
                    <h3 className="text-sm font-semibold uppercase tracking-wider">Radar Missing Feature Detection</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {missingFeatures.map((feat, idx) => (
                      <div
                        key={idx}
                        className="bg-white/[0.01] hover:bg-white/[0.02] border border-white/5 rounded-xl p-4 transition-all"
                      >
                        <h4 className="text-sm font-bold text-white">{feat.feature_name}</h4>
                        <p className="text-xs text-slate-400 leading-relaxed mt-1">{feat.description}</p>
                        <div className="mt-2 pt-2 border-t border-white/5 text-[10px] text-slate-500 leading-relaxed">
                          <strong>Rationale:</strong> {feat.reasoning}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right Column: Health, Structure & Tech Stack */}
            <div className="flex flex-col gap-6">
              {/* Community Health insights */}
              {healthData && (
                <div className="rounded-xl glass-panel p-5 border border-white/5 flex flex-col gap-4">
                  <div className="flex items-center gap-2 text-indigo-300 font-semibold border-b border-white/5 pb-2.5">
                    <Heart className="w-4 h-4 text-rose-400" />
                    <h3 className="text-sm font-semibold uppercase tracking-wider">Repo Health Insights</h3>
                  </div>

                  <div className="flex flex-col gap-3">
                    {/* Maintainer Activity */}
                    <div className="bg-white/[0.02] border border-white/5 p-2.5 rounded-xl">
                      <span className="text-[10px] text-slate-500 block">Maintainer Engagement</span>
                      <div className="flex items-center gap-1.5 mt-1">
                        <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div className="bg-indigo-400 h-full rounded-full" style={{ width: `${healthData.maintainer_activity}%` }}></div>
                        </div>
                        <span className="text-xs font-mono text-white font-bold">{healthData.maintainer_activity}%</span>
                      </div>
                    </div>

                    {/* Release Frequency */}
                    <div className="bg-white/[0.02] border border-white/5 p-2.5 rounded-xl">
                      <span className="text-[10px] text-slate-500 block">Release Frequency</span>
                      <div className="flex items-center gap-1.5 mt-1">
                        <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div className="bg-indigo-400 h-full rounded-full" style={{ width: `${healthData.release_frequency}%` }}></div>
                        </div>
                        <span className="text-xs font-mono text-white font-bold">{healthData.release_frequency}%</span>
                      </div>
                    </div>

                    {/* Contribution Velocity */}
                    <div className="bg-white/[0.02] border border-white/5 p-2.5 rounded-xl">
                      <span className="text-[10px] text-slate-500 block">Review Speed (Velocity)</span>
                      <div className="flex items-center gap-1.5 mt-1">
                        <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div className="bg-indigo-400 h-full rounded-full" style={{ width: `${healthData.contribution_velocity}%` }}></div>
                        </div>
                        <span className="text-xs font-mono text-white font-bold">{healthData.contribution_velocity}%</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-indigo-500/5 border border-indigo-500/10 p-3 rounded-xl text-xs text-slate-400 leading-relaxed flex items-start gap-1.5">
                    {getTrendIcon(healthData.open_issue_trends)}
                    <span>
                      <strong>Trend: {healthData.open_issue_trends}.</strong> {healthData.health_explanation}
                    </span>
                  </div>
                </div>
              )}

              {/* Tech Stack */}
              <div className="rounded-xl glass-panel p-5 border border-white/5 flex flex-col gap-3">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300">Technology Stack</h3>
                <div className="flex flex-col gap-2">
                  <div>
                    <span className="text-[10px] text-slate-500 block font-bold">Languages</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {repoData.tech_stack.languages.map((l: string, idx: number) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-white/5 text-xs text-slate-300">{l}</span>
                      ))}
                    </div>
                  </div>
                  {repoData.tech_stack.frameworks.length > 0 && (
                    <div>
                      <span className="text-[10px] text-slate-500 block font-bold">Frameworks</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {repoData.tech_stack.frameworks.map((f: string, idx: number) => (
                          <span key={idx} className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs">{f}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {repoData.tech_stack.tools.length > 0 && (
                    <div>
                      <span className="text-[10px] text-slate-500 block font-bold">Tools</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {repoData.tech_stack.tools.map((t: string, idx: number) => (
                          <span key={idx} className="px-2 py-0.5 rounded bg-white/5 text-xs text-slate-300">{t}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Directory Structure Slim Tree */}
              <div className="rounded-xl glass-panel p-5 border border-white/5 flex flex-col gap-3">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300">File Tree Structure</h3>
                <div className="bg-slate-950/45 p-4 rounded-xl border border-white/5 max-h-[350px] overflow-y-auto overflow-x-auto">
                  {renderFileNode(repoData.directory_structure)}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
