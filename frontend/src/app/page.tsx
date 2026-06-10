"use client";

import React, { useState } from "react";
import { Compass, HelpCircle, AlertCircle, RefreshCw, Search } from "lucide-react";
import HowItWorksModal from "@/components/HowItWorksModal";
import WorkflowForm from "@/components/WorkflowForm";
import WorkflowLoading from "@/components/WorkflowLoading";
import ResultDashboard from "@/components/ResultDashboard";

export default function Home() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultData, setResultData] = useState<any>(null);
  const [isNotFound, setIsNotFound] = useState(false);

  const handleStartWorkflow = async (repoUrl: string, issueNumber: number) => {
    setIsLoading(true);
    setError(null);
    setResultData(null);
    setIsNotFound(false);

    const backendBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const endpoint = `${backendBaseUrl}/api/v1/issue/complete-workflow`;

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repo_url: repoUrl,
          issue_number: issueNumber,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errMsg = errorData?.detail
          ? typeof errorData.detail === "string"
            ? errorData.detail
            : JSON.stringify(errorData.detail)
          : "An unexpected error occurred during pipeline execution. Please verify the repository exists and the issue number is correct.";

        if (response.status === 404) {
          setIsNotFound(true);
          setError(errMsg);
          return;
        }

        throw new Error(errMsg);
      }

      const data = await response.json();
      setResultData(data);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to establish a connection to the OpenSourcePilot backend API.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResultData(null);
    setError(null);
    setIsNotFound(false);
  };

  return (
    <div className="flex flex-col min-h-screen bg-bg-base text-slate-100 selection:bg-indigo-500/30">

      {/* Top Navbar */}
      <header className="sticky top-0 z-40 w-full border-b border-white/5 bg-bg-base/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">

          {/* Logo brand */}
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-gradient-to-tr from-indigo-500 to-violet-500 rounded-xl text-white shadow-md shadow-indigo-500/10">
              <Compass className="w-5 h-5 animate-pulse" />
            </div>
            <span className="font-extrabold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400">
              OpenSource<span className="text-indigo-400">Pilot</span>
            </span>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsModalOpen(true)}
              className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-white/5 hover:bg-white/10 border border-white/5 text-slate-300 hover:text-white flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <HelpCircle className="w-4 h-4" />
              How It Works
            </button>

            <a
              href="https://github.com/coderleeon/OpenSource-Pilot"
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 text-slate-400 hover:text-slate-200 transition-colors"
              title="View on GitHub"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.167 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.164 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
              </svg>
            </a>
          </div>

        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12 flex flex-col gap-10">

        {/* Landing Hero Section (only when not showing results or loading) */}
        {!isLoading && !resultData && (
          <div className="text-center max-w-3xl mx-auto flex flex-col gap-4 py-6 md:py-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold w-fit mx-auto animate-float">
              AI-Powered Open Source Contribution Assistant
            </div>
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-black tracking-tight text-white leading-tight">
              Empower Open Source Contributions with{" "}
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-violet-400 to-fuchsia-400">
                Agentic Intelligence
              </span>
            </h1>
            <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
              OpenSourcePilot automates issue triage, similarity code search, code structure analysis, solution design, test suite synthesis, and PR drafts directly from a single URL.
            </p>
          </div>
        )}

        {/* Dynamic State Layout */}
        <div className="w-full">
          {isLoading ? (
            <WorkflowLoading />
          ) : isNotFound ? (
            <div className="max-w-2xl mx-auto rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6 md:p-8 flex flex-col items-center text-center gap-4 shadow-xl">
              <div className="p-3 bg-amber-500/10 rounded-full text-amber-400">
                <Search className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Issue Not Found</h3>
                <p className="text-sm text-slate-400 mt-2 max-w-md leading-relaxed">{error}</p>
              </div>
              <button
                onClick={handleReset}
                className="mt-2 px-5 py-2.5 bg-white/5 hover:bg-white/10 border border-white/5 text-white font-medium rounded-xl text-sm flex items-center gap-2 transition-all active:scale-[0.98]"
              >
                <RefreshCw className="w-4 h-4" />
                Try Another Input
              </button>
            </div>
          ) : error ? (
            <div className="max-w-2xl mx-auto rounded-2xl border border-rose-500/20 bg-rose-500/5 p-6 md:p-8 flex flex-col items-center text-center gap-4 shadow-xl">
              <div className="p-3 bg-rose-500/10 rounded-full text-rose-400">
                <AlertCircle className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Execution Failed</h3>
                <p className="text-sm text-slate-400 mt-2 max-w-md leading-relaxed">{error}</p>
              </div>
              <button
                onClick={handleReset}
                className="mt-2 px-5 py-2.5 bg-white/5 hover:bg-white/10 border border-white/5 text-white font-medium rounded-xl text-sm flex items-center gap-2 transition-all active:scale-[0.98]"
              >
                <RefreshCw className="w-4 h-4" />
                Try Another Input
              </button>
            </div>
          ) : resultData ? (
            <div className="flex flex-col gap-6">
              {/* Back to Input trigger */}
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-400">
                  Showing results for {resultData.repository.name}
                </span>
                <button
                  onClick={handleReset}
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/5 text-slate-300 hover:text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all active:scale-[0.98]"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Analyze Another Issue
                </button>
              </div>
              <ResultDashboard data={resultData} />
            </div>
          ) : (
            <div className="max-w-4xl mx-auto">
              <WorkflowForm onSubmit={handleStartWorkflow} isLoading={false} />
            </div>
          )}
        </div>

        {/* Features / Details cards (only show on landing page) */}
        {!isLoading && !resultData && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">

            <div className="p-5 rounded-2xl bg-white/[0.01] border border-white/5 flex flex-col gap-2 hover:bg-white/[0.02] transition-colors">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-sm">
                1
              </div>
              <h3 className="font-semibold text-white text-base">Issue Classification</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Detects whether an issue is a bug, feature request, question, or discussion. Analyzes suitability and computes difficulty metrics dynamically.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-white/[0.01] border border-white/5 flex flex-col gap-2 hover:bg-white/[0.02] transition-colors">
              <div className="w-8 h-8 rounded-lg bg-violet-500/10 border border-violet-500/20 text-violet-400 flex items-center justify-center font-bold text-sm">
                2
              </div>
              <h3 className="font-semibold text-white text-base">Vector Search Retrieval</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Embeds target repository modules dynamically in local ChromaDB vectors using MiniLM models, retrieving closest similarity candidates high-speed.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-white/[0.01] border border-white/5 flex flex-col gap-2 hover:bg-white/[0.02] transition-colors">
              <div className="w-8 h-8 rounded-lg bg-fuchsia-500/10 border border-fuchsia-500/20 text-fuchsia-400 flex items-center justify-center font-bold text-sm">
                3
              </div>
              <h3 className="font-semibold text-white text-base">Resolution & Synthesis</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Synthesizes a resolution plan with estimated effort, generates comprehensive pytest suites, and builds formal Pull Request descriptions.
              </p>
            </div>

          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="w-full border-t border-white/5 py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <span>&copy; {new Date().getFullYear()} OpenSourcePilot. All rights reserved.</span>
          <span className="flex items-center gap-3">
            <span>Local Embedded LLMs</span>
            <span>&bull;</span>
            <span>ChromaDB Vector Indexing</span>
            <span>&bull;</span>
            <span>FastAPI Services</span>
          </span>
        </div>
      </footer>

      {/* "How It Works" Modal */}
      <HowItWorksModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />

    </div>
  );
}
