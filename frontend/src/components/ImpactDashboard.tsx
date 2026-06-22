"use client";

import React, { useEffect, useState } from "react";
import { Award, GitPullRequest, CheckCircle2, ShieldAlert, Sparkles, Plus, Minus } from "lucide-react";

interface ImpactStats {
  issuesSolved: number;
  prsSubmitted: number;
  prsMerged: number;
  reposContributed: number;
}

interface ImpactDashboardProps {
  stats: ImpactStats;
  onUpdateStats: (stats: ImpactStats) => void;
}

export default function ImpactDashboard({ stats, onUpdateStats }: ImpactDashboardProps) {
  // Impact Score calculation formula:
  // Merged PR = 25pts, Submitted PR = 10pts, Solved Issue = 5pts, Repos Contributed = 15pts
  const impactScore =
    stats.prsMerged * 25 +
    stats.prsSubmitted * 10 +
    stats.issuesSolved * 5 +
    stats.reposContributed * 15;

  const handleAdjust = (field: keyof ImpactStats, increment: boolean) => {
    const newStats = { ...stats };
    const val = newStats[field];
    newStats[field] = increment ? val + 1 : Math.max(0, val - 1);
    onUpdateStats(newStats);
  };

  const getRank = (score: number) => {
    if (score >= 200) return { title: "Elite Contributor", color: "text-amber-400 border-amber-500/30 bg-amber-500/10" };
    if (score >= 100) return { title: "Active Maintainer", color: "text-violet-400 border-violet-500/30 bg-violet-500/10" };
    if (score >= 40) return { title: "Rising Star", color: "text-indigo-400 border-indigo-500/30 bg-indigo-500/10" };
    return { title: "Novice Pilot", color: "text-slate-400 border-slate-500/20 bg-slate-500/5" };
  };

  const rank = getRank(impactScore);

  return (
    <div className="rounded-2xl glass-panel border border-white/10 p-6 shadow-xl flex flex-col gap-6">
      {/* Header Profile Title */}
      <div className="flex items-center gap-3 border-b border-white/5 pb-4">
        <div className="p-2.5 bg-gradient-to-tr from-indigo-500 to-violet-500 rounded-xl text-white">
          <Award className="w-5 h-5" />
        </div>
        <div className="flex flex-col">
          <h3 className="font-bold text-white text-base">Contributor Profile</h3>
          <span className={`text-[10px] font-bold rounded-lg border px-2 py-0.5 w-fit mt-1 ${rank.color}`}>
            {rank.title}
          </span>
        </div>
        
        {/* Impact Score Badge */}
        <div className="ml-auto flex flex-col items-end">
          <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">Impact Score</span>
          <span className="text-xl font-black text-indigo-400 font-mono leading-none mt-1">{impactScore}</span>
        </div>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-2 gap-3.5">
        {/* Issues Solved */}
        <div className="bg-white/[0.01] border border-white/5 rounded-xl p-3 flex flex-col gap-1.5 relative group">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Issues Solved</span>
          <div className="flex items-center justify-between">
            <span className="text-lg font-black text-white font-mono">{stats.issuesSolved}</span>
            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => handleAdjust("issuesSolved", false)}
                className="p-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 cursor-pointer"
              >
                <Minus className="w-3 h-3" />
              </button>
              <button
                onClick={() => handleAdjust("issuesSolved", true)}
                className="p-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 cursor-pointer"
              >
                <Plus className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>

        {/* PRs Submitted */}
        <div className="bg-white/[0.01] border border-white/5 rounded-xl p-3 flex flex-col gap-1.5 relative group">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">PRs Submitted</span>
          <div className="flex items-center justify-between">
            <span className="text-lg font-black text-white font-mono">{stats.prsSubmitted}</span>
            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => handleAdjust("prsSubmitted", false)}
                className="p-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 cursor-pointer"
              >
                <Minus className="w-3 h-3" />
              </button>
              <button
                onClick={() => handleAdjust("prsSubmitted", true)}
                className="p-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 cursor-pointer"
              >
                <Plus className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>

        {/* PRs Merged */}
        <div className="bg-white/[0.01] border border-white/5 rounded-xl p-3 flex flex-col gap-1.5 relative group">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">PRs Merged</span>
          <div className="flex items-center justify-between">
            <span className="text-lg font-black text-white font-mono">{stats.prsMerged}</span>
            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => handleAdjust("prsMerged", false)}
                className="p-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 cursor-pointer"
              >
                <Minus className="w-3 h-3" />
              </button>
              <button
                onClick={() => handleAdjust("prsMerged", true)}
                className="p-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 cursor-pointer"
              >
                <Plus className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>

        {/* Repos contributed */}
        <div className="bg-white/[0.01] border border-white/5 rounded-xl p-3 flex flex-col gap-1.5 relative group">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Repos Saved</span>
          <div className="flex items-center justify-between">
            <span className="text-lg font-black text-white font-mono">{stats.reposContributed}</span>
            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => handleAdjust("reposContributed", false)}
                className="p-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 cursor-pointer"
              >
                <Minus className="w-3 h-3" />
              </button>
              <button
                onClick={() => handleAdjust("reposContributed", true)}
                className="p-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 cursor-pointer"
              >
                <Plus className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Progress ring or motivational message */}
      <div className="bg-indigo-500/5 border border-indigo-500/10 p-3 rounded-xl flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-indigo-400 shrink-0" />
        <span className="text-[10px] text-slate-400 leading-snug">
          {impactScore === 0
            ? "Solve issues, draft pull requests, and contribute to repositories to level up!"
            : `Keep going! You're ${Math.max(0, 40 - impactScore)} points away from the next level.`}
        </span>
      </div>
    </div>
  );
}
