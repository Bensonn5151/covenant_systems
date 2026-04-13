"use client";

import { useEffect, useState } from "react";
import { Shield, AlertTriangle, CheckCircle, XCircle, FileUp, Upload, Loader2 } from "lucide-react";
import { fetchSamplePolicies, runComparison, runComparisonWithFile } from "@/lib/api";
import type { SamplePolicy, ComparisonResult } from "@/lib/types";
import StatCard from "@/components/shared/StatCard";
import ComplianceHealthScore from "@/components/dashboard/ComplianceHealthScore";
import RiskBadge from "@/components/shared/RiskBadge";
import ClassificationBadge from "@/components/shared/ClassificationBadge";
import Link from "next/link";

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

          {/* Top Gaps */}
          <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">Compliance Gaps ({result.gaps})</span>
              <Link href="/dashboard/gaps" className="text-xs text-green-500 hover:text-green-400">View all</Link>
            </div>
            <p className="text-xs text-gray-600 mb-4">PIPEDA requirements not adequately addressed by your policy</p>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {result.gap_details.slice(0, 10).map((gap) => (
                <div key={gap.regulation_section_id} className="p-3 bg-black/30 border border-gray-800 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <XCircle className="w-3.5 h-3.5 text-red-400" />
                    <RiskBadge level={gap.risk_level} />
                    <ClassificationBadge label={gap.classification} />
                    <span className="text-xs text-gray-600 ml-auto font-mono">score: {(gap.best_match_score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="text-sm text-gray-300">{gap.regulation_title}</div>
                  <div className="text-xs text-gray-500 mt-1 line-clamp-2">{gap.regulation_body}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Matched Sections */}
          <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
            <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">Matched Sections ({result.covered})</span>
            <p className="text-xs text-gray-600 mt-1 mb-4">Policy sections that cover regulatory requirements</p>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {result.matches.slice(0, 10).map((match) => (
                <div key={match.regulation_section_id} className="p-3 bg-black/30 border border-gray-800 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                    <RiskBadge level={match.risk_level} />
                    <span className="text-xs text-green-400 font-mono ml-auto">{(match.best_match_score * 100).toFixed(0)}% match</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 mt-2">
                    <div>
                      <div className="text-[10px] text-gray-600 font-mono uppercase mb-1">Regulation</div>
                      <div className="text-xs text-gray-400">{match.regulation_title}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-gray-600 font-mono uppercase mb-1">Your Policy</div>
                      <div className="text-xs text-gray-400">{match.matched_policy_section}</div>
                    </div>
                  </div>
                </div>
              ))}
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
