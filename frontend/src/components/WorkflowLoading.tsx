"use client";

import React, { useEffect, useState } from "react";
import { Activity, Clock } from "lucide-react";

export default function WorkflowLoading() {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      setElapsed((Date.now() - startTime) / 1000);
    }, 100);

    return () => clearInterval(interval);
  }, []);

  const stages = [
    { title: "Initializing Sandbox", desc: "Cloning GitHub repo and resolving default branch." },
    { title: "Codebase Vector Indexing", desc: "Chunking source files and embedding them with all-MiniLM-L6-v2 in ChromaDB." },
    { title: "Issue Analysis & Classification", desc: "Retrieving issue parameters, classifying difficulty, and scoring beginner-friendliness." },
    { title: "Semantic Code Discovery", desc: "Retrieving relevant modules and locating candidates via similarity distance." },
    { title: "Contribution Synthesis", desc: "Drafting the implementation steps, writing test suites, and creating the pull request draft." },
  ];

  return (
    <div className="w-full max-w-2xl mx-auto rounded-2xl glass-panel p-8 border border-white/10 shadow-2xl flex flex-col items-center text-center transition-all duration-300">
      
      {/* Spinning Outer Ring & Glowing Center */}
      <div className="relative w-24 h-24 mb-6">
        <div className="absolute inset-0 rounded-full border-4 border-white/5 border-t-indigo-500 animate-spin" />
        <div className="absolute inset-2 rounded-full border-4 border-white/5 border-b-violet-500 animate-spin duration-1000" />
        <div className="absolute inset-0 flex items-center justify-center">
          <Activity className="w-8 h-8 text-indigo-400 animate-pulse" />
        </div>
      </div>

      {/* Title */}
      <h3 className="text-xl font-bold text-white mb-2 tracking-tight">
        Executing Agentic Contributor Pipeline
      </h3>
      <p className="text-sm text-slate-400 max-w-md mb-6 leading-relaxed">
        We are building your vector workspace and planning resolutions. This typically takes 15–45 seconds depending on codebase size and issue complexity.
      </p>

      {/* Elapsed Timer */}
      <div className="flex items-center gap-2 px-4 py-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full text-indigo-300 font-mono text-sm font-semibold mb-8">
        <Clock className="w-4 h-4" />
        <span>Elapsed Time: {elapsed.toFixed(1)}s</span>
      </div>

      {/* Pipeline Progress Stages */}
      <div className="w-full text-left space-y-4">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 text-center">
          Workflow Stages
        </h4>
        <div className="space-y-3 max-w-lg mx-auto">
          {stages.map((stage, idx) => {
            // Determine active/pending stages roughly by elapsed time to make it feel alive without being fake.
            // This is just a visual guide of where it typically is.
            const isActive = elapsed >= idx * 7 && elapsed < (idx + 1) * 7;
            const isCompleted = elapsed >= (idx + 1) * 7;

            return (
              <div
                key={idx}
                className={`flex gap-3 items-start p-3 rounded-xl border transition-all duration-300 ${
                  isActive
                    ? "bg-indigo-500/5 border-indigo-500/30 text-white"
                    : isCompleted
                    ? "bg-emerald-500/5 border-emerald-500/20 text-slate-300 opacity-80"
                    : "bg-transparent border-transparent text-slate-500"
                }`}
              >
                {/* Visual indicator */}
                <div className="mt-1 flex items-center justify-center shrink-0">
                  {isCompleted ? (
                    <div className="w-3.5 h-3.5 rounded-full bg-emerald-500/20 border border-emerald-500 flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    </div>
                  ) : isActive ? (
                    <div className="w-3.5 h-3.5 rounded-full bg-indigo-500/20 border border-indigo-500 flex items-center justify-center animate-pulse">
                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                    </div>
                  ) : (
                    <div className="w-3.5 h-3.5 rounded-full bg-slate-800 border border-slate-700" />
                  )}
                </div>
                <div>
                  <h5 className="text-xs font-semibold uppercase tracking-wider">{stage.title}</h5>
                  <p className="text-xs text-slate-400 mt-0.5">{stage.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
    </div>
  );
}
