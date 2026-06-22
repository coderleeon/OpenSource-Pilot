"use client";

import React, { useState } from "react";
import { Play, Sparkles, HelpCircle, AlertCircle } from "lucide-react";

interface WorkflowFormProps {
  onSubmit: (repoUrl: string, issueNumber: number) => void;
  isLoading: boolean;
  initialRepoUrl?: string;
  initialIssueNumber?: string;
}

export default function WorkflowForm({
  onSubmit,
  isLoading,
  initialRepoUrl = "",
  initialIssueNumber = ""
}: WorkflowFormProps) {
  const [repoUrl, setRepoUrl] = useState(initialRepoUrl);
  const [issueNumber, setIssueNumber] = useState(initialIssueNumber);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    if (initialRepoUrl) {
      setRepoUrl(initialRepoUrl);
    }
    if (initialIssueNumber) {
      setIssueNumber(initialIssueNumber);
    }
  }, [initialRepoUrl, initialIssueNumber]);

  const presets = [
    {
      label: "Flask Bug #5420",
      repo: "https://github.com/pallets/flask",
      issue: 5420,
      description: "Bug report on Pallets Flask",
    },
    {
      label: "Requests Feature #6000",
      repo: "https://github.com/psf/requests",
      issue: 6000,
      description: "Feature request on PSF Requests",
    },
    {
      label: "Pytest Edge Case #11000",
      repo: "https://github.com/pytest-dev/pytest",
      issue: 11000,
      description: "Testing edge case in Pytest framework",
    },
  ];

  const handlePresetClick = (repo: string, issue: number) => {
    if (isLoading) return;
    setRepoUrl(repo);
    setIssueNumber(issue.toString());
    setError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!repoUrl.trim()) {
      setError("Please provide a GitHub repository URL.");
      return;
    }

    if (!repoUrl.toLowerCase().includes("github.com")) {
      setError("Only GitHub repositories are supported.");
      return;
    }

    const parsedIssueNum = parseInt(issueNumber, 10);
    if (isNaN(parsedIssueNum) || parsedIssueNum <= 0) {
      setError("Please provide a valid, positive GitHub issue number.");
      return;
    }

    onSubmit(repoUrl.trim().replace(/\/$/, ""), parsedIssueNum);
  };

  return (
    <div className="w-full rounded-2xl glass-panel p-6 border border-white/10 shadow-xl transition-all duration-300">
      <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-indigo-400" />
        Start Contributor Workflow
      </h2>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          
          {/* Repository URL Input */}
          <div className="md:col-span-3 flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              GitHub Repository URL
            </label>
            <input
              type="text"
              placeholder="e.g. https://github.com/pallets/flask"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              disabled={isLoading}
              className="px-4 py-3 bg-slate-950/60 border border-white/10 focus:border-indigo-500 rounded-xl text-slate-100 placeholder-slate-500 text-sm outline-none transition-all duration-200 focus:ring-1 focus:ring-indigo-500/30 disabled:opacity-50"
            />
          </div>

          {/* Issue Number Input */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Issue Number
            </label>
            <input
              type="number"
              min="1"
              placeholder="e.g. 5420"
              value={issueNumber}
              onChange={(e) => setIssueNumber(e.target.value)}
              disabled={isLoading}
              className="px-4 py-3 bg-slate-950/60 border border-white/10 focus:border-indigo-500 rounded-xl text-slate-100 placeholder-slate-500 text-sm outline-none transition-all duration-200 focus:ring-1 focus:ring-indigo-500/30 disabled:opacity-50 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
            />
          </div>

        </div>

        {/* Validation Errors */}
        {error && (
          <div className="flex items-center gap-2 text-sm text-rose-400 bg-rose-500/5 border border-rose-500/20 p-3 rounded-xl">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form Action Buttons */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 pt-2">
          
          {/* Presets Grid */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-slate-400">Quick Presets:</span>
            {presets.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handlePresetClick(preset.repo, preset.issue)}
                disabled={isLoading}
                className="px-3 py-1.5 text-xs font-medium bg-white/5 hover:bg-white/10 border border-white/5 rounded-lg text-slate-300 hover:text-white transition-all duration-150 active:scale-[0.98] disabled:opacity-40 shrink-0"
                title={preset.description}
              >
                {preset.label}
              </button>
            ))}
          </div>

          {/* Submit Action */}
          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:from-indigo-800 disabled:to-violet-800 text-white font-medium rounded-xl text-sm flex items-center justify-center gap-2 transition-all duration-200 shadow-lg hover:shadow-indigo-500/10 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed shrink-0"
          >
            {isLoading ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Processing...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                Analyze & Generate
              </>
            )}
          </button>
          
        </div>
      </form>
    </div>
  );
}
