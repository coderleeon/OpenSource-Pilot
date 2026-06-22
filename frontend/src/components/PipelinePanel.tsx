"use client";

import React from "react";
import { Bookmark, Star, Trash2, ArrowRight, GitBranch } from "lucide-react";

interface SavedOpportunity {
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
}

interface PipelinePanelProps {
  savedOpportunities: SavedOpportunity[];
  onRemove: (opp: SavedOpportunity) => void;
  onAnalyzeRepo: (url: string) => void;
  onContribute: (url: string, issueNumber: number) => void;
}

export default function PipelinePanel({
  savedOpportunities,
  onRemove,
  onAnalyzeRepo,
  onContribute
}: PipelinePanelProps) {
  return (
    <div className="rounded-2xl glass-panel border border-white/10 p-6 shadow-xl h-full flex flex-col gap-5">
      <div className="flex items-center gap-2 border-b border-white/5 pb-3">
        <Bookmark className="w-5 h-5 text-indigo-400 fill-indigo-400/20" />
        <h3 className="font-bold text-white text-base">Opportunity Pipeline</h3>
        <span className="ml-auto bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-bold font-mono px-2 py-0.5 rounded-full">
          {savedOpportunities.length} Saved
        </span>
      </div>

      {savedOpportunities.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center gap-2">
          <Bookmark className="w-8 h-8 text-slate-700" />
          <p className="text-xs text-slate-500 max-w-[200px] leading-relaxed">
            Your pipeline is currently empty. Use the **Discover** tab to search and bookmark opportunities!
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-4 overflow-y-auto max-h-[500px] pr-1">
          {savedOpportunities.map((opp, idx) => {
            return (
              <div
                key={idx}
                className="bg-white/[0.01] hover:bg-white/[0.02] border border-white/5 hover:border-white/10 transition-all rounded-xl p-4 flex flex-col gap-3 group"
              >
                {/* Repo / Fit Header */}
                <div className="flex justify-between items-start gap-3">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-[10px] text-slate-500 font-mono inline-flex items-center gap-1">
                      <svg className="w-3 h-3 text-slate-500" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.167 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.164 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
                      </svg>
                      {opp.repository.full_name}
                    </span>
                    <h4 className="text-xs font-bold text-white leading-snug line-clamp-2 mt-1">
                      #{opp.issue.number}: {opp.issue.title}
                    </h4>
                  </div>
                  
                  {/* Fit Badge */}
                  <span className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-black font-mono px-2 py-0.5 rounded shrink-0">
                    {opp.fit_analysis.fit_score}% Fit
                  </span>
                </div>

                {/* Actions Row */}
                <div className="flex items-center justify-between border-t border-white/5 pt-2.5 mt-1">
                  {/* Left: Remove button */}
                  <button
                    onClick={() => onRemove(opp)}
                    className="p-1 text-slate-500 hover:text-rose-400 hover:bg-rose-500/5 rounded transition-all cursor-pointer"
                    title="Remove from pipeline"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>

                  {/* Right: navigation buttons */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => onAnalyzeRepo(opp.repository.url)}
                      className="px-2.5 py-1 text-[10px] font-semibold bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white rounded-lg border border-white/5 transition-all cursor-pointer"
                    >
                      Analyze Repo
                    </button>
                    
                    <button
                      onClick={() => onContribute(opp.repository.url, opp.issue.number)}
                      className="px-2.5 py-1 text-[10px] font-bold bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg flex items-center gap-1 transition-all active:scale-[0.98] shadow-md shadow-indigo-500/10 cursor-pointer"
                    >
                      <GitBranch className="w-3 h-3" />
                      Solve
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
