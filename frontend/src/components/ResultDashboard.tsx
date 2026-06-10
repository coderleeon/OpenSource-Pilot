"use client";

import React, { useState } from "react";
import {
  Copy,
  Check,
  FileText,
  Search,
  Code2,
  FileCode,
  Layout,
  Info,
  ExternalLink,
  Flame,
  CheckCircle,
  AlertTriangle
} from "lucide-react";

interface CodeSnippet {
  file_path: string;
  language: string;
  snippet: string;
  relevance_distance: number;
}

interface IssueDetail {
  number: number;
  title: string;
  body: string | null;
  labels: string[];
  state: string;
  url: string;
  comments_count: number;
  author: string;
  created_at: string;
}

interface WorkflowRepositoryDetail {
  name: string;
  full_name: string;
  description: string | null;
  url: string;
  primary_language: string | null;
  default_branch: string;
}

interface WorkflowClassificationDetail {
  issue_type: string;
  issue_type_display: string;
  difficulty_estimate: string;
  suitability_score: number;
  beginner_friendly: boolean;
}

interface ContributionPlanResponse {
  plan_type: string;
  issue_type: string;
  problem_explanation: string;
  root_cause_hypothesis: string;
  implementation_steps: string[];
  files_to_modify: string[];
  relevant_concepts: string[];
  estimated_effort: string;
  references: string[];
  answer_explanation: string;
  key_questions: string[];
  suggested_resources: string[];
}

interface GeneratedTestsResponse {
  framework: string;
  test_file_path: string;
  unit_tests: string;
  integration_tests: string;
  edge_cases: string;
  dependencies: string[];
  setup_notes: string;
}

interface PRDraftResponse {
  title: string;
  summary: string;
  testing_checklist: string[];
  reviewer_notes: string;
  labels_suggested: string[];
  draft_body: string;
}

interface WorkflowMetadata {
  status: string;
  started_at: string;
  completed_at: string;
  duration_seconds: number;
  errors: string[];
}

interface ResultDashboardProps {
  data: {
    repository: WorkflowRepositoryDetail;
    issue: IssueDetail;
    classification: WorkflowClassificationDetail;
    relevant_files: string[];
    search_results: CodeSnippet[];
    contribution_plan: ContributionPlanResponse;
    generated_tests: GeneratedTestsResponse | null;
    pr_draft: PRDraftResponse | null;
    estimated_effort: string | null;
    metadata: WorkflowMetadata;
  };
}

export default function ResultDashboard({ data }: ResultDashboardProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "plan" | "snippets" | "tests" | "pr">("overview");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => {
      setCopiedId(null);
    }, 2000);
  };

  const {
    repository,
    issue,
    classification,
    relevant_files,
    search_results,
    contribution_plan,
    generated_tests,
    pr_draft,
    metadata
  } = data;

  const isContribution = contribution_plan.plan_type === "contribution";

  // Difficulty badge colors
  const getDifficultyColor = (diff: string) => {
    switch (diff.toLowerCase()) {
      case "easy":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      case "medium":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "hard":
        return "bg-rose-500/10 text-rose-400 border-rose-500/30";
      default:
        return "bg-slate-500/10 text-slate-400 border-slate-500/30";
    }
  };

  return (
    <div className="w-full flex flex-col gap-6">
      
      {/* Classification Banner / Header Card */}
      <div className="w-full rounded-2xl glass-panel border border-white/10 p-6 shadow-xl flex flex-col md:flex-row items-stretch md:items-center justify-between gap-6">
        
        {/* Left Info */}
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="text-lg font-bold text-white tracking-tight">{repository.full_name}</span>
            <span className="text-slate-500">/</span>
            <a
              href={issue.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1 group text-sm"
            >
              Issue #{issue.number}
              <ExternalLink className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100 transition-opacity" />
            </a>
          </div>
          <h1 className="text-xl font-semibold text-white/90 line-clamp-1">
            {issue.title}
          </h1>
          
          <div className="flex flex-wrap items-center gap-2 mt-1">
            <span className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              {classification.issue_type_display}
            </span>
            <span className={`px-2.5 py-1 text-xs font-semibold rounded-lg border ${getDifficultyColor(classification.difficulty_estimate)}`}>
              Difficulty: {classification.difficulty_estimate.toUpperCase()}
            </span>
            {classification.beginner_friendly && (
              <span className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-teal-500/10 text-teal-400 border border-teal-500/20">
                Beginner Friendly
              </span>
            )}
            <span className="text-xs font-mono text-slate-400 ml-1">
              Time: {metadata.duration_seconds.toFixed(1)}s
            </span>
          </div>
        </div>

        {/* Right Score Meter */}
        <div className="flex items-center gap-4 bg-white/[0.02] border border-white/5 p-4 rounded-xl shrink-0 self-start md:self-auto">
          <div className="flex flex-col text-right">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Suitability Score</span>
            <span className="text-2xl font-black text-white font-mono">{classification.suitability_score.toFixed(1)}<span className="text-xs text-slate-500">/10</span></span>
          </div>
          
          <div className="relative w-12 h-12 flex items-center justify-center">
            {/* Simple circular visual helper */}
            <svg className="w-12 h-12 transform -rotate-90">
              <circle
                cx="24"
                cy="24"
                r="20"
                className="stroke-slate-800"
                strokeWidth="4"
                fill="transparent"
              />
              <circle
                cx="24"
                cy="24"
                r="20"
                className="stroke-indigo-500"
                strokeWidth="4"
                fill="transparent"
                strokeDasharray={2 * Math.PI * 20}
                strokeDashoffset={2 * Math.PI * 20 * (1 - classification.suitability_score / 10)}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <Flame className={`w-5 h-5 ${classification.suitability_score >= 7 ? "text-indigo-400" : "text-slate-500"}`} />
            </div>
          </div>
        </div>

      </div>

      {/* Tabs bar */}
      <div className="flex border-b border-white/10 overflow-x-auto pb-px">
        <button
          onClick={() => setActiveTab("overview")}
          className={`flex items-center gap-2 px-5 py-3 border-b-2 font-semibold text-sm transition-all duration-200 cursor-pointer shrink-0 ${
            activeTab === "overview"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Layout className="w-4 h-4" />
          Overview
        </button>
        <button
          onClick={() => setActiveTab("plan")}
          className={`flex items-center gap-2 px-5 py-3 border-b-2 font-semibold text-sm transition-all duration-200 cursor-pointer shrink-0 ${
            activeTab === "plan"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileText className="w-4 h-4" />
          Contribution Plan
        </button>
        <button
          onClick={() => setActiveTab("snippets")}
          className={`flex items-center gap-2 px-5 py-3 border-b-2 font-semibold text-sm transition-all duration-200 cursor-pointer shrink-0 ${
            activeTab === "snippets"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Search className="w-4 h-4" />
          Code Search ({search_results.length})
        </button>
        <button
          onClick={() => setActiveTab("tests")}
          disabled={!generated_tests}
          className={`flex items-center gap-2 px-5 py-3 border-b-2 font-semibold text-sm transition-all duration-200 shrink-0 ${
            !generated_tests
              ? "opacity-40 cursor-not-allowed text-slate-600"
              : activeTab === "tests"
              ? "border-indigo-500 text-white cursor-pointer"
              : "border-transparent text-slate-400 hover:text-slate-200 cursor-pointer"
          }`}
        >
          <FileCode className="w-4 h-4" />
          Generated Tests
        </button>
        <button
          onClick={() => setActiveTab("pr")}
          disabled={!pr_draft}
          className={`flex items-center gap-2 px-5 py-3 border-b-2 font-semibold text-sm transition-all duration-200 shrink-0 ${
            !pr_draft
              ? "opacity-40 cursor-not-allowed text-slate-600"
              : activeTab === "pr"
              ? "border-indigo-500 text-white cursor-pointer"
              : "border-transparent text-slate-400 hover:text-slate-200 cursor-pointer"
          }`}
        >
          <Code2 className="w-4 h-4" />
          PR Draft
        </button>
      </div>

      {/* Tabs content */}
      <div className="w-full">
        
        {/* Tab 1: Overview */}
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Left Col: Issue & Repository details */}
            <div className="lg:col-span-2 flex flex-col gap-6">
              
              {/* Repository Metadata */}
              <div className="rounded-xl glass-panel p-5 border border-white/5">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300 mb-3">Repository Context</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="block text-xs text-slate-500">Name</span>
                    <span className="font-semibold text-white">{repository.name}</span>
                  </div>
                  <div>
                    <span className="block text-xs text-slate-500">Primary Language</span>
                    <span className="font-semibold text-white">{repository.primary_language || "N/A"}</span>
                  </div>
                  <div>
                    <span className="block text-xs text-slate-500">Default Branch</span>
                    <span className="font-mono text-xs text-slate-300 bg-white/5 px-2 py-0.5 rounded border border-white/5">{repository.default_branch}</span>
                  </div>
                  <div>
                    <span className="block text-xs text-slate-500">Repository Link</span>
                    <a
                      href={repository.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-indigo-400 hover:underline inline-flex items-center gap-1 mt-0.5"
                    >
                      GitHub Repo <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
                {repository.description && (
                  <div className="mt-4 pt-3 border-t border-white/5">
                    <span className="block text-xs text-slate-500 mb-1">Description</span>
                    <p className="text-sm text-slate-300">{repository.description}</p>
                  </div>
                )}
              </div>

              {/* Issue Description */}
              <div className="rounded-xl glass-panel p-5 border border-white/5">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300">Issue Details</h3>
                  <div className="flex gap-2">
                    <span className="px-2 py-0.5 text-[10px] font-semibold bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 rounded uppercase">
                      {issue.state}
                    </span>
                    <span className="px-2 py-0.5 text-[10px] font-semibold bg-white/5 text-slate-400 rounded">
                      Author: {issue.author}
                    </span>
                  </div>
                </div>
                <div className="max-h-[300px] overflow-y-auto bg-slate-950/40 p-4 rounded-xl border border-white/5">
                  {issue.body ? (
                    <pre className="text-xs text-slate-300 font-sans whitespace-pre-wrap leading-relaxed">
                      {issue.body}
                    </pre>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No description provided in this issue.</p>
                  )}
                </div>
              </div>
            </div>

            {/* Right Col: Index & Scan details */}
            <div className="flex flex-col gap-6">
              
              {/* Codebase scan info */}
              <div className="rounded-xl glass-panel p-5 border border-white/5">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300 mb-3 font-semibold">Semantic Match Files</h3>
                <p className="text-xs text-slate-400 mb-3 leading-relaxed">
                  These files matched the query embeddings and were target components:
                </p>
                {relevant_files.length > 0 ? (
                  <ul className="space-y-1.5 max-h-[220px] overflow-y-auto pr-1">
                    {relevant_files.map((file, idx) => (
                      <li
                        key={idx}
                        className="text-xs font-mono text-slate-300 bg-white/[0.02] border border-white/5 p-2 rounded-lg truncate hover:text-white transition-colors"
                        title={file}
                      >
                        {file}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-500 italic">No matching code files located.</p>
                )}
              </div>

              {/* Warnings and soft errors */}
              {metadata.errors && metadata.errors.length > 0 && (
                <div className="rounded-xl bg-amber-500/5 border border-amber-500/20 p-5">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-amber-400 flex items-center gap-1.5 mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    Workflow Advisories
                  </h3>
                  <ul className="space-y-1 text-xs text-slate-300">
                    {metadata.errors.map((err, idx) => (
                      <li key={idx} className="list-disc list-inside leading-relaxed">
                        {err}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

          </div>
        )}

        {/* Tab 2: Plan */}
        {activeTab === "plan" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Plan contents */}
            <div className="lg:col-span-2 flex flex-col gap-6">
              
              {/* Problem Explanation */}
              <div className="rounded-xl glass-panel p-5 border border-white/5">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300 mb-3">Problem Summary</h3>
                <p className="text-sm text-slate-300 leading-relaxed">
                  {contribution_plan.problem_explanation || "No explanation summary generated."}
                </p>
              </div>

              {/* Hypothesized root cause */}
              {isContribution && contribution_plan.root_cause_hypothesis && (
                <div className="rounded-xl glass-panel p-5 border border-white/5">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300 mb-3">Root Cause Diagnosis</h3>
                  <p className="text-sm text-slate-300 leading-relaxed font-mono bg-slate-950/20 p-3 rounded-lg border border-white/5">
                    {contribution_plan.root_cause_hypothesis}
                  </p>
                </div>
              )}

              {/* Steps checklist */}
              {isContribution ? (
                <div className="rounded-xl glass-panel p-5 border border-white/5">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300">Implementation Milestones</h3>
                    <button
                      onClick={() => handleCopy(contribution_plan.implementation_steps.join("\n"), "steps")}
                      className="px-2.5 py-1 text-xs font-semibold bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white rounded-lg border border-white/10 flex items-center gap-1 transition-all active:scale-[0.98]"
                    >
                      {copiedId === "steps" ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy List</span>
                        </>
                      )}
                    </button>
                  </div>
                  {contribution_plan.implementation_steps && contribution_plan.implementation_steps.length > 0 ? (
                    <ul className="space-y-3">
                      {contribution_plan.implementation_steps.map((step, idx) => (
                        <li key={idx} className="flex gap-3 text-sm text-slate-300 items-start">
                          <span className="w-5 h-5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs flex items-center justify-center font-bold font-mono shrink-0 mt-0.5">
                            {idx + 1}
                          </span>
                          <span className="leading-relaxed">{step}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-slate-500 italic">No checklist steps synthesized.</p>
                  )}
                </div>
              ) : (
                /* Question/Discussion plan */
                <div className="rounded-xl glass-panel p-5 border border-white/5">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300">Explanation & Answer</h3>
                    <button
                      onClick={() => handleCopy(contribution_plan.answer_explanation, "ans")}
                      className="px-2.5 py-1 text-xs font-semibold bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white rounded-lg border border-white/10 flex items-center gap-1 transition-all active:scale-[0.98]"
                    >
                      {copiedId === "ans" ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy Answer</span>
                        </>
                      )}
                    </button>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap bg-slate-950/20 p-4 rounded-xl border border-white/5">
                    {contribution_plan.answer_explanation}
                  </p>
                </div>
              )}
            </div>

            {/* Right details panel */}
            <div className="flex flex-col gap-6">
              
              {/* Files to edit / Concepts */}
              {isContribution ? (
                <div className="rounded-xl glass-panel p-5 border border-white/5">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300 mb-3">Target Code Files</h3>
                  {contribution_plan.files_to_modify && contribution_plan.files_to_modify.length > 0 ? (
                    <ul className="space-y-1.5">
                      {contribution_plan.files_to_modify.map((file, idx) => (
                        <li
                          key={idx}
                          className="text-xs font-mono text-slate-300 bg-white/[0.02] border border-white/5 p-2 rounded-lg truncate"
                        >
                          {file}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No code files explicitly listed for editing.</p>
                  )}
                </div>
              ) : (
                <div className="rounded-xl glass-panel p-5 border border-white/5">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300 mb-3">Key Questions</h3>
                  {contribution_plan.key_questions && contribution_plan.key_questions.length > 0 ? (
                    <ul className="space-y-2">
                      {contribution_plan.key_questions.map((q, idx) => (
                        <li key={idx} className="text-xs text-slate-300 leading-relaxed list-disc list-inside">
                          {q}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No key questions analyzed.</p>
                  )}
                </div>
              )}

              {/* Effort Estimation */}
              <div className="rounded-xl glass-panel p-5 border border-white/5">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300 mb-2">Effort Estimation</h3>
                <div className="p-3 bg-white/[0.02] border border-white/5 rounded-xl flex items-center justify-between">
                  <span className="text-xs text-slate-400">Resolution Time</span>
                  <span className="text-sm font-bold text-white bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 rounded-lg">
                    {contribution_plan.estimated_effort || "Unknown"}
                  </span>
                </div>
              </div>

              {/* Suggested Resources / References */}
              <div className="rounded-xl glass-panel p-5 border border-white/5">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300 mb-3">
                  {isContribution ? "References" : "Suggested Resources"}
                </h3>
                {isContribution ? (
                  contribution_plan.references && contribution_plan.references.length > 0 ? (
                    <ul className="space-y-1.5">
                      {contribution_plan.references.map((ref, idx) => (
                        <li key={idx} className="text-xs text-slate-400 leading-relaxed list-disc list-inside">
                          {ref}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No resources referenced.</p>
                  )
                ) : (
                  contribution_plan.suggested_resources && contribution_plan.suggested_resources.length > 0 ? (
                    <ul className="space-y-1.5">
                      {contribution_plan.suggested_resources.map((res, idx) => (
                        <li key={idx} className="text-xs text-slate-400 leading-relaxed list-disc list-inside">
                          {res}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No resources suggested.</p>
                  )
                )}
              </div>

            </div>

          </div>
        )}

        {/* Tab 3: Code Search Snippets */}
        {activeTab === "snippets" && (
          <div className="flex flex-col gap-6">
            <div className="rounded-xl glass-panel p-5 border border-white/5">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300 mb-2">ChromaDB Code retrieval</h3>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                The similarity search matches based on vector distance from MiniLM embedding calculations. Lower distance indicates high similarity.
              </p>

              {search_results.length > 0 ? (
                <div className="space-y-5">
                  {search_results.map((snippet, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl border border-white/5 bg-slate-950/40 hover:border-white/10 transition-all overflow-hidden"
                    >
                      {/* snippet header */}
                      <div className="flex items-center justify-between px-4 py-3 bg-white/[0.02] border-b border-white/5">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-slate-300 font-mono">{snippet.file_path}</span>
                          <span className="px-1.5 py-0.5 text-[9px] font-semibold bg-white/5 text-slate-400 rounded-md font-mono uppercase">
                            {snippet.language}
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] font-semibold text-slate-500 font-mono">
                            Distance: {snippet.relevance_distance.toFixed(4)}
                          </span>
                          <button
                            onClick={() => handleCopy(snippet.snippet, `snippet-${idx}`)}
                            className="p-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                            title="Copy snippet code"
                          >
                            {copiedId === `snippet-${idx}` ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      </div>

                      {/* snippet body */}
                      <div className="p-4 overflow-x-auto">
                        <pre className="text-xs text-slate-300 font-mono whitespace-pre leading-relaxed">
                          {snippet.snippet}
                        </pre>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500 italic">No semantic snippets found.</p>
              )}
            </div>
          </div>
        )}

        {/* Tab 4: Tests */}
        {activeTab === "tests" && generated_tests && (
          <div className="flex flex-col gap-6">
            
            {/* Setup and Notes */}
            <div className="rounded-xl glass-panel p-5 border border-white/5 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300 mb-2">Test Setup Overview</h3>
                <div className="space-y-1.5 text-xs">
                  <div>
                    <span className="text-slate-500">Framework:</span>{" "}
                    <span className="font-semibold text-white uppercase font-mono">{generated_tests.framework}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Suggested Test Path:</span>{" "}
                    <span className="font-semibold text-slate-300 font-mono">{generated_tests.test_file_path}</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300 mb-2">Required Dependencies</h3>
                {generated_tests.dependencies && generated_tests.dependencies.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {generated_tests.dependencies.map((dep, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-white/5 border border-white/5 font-mono text-[10px] text-slate-300"
                      >
                        {dep}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-xs text-slate-500 italic">No additional test dependencies requested.</span>
                )}
              </div>
            </div>

            {generated_tests.setup_notes && (
              <div className="rounded-xl bg-indigo-500/5 border border-indigo-500/10 p-5 text-sm text-slate-300 leading-relaxed">
                <h4 className="text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-1">Configuration Notes</h4>
                {generated_tests.setup_notes}
              </div>
            )}

            {/* Test suites code blocks */}
            <div className="space-y-6">
              
              {/* Unit Tests */}
              {generated_tests.unit_tests && (
                <div className="rounded-xl border border-white/5 bg-slate-950/40 overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-3 bg-white/[0.02] border-b border-white/5">
                    <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Unit Tests Suite</span>
                    <button
                      onClick={() => handleCopy(generated_tests.unit_tests, "unit-tests")}
                      className="px-2.5 py-1 text-xs font-semibold bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white rounded-lg border border-white/10 flex items-center gap-1 transition-all active:scale-[0.98]"
                    >
                      {copiedId === "unit-tests" ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy Code</span>
                        </>
                      )}
                    </button>
                  </div>
                  <div className="p-4 overflow-x-auto max-h-[400px] overflow-y-auto">
                    <pre className="text-xs text-slate-300 font-mono whitespace-pre leading-relaxed">
                      {generated_tests.unit_tests}
                    </pre>
                  </div>
                </div>
              )}

              {/* Integration Tests */}
              {generated_tests.integration_tests && (
                <div className="rounded-xl border border-white/5 bg-slate-950/40 overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-3 bg-white/[0.02] border-b border-white/5">
                    <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Integration Tests Suite</span>
                    <button
                      onClick={() => handleCopy(generated_tests.integration_tests, "integration-tests")}
                      className="px-2.5 py-1 text-xs font-semibold bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white rounded-lg border border-white/10 flex items-center gap-1 transition-all active:scale-[0.98]"
                    >
                      {copiedId === "integration-tests" ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy Code</span>
                        </>
                      )}
                    </button>
                  </div>
                  <div className="p-4 overflow-x-auto max-h-[400px] overflow-y-auto">
                    <pre className="text-xs text-slate-300 font-mono whitespace-pre leading-relaxed">
                      {generated_tests.integration_tests}
                    </pre>
                  </div>
                </div>
              )}

              {/* Edge cases */}
              {generated_tests.edge_cases && (
                <div className="rounded-xl border border-white/5 bg-slate-950/40 overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-3 bg-white/[0.02] border-b border-white/5">
                    <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Edge Cases & Error Handling</span>
                    <button
                      onClick={() => handleCopy(generated_tests.edge_cases, "edge-tests")}
                      className="px-2.5 py-1 text-xs font-semibold bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white rounded-lg border border-white/10 flex items-center gap-1 transition-all active:scale-[0.98]"
                    >
                      {copiedId === "edge-tests" ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy Code</span>
                        </>
                      )}
                    </button>
                  </div>
                  <div className="p-4 overflow-x-auto max-h-[400px] overflow-y-auto">
                    <pre className="text-xs text-slate-300 font-mono whitespace-pre leading-relaxed">
                      {generated_tests.edge_cases}
                    </pre>
                  </div>
                </div>
              )}

            </div>

          </div>
        )}

        {/* Tab 5: PR Draft */}
        {activeTab === "pr" && pr_draft && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* PR Details */}
            <div className="lg:col-span-2 flex flex-col gap-6">
              
              {/* Draft body (Markdown) */}
              <div className="rounded-xl border border-white/5 bg-slate-950/40 overflow-hidden">
                <div className="flex items-center justify-between px-4 py-3 bg-white/[0.02] border-b border-white/5">
                  <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Full Markdown PR Body</span>
                  <button
                    onClick={() => handleCopy(pr_draft.draft_body, "pr-body")}
                    className="px-2.5 py-1 text-xs font-semibold bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white rounded-lg border border-white/10 flex items-center gap-1 transition-all active:scale-[0.98]"
                  >
                    {copiedId === "pr-body" ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy Markdown</span>
                      </>
                    )}
                  </button>
                </div>
                <div className="p-5 max-h-[500px] overflow-y-auto">
                  <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
                    {pr_draft.draft_body}
                  </pre>
                </div>
              </div>
            </div>

            {/* PR Metadata panel */}
            <div className="flex flex-col gap-6">
              
              {/* Proposed Title */}
              <div className="rounded-xl glass-panel p-5 border border-white/5">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300">PR Title</h3>
                  <button
                    onClick={() => handleCopy(pr_draft.title, "pr-title")}
                    className="p-1 rounded hover:bg-white/5 text-slate-400 hover:text-white transition-colors"
                    title="Copy PR Title"
                  >
                    {copiedId === "pr-title" ? (
                      <Check className="w-3 h-3 text-emerald-400" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                </div>
                <p className="text-sm font-mono text-white bg-slate-950/40 p-3 rounded-lg border border-white/5">
                  {pr_draft.title}
                </p>
              </div>

              {/* Testing checklist */}
              <div className="rounded-xl glass-panel p-5 border border-white/5">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300 mb-3 font-semibold">Testing Checklist</h3>
                {pr_draft.testing_checklist && pr_draft.testing_checklist.length > 0 ? (
                  <ul className="space-y-2">
                    {pr_draft.testing_checklist.map((item, idx) => (
                      <li key={idx} className="flex gap-2 text-xs text-slate-300 items-start">
                        <CheckCircle className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-500 italic">No checklist generated.</p>
                )}
              </div>

              {/* Reviewer labels suggested */}
              {pr_draft.labels_suggested && pr_draft.labels_suggested.length > 0 && (
                <div className="rounded-xl glass-panel p-5 border border-white/5">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-300 mb-2">Suggested Labels</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {pr_draft.labels_suggested.map((label, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-white/5 border border-white/5 font-semibold text-[10px] text-indigo-300"
                      >
                        {label}
                      </span>
                    ))}
                  </div>
                </div>
              )}

            </div>

          </div>
        )}

      </div>
      
    </div>
  );
}
