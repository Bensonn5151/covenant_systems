"use client";

import { useEffect, useState } from "react";
import { Shield, CheckCircle, XCircle, AlertTriangle, FileUp, Upload, Loader2 } from "lucide-react";
import { fetchSamplePolicies, runComparison, runComparisonWithFile } from "@/lib/api";
import type { SamplePolicy, ComparisonResult, ComparisonMatch, RiskLevel, SeveritySignal } from "@/lib/types";
import StatCard from "@/components/shared/StatCard";
import ComplianceHealthScore from "@/components/dashboard/ComplianceHealthScore";

const AREA_LABELS: Record<string, string> = {
  data_collection: "Data Collection",
  data_use: "Data Use",
  data_disclosure: "Data Disclosure",
  consent: "Consent",
  breach_notification: "Breach Notification",
  data_retention: "Data Retention",
  access_rights: "Access Rights",
  accountability: "Accountability",
};

export default function DashboardOverview() {
  const [policies, setPolicies] = useState<SamplePolicy[]>([]);
  const [selectedPolicy, setSelectedPolicy] = useState<string>("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [mode, setMode] = useState<"sample" | "upload">("sample");
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingPolicies, setLoadingPolicies] = useState(true);

  useEffect(() => {
    fetchSamplePolicies()
      .then((d) => setPolicies(d.policies))
      .catch(() => {})
      .finally(() => setLoadingPolicies(false));
  }, []);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setSelectedPolicy("");
      setMode("upload");
    }
  }

  async function handleAnalyze() {
    setLoading(true);
    setResult(null);
    try {
      if (mode === "upload" && uploadedFile) {
        const data = await runComparisonWithFile(uploadedFile);
        setResult(data);
      } else if (mode === "sample" && selectedPolicy) {
        const data = await runComparison(selectedPolicy);
        setResult(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Compliance Analysis</h1>
        <p className="text-sm text-gray-500 mt-1">Compare your privacy policy against PIPEDA regulatory requirements</p>
      </div>

      {/* Policy Selection */}
      <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
        {/* Mode Tabs */}
        <div className="flex gap-1 bg-black/30 p-1 rounded-lg border border-gray-800 w-fit mb-5">
          <button
            onClick={() => setMode("upload")}
            className={`px-4 py-2 rounded text-sm font-mono flex items-center gap-2 transition-colors ${
              mode === "upload" ? "bg-green-500/15 text-green-400" : "text-gray-500 hover:text-white"
            }`}
          >
            <Upload className="w-3.5 h-3.5" /> Upload Policy
          </button>
          <button
            onClick={() => setMode("sample")}
            className={`px-4 py-2 rounded text-sm font-mono flex items-center gap-2 transition-colors ${
              mode === "sample" ? "bg-green-500/15 text-green-400" : "text-gray-500 hover:text-white"
            }`}
          >
            <FileUp className="w-3.5 h-3.5" /> Sample Policies
          </button>
        </div>

        {/* Upload Mode */}
        {mode === "upload" && (
          <div>
            <label className="block">
              <div className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                uploadedFile ? "border-green-500/40 bg-green-500/5" : "border-gray-700 hover:border-gray-600"
              }`}>
                <Upload className={`w-8 h-8 mx-auto mb-3 ${uploadedFile ? "text-green-500" : "text-gray-600"}`} />
                {uploadedFile ? (
                  <>
                    <div className="text-sm text-green-400 font-medium">{uploadedFile.name}</div>
                    <div className="text-xs text-gray-500 mt-1">{(uploadedFile.size / 1024).toFixed(1)} KB — Click to change</div>
                  </>
                ) : (
                  <>
                    <div className="text-sm text-gray-400">Drop your policy document here or click to browse</div>
                    <div className="text-xs text-gray-600 mt-1">Supports .pdf and .txt files</div>
                  </>
                )}
              </div>
              <input type="file" accept=".pdf,.txt" onChange={handleFileChange} className="hidden" />
            </label>
          </div>
        )}

        {/* Sample Mode */}
        {mode === "sample" && (
          <div>
            {loadingPolicies ? (
              <div className="flex items-center gap-2 text-gray-500 text-sm"><Loader2 className="w-4 h-4 animate-spin" /> Loading...</div>
            ) : (
              <div className="flex gap-3 flex-wrap">
                {policies.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => { setSelectedPolicy(p.id); setUploadedFile(null); }}
                    className={`px-4 py-3 rounded-lg text-sm text-left transition-all border ${
                      selectedPolicy === p.id
                        ? "bg-green-500/10 border-green-500/30 text-green-400"
                        : "bg-gray-800/50 border-gray-700 text-gray-400 hover:text-white hover:border-gray-600"
                    }`}
                  >
                    <div className="font-medium">{p.name}</div>
                    <div className="text-xs opacity-60 mt-0.5">{p.sections_count} sections | {p.filename}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <button
          onClick={handleAnalyze}
          disabled={(!selectedPolicy && !uploadedFile) || loading}
          className="mt-5 px-6 py-2.5 bg-green-500 text-black font-mono font-bold text-sm rounded-lg hover:bg-green-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Analyzing...</span>
          ) : (
            "Run Compliance Analysis"
          )}
        </button>
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Score + Stats */}
          <div className="grid grid-cols-4 gap-4">
            <ComplianceHealthScore score={result.score} />
            <StatCard
              label="Obligations Checked"
              value={result.total_obligations}
              icon={<Shield className="w-4 h-4" />}
              subtitle="PIPEDA requirements"
            />
            <StatCard
              label="Covered"
              value={result.covered}
              icon={<CheckCircle className="w-4 h-4" />}
              subtitle={`${result.score}% match rate`}
              color="text-green-400"
            />
            <StatCard
              label="Gaps Found"
              value={result.gaps}
              icon={<XCircle className="w-4 h-4" />}
              subtitle="Missing coverage"
              color="text-red-400"
            />
          </div>

          {/* Coverage by Area */}
          <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
            <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">Coverage by Operational Area</span>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
              {Object.entries(result.coverage_by_area).sort(([,a],[,b]) => a.percentage - b.percentage).map(([area, data]) => (
                <div key={area} className="p-3 bg-black/30 rounded-lg border border-gray-800">
                  <div className="text-xs font-medium text-gray-400">{AREA_LABELS[area] || area.replace(/_/g, " ")}</div>
                  <div className="flex items-end gap-2 mt-1">
                    <span className={`text-xl font-bold font-mono ${
                      data.percentage >= 75 ? "text-green-400" : data.percentage >= 50 ? "text-amber-400" : "text-red-400"
                    }`}>{data.percentage}%</span>
                    <span className="text-[10px] text-gray-600 mb-0.5">{data.covered}/{data.total}</span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-800 rounded-full mt-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        data.percentage >= 75 ? "bg-green-500" : data.percentage >= 50 ? "bg-amber-500" : "bg-red-500"
                      }`}
                      style={{ width: `${data.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ── Compliance Gaps ──────────────────────────────── */}
          <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">
                Compliance Gaps ({result.gap_details.length})
              </span>
              <span className="text-xs text-gray-600 font-mono">
                sorted by residual risk
              </span>
            </div>
            <p className="text-xs text-gray-500 mb-5">
              These PIPEDA requirements have <strong className="text-gray-300">no adequate clause</strong> in your policy.
              <span className="text-amber-400/80 ml-1">Residual risk</span> reflects how exposed your organization is
              given the severity of the obligation and the gap in coverage.
            </p>

            <div className="space-y-3 max-h-[32rem] overflow-y-auto">
              {result.gap_details.slice(0, 10).map((gap) => {
                const score = gap.coverage_score ?? gap.best_match_score ?? 0;
                const risk = gap.residual_risk || "high";
                const signal = gap.severity_signal || "mandatory";
                return (
                  <div key={gap.regulation_section_id} className="bg-black/30 border border-gray-800 rounded-lg overflow-hidden">
                    {/* Risk header bar */}
                    <div className={`px-4 py-2 flex items-center gap-3 border-b border-gray-800/50 ${
                      risk === "critical" ? "bg-red-500/10" : risk === "high" ? "bg-red-500/5" : "bg-amber-500/5"
                    }`}>
                      <AlertTriangle className={`w-3.5 h-3.5 shrink-0 ${
                        risk === "critical" ? "text-red-400" : risk === "high" ? "text-red-400/80" : "text-amber-400"
                      }`} />
                      <span className={`text-xs font-bold font-mono uppercase ${
                        risk === "critical" ? "text-red-400" : risk === "high" ? "text-red-400/80" : "text-amber-400"
                      }`}>{risk} risk</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono border ${
                        signal === "punitive" ? "bg-purple-500/15 text-purple-300 border-purple-500/30"
                        : signal === "mandatory" ? "bg-blue-500/15 text-blue-300 border-blue-500/30"
                        : "bg-gray-700/30 text-gray-400 border-gray-700/50"
                      }`}>{signal}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono border ${
                        gap.classification === "prohibition"
                          ? "bg-red-500/10 text-red-300 border-red-500/20"
                          : "bg-blue-500/10 text-blue-300 border-blue-500/20"
                      }`}>{gap.classification}</span>
                      <span className="text-[10px] text-gray-600 font-mono ml-auto">
                        nearest match: {(score * 100).toFixed(0)}%
                      </span>
                    </div>
                    {/* Content */}
                    <div className="px-4 py-3">
                      <div className="text-sm text-gray-200 font-medium">
                        {gap.regulation_title}
                      </div>
                      <div className="text-xs text-gray-500 mt-1.5 line-clamp-2 leading-relaxed">
                        {gap.regulation_body}
                      </div>
                      <div className="mt-2.5 text-[10px] text-amber-500/80 font-mono">
                        ACTION: Add a policy clause addressing this {gap.classification}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* ── Matched Sections ──────────────────────────────── */}
          <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">
                Covered Obligations ({result.covered})
              </span>
              <span className="text-xs text-gray-600 font-mono">
                sorted by match strength
              </span>
            </div>
            <p className="text-xs text-gray-500 mb-5">
              Your policy addresses these PIPEDA requirements. <span className="text-green-400/80">Match strength</span> is
              the semantic similarity between the regulation obligation and the best-matching policy clause.
            </p>

            <div className="space-y-3 max-h-[32rem] overflow-y-auto">
              {result.matches.slice(0, 10).map((match) => {
                const score = match.coverage_score ?? match.best_match_score ?? 0;
                const risk = match.residual_risk || "low";
                return (
                  <div key={match.regulation_section_id} className="bg-black/30 border border-gray-800 rounded-lg overflow-hidden">
                    {/* Match header */}
                    <div className="px-4 py-2 flex items-center gap-3 border-b border-gray-800/50 bg-green-500/5">
                      <CheckCircle className="w-3.5 h-3.5 text-green-400 shrink-0" />
                      <span className={`text-xs font-bold font-mono ${
                        score >= 0.7 ? "text-green-400" : score >= 0.55 ? "text-amber-400" : "text-gray-400"
                      }`}>{(score * 100).toFixed(0)}% match</span>
                      {risk !== "low" && (
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono border ${
                          risk === "medium" ? "bg-amber-500/15 text-amber-300 border-amber-500/30" : "bg-green-500/15 text-green-300 border-green-500/30"
                        }`}>residual: {risk}</span>
                      )}
                      <span className="text-[10px] text-gray-600 font-mono ml-auto">
                        {match.classification}
                      </span>
                    </div>
                    {/* Side-by-side regulation ↔ policy */}
                    <div className="grid grid-cols-2 divide-x divide-gray-800/50">
                      <div className="px-4 py-3">
                        <div className="text-[10px] text-gray-600 font-mono uppercase mb-1">Regulation Requirement</div>
                        <div className="text-xs text-gray-300 leading-relaxed">{match.regulation_title}</div>
                      </div>
                      <div className="px-4 py-3">
                        <div className="text-[10px] text-gray-600 font-mono uppercase mb-1">Your Policy Clause</div>
                        <div className="text-xs text-gray-300 leading-relaxed">{match.matched_policy_section || "—"}</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}

      {!result && !loading && (
        <div className="text-center py-20">
          <Shield className="w-16 h-16 text-gray-700 mx-auto mb-4" />
          <p className="text-gray-500">Select a policy document above and run the analysis</p>
          <p className="text-gray-600 text-xs mt-1">We&apos;ll compare it against PIPEDA&apos;s 61 obligations and prohibitions</p>
        </div>
      )}
    </div>
  );
}
