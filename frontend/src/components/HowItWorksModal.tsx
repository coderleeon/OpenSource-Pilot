"use client";

import React, { useEffect } from "react";
import { X, GitBranch, Search, Cpu, Database, FileText } from "lucide-react";

interface HowItWorksModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function HowItWorksModal({ isOpen, onClose }: HowItWorksModalProps) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleEscape);
    }
    return () => {
      document.body.style.overflow = "unset";
      window.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const steps = [
    {
      icon: GitBranch,
      title: "1. Repo Cloning & Setup",
      description: "Clones the target GitHub repository locally, reads the repository tree, and extracts files for semantic analysis.",
      color: "text-indigo-400 border-indigo-500/30",
    },
    {
      icon: Database,
      title: "2. Vector Indexing",
      description: "Embeds codebase chunks using a local sentence-transformers model (MiniLM-L6-v2) and stores them in ChromaDB vector index.",
      color: "text-fuchsia-400 border-fuchsia-500/30",
    },
    {
      icon: Search,
      title: "3. Semantic Code Search",
      description: "Retrieves the target GitHub issue, parses its description, and executes vector similarity searches to pinpoint matching code snippets.",
      color: "text-violet-400 border-violet-500/30",
    },
    {
      icon: Cpu,
      title: "4. Agentic contribution planning",
      description: "Instructs specialized LLM agents (via OpenRouter/Claude/GPT-4o) to reason about the codebase, diagnose bugs, and estimate resolving efforts.",
      color: "text-indigo-400 border-indigo-500/30",
    },
    {
      icon: FileText,
      title: "5. Test & PR Generation",
      description: "Automatically writes comprehensive unit/integration tests and synthesizes a production-grade PR draft containing a review checklist.",
      color: "text-emerald-400 border-emerald-500/30",
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 md:p-10">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/75 backdrop-blur-md transition-opacity duration-300"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div className="relative w-full max-w-4xl max-h-[85vh] overflow-y-auto rounded-2xl glass-panel-heavy p-6 shadow-2xl transition-all duration-300 flex flex-col border border-border-subtle text-slate-100">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-6">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-white bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-violet-400">
              System Architecture & Workflow Flow
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              How OpenSourcePilot processes GitHub repositories and issues end-to-end.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-400 hover:text-white transition-colors duration-200"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* System Diagram Visual */}
        <div className="mb-8 p-4 bg-slate-950/60 rounded-xl border border-white/5">
          <h3 className="text-sm font-semibold text-indigo-300 mb-4 uppercase tracking-wider text-center">
            System Interaction Pipeline
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative text-center">
            <div className="p-3 bg-white/5 rounded-lg border border-white/5 flex flex-col items-center">
              <div className="p-2 bg-indigo-500/10 rounded-full text-indigo-400 mb-2">
                <FileText className="w-5 h-5" />
              </div>
              <span className="text-xs font-semibold text-white">GitHub Issue / URL</span>
              <span className="text-[10px] text-slate-400 mt-1">Developer inputs repo & issue</span>
            </div>
            
            <div className="hidden md:flex items-center justify-center text-slate-600 font-bold">➔</div>

            <div className="p-3 bg-white/5 rounded-lg border border-white/5 flex flex-col items-center">
              <div className="p-2 bg-violet-500/10 rounded-full text-violet-400 mb-2">
                <Cpu className="w-5 h-5" />
              </div>
              <span className="text-xs font-semibold text-white">FastAPI Workflow</span>
              <span className="text-[10px] text-slate-400 mt-1">ContributionWorkflowService orchestrates</span>
            </div>

            <div className="hidden md:flex items-center justify-center text-slate-600 font-bold">➔</div>

            <div className="p-3 bg-white/5 rounded-lg border border-white/5 flex flex-col items-center">
              <div className="p-2 bg-fuchsia-500/10 rounded-full text-fuchsia-400 mb-2">
                <Database className="w-5 h-5" />
              </div>
              <span className="text-xs font-semibold text-white">ChromaDB Store</span>
              <span className="text-[10px] text-slate-400 mt-1">Queries semantic code vector index</span>
            </div>
          </div>
        </div>

        {/* Detailed steps */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
            Pipeline Execution Details
          </h3>
          
          <div className="grid grid-cols-1 gap-4">
            {steps.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div
                  key={idx}
                  className="flex gap-4 p-4 bg-white/[0.02] rounded-xl border border-white/5 hover:border-white/10 transition-colors duration-200"
                >
                  <div className={`p-3 rounded-xl bg-white/[0.03] border ${step.color} self-start`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-white text-base">{step.title}</h4>
                    <p className="text-sm text-slate-400 mt-1 leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 pt-4 border-t border-white/10 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium rounded-xl text-sm transition-all duration-200 shadow-lg hover:shadow-indigo-500/10 active:scale-[0.98]"
          >
            Got It, Thanks!
          </button>
        </div>

      </div>
    </div>
  );
}
