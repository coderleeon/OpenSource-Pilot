"use client";

import React, { useState, useEffect } from "react";
import { Compass, HelpCircle, AlertCircle, RefreshCw, Search, Award, Bookmark, ShieldAlert, Sparkles, GitBranch, CheckCircle2 } from "lucide-react";
import HowItWorksModal from "@/components/HowItWorksModal";
import WorkflowForm from "@/components/WorkflowForm";
import WorkflowLoading from "@/components/WorkflowLoading";
import ResultDashboard from "@/components/ResultDashboard";
import DiscoverTab from "@/components/DiscoverTab";
import AnalyzeTab from "@/components/AnalyzeTab";
import PipelinePanel from "@/components/PipelinePanel";
import ImpactDashboard from "@/components/ImpactDashboard";

interface ImpactStats {
  issuesSolved: number;
  prsSubmitted: number;
  prsMerged: number;
  reposContributed: number;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<"discover" | "analyze" | "contribute">("discover");
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Pipeline state
  const [savedOpportunities, setSavedOpportunities] = useState<any[]>([]);
  const [savedIds, setSavedIds] = useState<string[]>([]);
  
  // Impact Stats state
  const [impactStats, setImpactStats] = useState<ImpactStats>({
    issuesSolved: 0,
    prsSubmitted: 0,
    prsMerged: 0,
    reposContributed: 0,
  });

  // Contribute states
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultData, setResultData] = useState<any>(null);
  const [isNotFound, setIsNotFound] = useState(false);

  // Initial routing targets when transitioning between tabs
  const [analyzeUrl, setAnalyzeUrl] = useState("");
  const [contributeUrl, setContributeUrl] = useState("");
  const [contributeIssue, setContributeIssue] = useState("");

  // Load from local storage on mount
  useEffect(() => {
    try {
      const storedPipeline = localStorage.getItem("opensourcepilot_pipeline");
      if (storedPipeline) {
        const parsed = JSON.parse(storedPipeline);
        setSavedOpportunities(parsed);
        setSavedIds(parsed.map((opp: any) => `${opp.repository.full_name}#${opp.issue.number}`));
      }

      const storedStats = localStorage.getItem("opensourcepilot_impact");
      if (storedStats) {
        setImpactStats(JSON.parse(storedStats));
      }
    } catch (e) {
      console.error("Failed loading local storage", e);
    }
  }, []);

  const handleUpdateStats = (newStats: ImpactStats) => {
    setImpactStats(newStats);
    localStorage.setItem("opensourcepilot_impact", JSON.stringify(newStats));
  };

  const handleSaveOpportunity = (opp: any) => {
    const key = `${opp.repository.full_name}#${opp.issue.number}`;
    let newPipeline = [...savedOpportunities];
    
    if (savedIds.includes(key)) {
      newPipeline = newPipeline.filter(item => `${item.repository.full_name}#${item.issue.number}` !== key);
    } else {
      newPipeline.push(opp);
      // Increment saved repos stat
      const newStats = { ...impactStats, reposContributed: impactStats.reposContributed + 1 };
      handleUpdateStats(newStats);
    }

    setSavedOpportunities(newPipeline);
    setSavedIds(newPipeline.map(item => `${item.repository.full_name}#${item.issue.number}`));
    localStorage.setItem("opensourcepilot_pipeline", JSON.stringify(newPipeline));
  };

  const handleRemoveOpportunity = (opp: any) => {
    const key = `${opp.repository.full_name}#${opp.issue.number}`;
    const newPipeline = savedOpportunities.filter(item => `${item.repository.full_name}#${item.issue.number}` !== key);
    setSavedOpportunities(newPipeline);
    setSavedIds(newPipeline.map(item => `${item.repository.full_name}#${item.issue.number}`));
    localStorage.setItem("opensourcepilot_pipeline", JSON.stringify(newPipeline));
  };

  const handleAnalyzeRepo = (url: string) => {
    setAnalyzeUrl(url);
    setActiveTab("analyze");
  };

  const handleContribute = (url: string, issueNumber: number) => {
    setContributeUrl(url);
    setContributeIssue(issueNumber.toString());
    setActiveTab("contribute");
  };

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
      
      // Auto increment submitted PR and issues solved stats on success
      const newStats = {
        ...impactStats,
        prsSubmitted: impactStats.prsSubmitted + 1,
        issuesSolved: impactStats.issuesSolved + 1
      };
      handleUpdateStats(newStats);

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
    setContributeUrl("");
    setContributeIssue("");
  };

  return (
    <div className="flex flex-col min-h-screen bg-bg-base text-slate-100 selection:bg-indigo-500/30">

      {/* Top Navbar */}
      <header className="sticky top-0 z-40 w-full border-b border-white/5 bg-bg-base/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">

          {/* Logo brand */}
          <div className="flex items-center gap-2.5 shrink-0">
            <div className="p-2 bg-gradient-to-tr from-indigo-500 to-violet-500 rounded-xl text-white shadow-md shadow-indigo-500/10">
              <Compass className="w-5 h-5" />
            </div>
            <span className="font-extrabold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400">
              OpenSource<span className="text-indigo-400">Pilot</span>
            </span>
          </div>

          {/* Center Tabs Navigation */}
          <div className="flex items-center gap-1.5 bg-white/5 border border-white/5 p-1 rounded-xl mx-4 overflow-x-auto">
            <button
              onClick={() => setActiveTab("discover")}
              className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                activeTab === "discover"
                  ? "bg-indigo-500 text-white shadow-md"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Discover
            </button>
            <button
              onClick={() => setActiveTab("analyze")}
              className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                activeTab === "analyze"
                  ? "bg-indigo-500 text-white shadow-md"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Analyze
            </button>
            <button
              onClick={() => setActiveTab("contribute")}
              className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                activeTab === "contribute"
                  ? "bg-indigo-500 text-white shadow-md"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Contribute
            </button>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => setIsModalOpen(true)}
              className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-white/5 hover:bg-white/10 border border-white/5 text-slate-300 hover:text-white flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <HelpCircle className="w-4 h-4" />
              <span className="hidden sm:inline">How It Works</span>
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
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        
        {/* Main Columns Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start">
          
          {/* Active Tab Panel (Colspan 3) */}
          <div className="lg:col-span-3 flex flex-col gap-6">
            
            {/* 1. Discover Tab */}
            {activeTab === "discover" && (
              <DiscoverTab
                onAnalyzeRepo={handleAnalyzeRepo}
                onContribute={handleContribute}
                onSaveOpportunity={handleSaveOpportunity}
                savedIds={savedIds}
              />
            )}

            {/* 2. Analyze Tab */}
            {activeTab === "analyze" && (
              <AnalyzeTab
                onStartContribution={handleAnalyzeRepo}
                initialUrl={analyzeUrl}
              />
            )}

            {/* 3. Contribute Tab */}
            {activeTab === "contribute" && (
              <div className="flex flex-col gap-6">
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
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-slate-400 font-semibold">
                        Workflow results for {resultData.repository.name}
                      </span>
                      <div className="flex gap-2">
                        {/* Simulation action: Mark as Merged */}
                        <button
                          onClick={() => {
                            const newStats = { ...impactStats, prsMerged: impactStats.prsMerged + 1 };
                            handleUpdateStats(newStats);
                            alert("PR status logged! Contributor rank and impact score updated.");
                          }}
                          className="px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 text-emerald-400 hover:text-emerald-300 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all active:scale-[0.98] cursor-pointer"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Mark PR Merged
                        </button>

                        <button
                          onClick={handleReset}
                          className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/5 text-slate-300 hover:text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all active:scale-[0.98] cursor-pointer"
                        >
                          <RefreshCw className="w-3.5 h-3.5" />
                          Analyze Another Issue
                        </button>
                      </div>
                    </div>
                    <ResultDashboard data={resultData} />
                  </div>
                ) : (
                  <div className="max-w-4xl mx-auto w-full">
                    <WorkflowForm
                      onSubmit={handleStartWorkflow}
                      isLoading={false}
                      initialRepoUrl={contributeUrl}
                      initialIssueNumber={contributeIssue}
                    />
                  </div>
                )}
              </div>
            )}

          </div>

          {/* Right Sidebar Widgets Panel (Colspan 1) */}
          <div className="lg:col-span-1 flex flex-col gap-6 w-full">
            <ImpactDashboard
              stats={impactStats}
              onUpdateStats={handleUpdateStats}
            />

            <PipelinePanel
              savedOpportunities={savedOpportunities}
              onRemove={handleRemoveOpportunity}
              onAnalyzeRepo={handleAnalyzeRepo}
              onContribute={handleContribute}
            />
          </div>

        </div>

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
