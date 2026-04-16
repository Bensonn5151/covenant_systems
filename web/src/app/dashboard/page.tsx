"use client";

import { useEffect, useState, useMemo } from "react";
import { Shield, CheckCircle, XCircle, AlertTriangle, FileUp, Upload, Loader2, X } from "lucide-react";
import { fetchSamplePolicies, runMultiComparison, runMultiComparisonWithFile } from "@/lib/api";
import type { SamplePolicy, MultiComparisonResult, ComparisonMatch } from "@/lib/types";
import StatCard from "@/components/shared/StatCard";
import ComplianceHealthScore from "@/components/dashboard/ComplianceHealthScore";
import RiskHeatmap from "@/components/dashboard/RiskHeatmap";

const REGULATION_LABELS: Record<string, string> = {
  pipeda: "PIPEDA",
  privacy_act: "Privacy Act",
  sor_2018_64_breach_of_security_safeguards_regulations: "Breach Regs",
  sor_2001_7_pipeda_regulations: "PIPEDA Regs",
  opc__guidelines_for_obtaining_meaningful_consent: "Consent Guide",
  opc__breach_of_security_safeguards_reporting: "Breach Report",
  opc__inappropriate_data_practices: "Data Practices",
  opc__privacy_and_ai: "AI Guidance",
  opc__ten_fair_information_principles: "10 Principles",
};

const AREA_LABELS: Record<string, string> = {
  data_collection: "Data Collection",
  consent: "Consent",
  data_use: "Data Use",
  data_disclosure: "Data Disclosure",
  data_retention: "Data Retention",
  breach_notification: "Breach Notification",
  access_rights: "Access Rights",
  accountability: "Accountability",
};

export default function DashboardOverview() {
  const [policies, setPolicies] = useState<SamplePolicy[]>([]);
  const [selectedPolicy, setSelectedPolicy] = useState<string>("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [mode, setMode] = useState<"sample" | "upload">("sample");
  const [result, setResult] = useState<MultiComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingPolicies, setLoadingPolicies] = useState(true);
  // area can be null to mean "all areas for this regulation" (clicked the summary row)
  const [activeCell, setActiveCell] = useState<{ regulation: string; area: string | null } | null>(null);

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
    setActiveCell(null);
    try {
      if (mode === "upload" && uploadedFile) {
        setResult(await runMultiComparisonWithFile(uploadedFile));
      } else if (mode === "sample" && selectedPolicy) {
        setResult(await runMultiComparison(selectedPolicy));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  // Aggregate stats from multi-regulation result
  const stats = useMemo(() => {
    if (!result) return null;
    const regs = result.regulations.length;
    const scores = Object.values(result.summary).map((s) => s.score);
    const avgCoverage = scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length * 10) / 10 : 0;
    const totalGaps = Object.values(result.summary).reduce((a, s) => a + s.gaps, 0);
    const criticalCells = Object.values(result.heatmap).reduce(
      (acc, areas) => acc + Object.values(areas).filter((c) => c.worst_risk === "critical").length, 0,
    );
    return { regs, avgCoverage, totalGaps, criticalCells };
  }, [result]);

  // Filtered gap/match details based on active heatmap cell
  const filteredGaps = useMemo(() => {
    if (!result) return [];
    if (!activeCell) {
      // All gaps across all regulations, sorted by risk
      const riskOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
      const all: (ComparisonMatch & { _reg: string })[] = [];
      for (const reg of result.regulations) {
        const d = result.details[reg];
        if (d?.gap_details) {
          for (const g of d.gap_details) {
            all.push({ ...g, _reg: reg });
          }
        }
      }
      all.sort((a, b) => (riskOrder[a.residual_risk] ?? 3) - (riskOrder[b.residual_risk] ?? 3));
      return all;
    }
    const d = result.details[activeCell.regulation];
    if (!d?.gap_details) return [];
    // area === null means "all gaps for this regulation" (clicked summary row)
    if (!activeCell.area) {
      return d.gap_details.map((g) => ({ ...g, _reg: activeCell.regulation }));
    }
    // Strict area match — only gaps tagged with this specific area
    return d.gap_details
      .filter((g) => (g.operational_areas || []).includes(activeCell.area!))
      .map((g) => ({ ...g, _reg: activeCell.regulation }));
  }, [result, activeCell]);

  const filteredMatches = useMemo(() => {
    if (!result) return [];
    if (!activeCell) {
      const all: (ComparisonMatch & { _reg: string })[] = [];
      for (const reg of result.regulations) {
        const d = result.details[reg];
        if (d?.matches) {
          for (const m of d.matches) {
            all.push({ ...m, _reg: reg });
          }
        }
      }
      all.sort((a, b) => (b.coverage_score ?? b.best_match_score ?? 0) - (a.coverage_score ?? a.best_match_score ?? 0));
      return all;
    }
    const d = result.details[activeCell.regulation];
    if (!d?.matches) return [];
    if (!activeCell.area) {
      return d.matches.map((m) => ({ ...m, _reg: activeCell.regulation }));
    }
    return d.matches
      .filter((m) => (m.operational_areas || []).includes(activeCell.area!))
      .map((m) => ({ ...m, _reg: activeCell.regulation }));
  }, [result, activeCell]);

  const filterLabel = activeCell
    ? activeCell.area
      ? `${REGULATION_LABELS[activeCell.regulation] || activeCell.regulation} / ${AREA_LABELS[activeCell.area] || activeCell.area}`
      : REGULATION_LABELS[activeCell.regulation] || activeCell.regulation
    : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Compliance Analysis</h1>
        <p className="text-sm text-gray-500 mt-1">
          Assess your policy against {result ? result.regulations.length : "all"} Canadian privacy regulations
        </p>
      </div>

      {/* Policy Selection */}
      <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
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

        {mode === "upload" && (
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
        )}

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
            <span className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Analyzing {result ? "" : "all regulations"}...
            </span>
          ) : (
            "Run Compliance Analysis"
          )}
        </button>
      </div>

      {/* Results */}
      {result && stats && (
        <>
          {/* Score cards */}
          <div className="grid grid-cols-4 gap-4">
            <ComplianceHealthScore score={stats.avgCoverage} />
            <StatCard
              label="Regulations Analyzed"
              value={stats.regs}
              icon={<Shield className="w-4 h-4" />}
              subtitle="Canadian privacy corpus"
            />
            <StatCard
              label="Total Gaps"
              value={stats.totalGaps}
              icon={<XCircle className="w-4 h-4" />}
              subtitle="across all regulations"
              color="text-red-400"
            />
            <StatCard
              label="Critical Exposures"
              value={stats.criticalCells}
              icon={<AlertTriangle className="w-4 h-4" />}
              subtitle="heatmap cells at critical"
              color={stats.criticalCells > 0 ? "text-red-400" : "text-green-400"}
            />
          </div>

          {/* Heatmap */}
          <RiskHeatmap
            heatmap={result.heatmap}
            summary={result.summary}
            regulations={result.regulations}
            operationalAreas={result.operational_areas}
            onCellClick={(reg, area) => {
              if (activeCell?.regulation === reg && activeCell?.area === area) {
                setActiveCell(null);
              } else {
                setActiveCell({ regulation: reg, area });
              }
            }}
            activeCell={activeCell}
          />

          {/* Filter indicator */}
          {filterLabel && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 font-mono">Filtered to:</span>
              <span className="text-xs text-green-400 font-mono bg-green-500/10 px-2 py-1 rounded border border-green-500/20">
                {filterLabel}
              </span>
              <button
                onClick={() => setActiveCell(null)}
                className="text-xs text-gray-500 hover:text-white flex items-center gap-1 font-mono"
              >
                <X className="w-3 h-3" /> Clear
              </button>
            </div>
          )}

          {/* Gaps */}
          <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">
                {filterLabel ? `Gaps: ${filterLabel}` : "All Compliance Gaps"} ({filteredGaps.length})
              </span>
              <span className="text-xs text-gray-600 font-mono">sorted by residual risk</span>
            </div>
            <p className="text-xs text-gray-500 mb-5">
              Regulatory requirements <strong className="text-gray-300">not adequately addressed</strong> by your policy.
            </p>

            {filteredGaps.length === 0 ? (
              <div className="text-center py-8 text-gray-600 text-sm">
                {filterLabel ? "No gaps in this area." : "No gaps found."}
              </div>
            ) : (
              <div className="space-y-3 max-h-[32rem] overflow-y-auto">
                {filteredGaps.slice(0, 20).map((gap, idx) => {
                  const score = gap.coverage_score ?? gap.best_match_score ?? 0;
                  const risk = gap.residual_risk || "high";
                  const signal = gap.severity_signal || "mandatory";
                  const regLabel = REGULATION_LABELS[(gap as { _reg: string })._reg] || (gap as { _reg: string })._reg;
                  return (
                    <div key={`${(gap as { _reg: string })._reg}-${gap.regulation_section_id}-${idx}`} className="bg-black/30 border border-gray-800 rounded-lg overflow-hidden">
                      <div className={`px-4 py-2 flex items-center gap-3 border-b border-gray-800/50 flex-wrap ${
                        risk === "critical" ? "bg-red-500/10" : risk === "high" ? "bg-red-500/5" : "bg-amber-500/5"
                      }`}>
                        <AlertTriangle className={`w-3.5 h-3.5 shrink-0 ${
                          risk === "critical" ? "text-red-400" : risk === "high" ? "text-red-400/80" : "text-amber-400"
                        }`} />
                        <span className={`text-xs font-bold font-mono uppercase ${
                          risk === "critical" ? "text-red-400" : risk === "high" ? "text-red-400/80" : "text-amber-400"
                        }`}>{risk}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded font-mono border bg-gray-800/50 text-gray-400 border-gray-700">{regLabel}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono border ${
                          signal === "punitive" ? "bg-purple-500/15 text-purple-300 border-purple-500/30"
                          : "bg-blue-500/15 text-blue-300 border-blue-500/30"
                        }`}>{signal}</span>
                        <span className="text-[10px] text-gray-600 font-mono ml-auto">
                          nearest: {(score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="px-4 py-3">
                        <div className="text-sm text-gray-200 font-medium">{gap.regulation_title}</div>
                        {gap.matched_policy_body && (
                          <div className="text-xs text-amber-400/90 mt-1.5 leading-relaxed">
                            {gap.matched_policy_body}
                          </div>
                        )}
                        <div className="text-xs text-gray-500 mt-1.5 line-clamp-2 leading-relaxed">{gap.regulation_body}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Matches */}
          <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">
                {filterLabel ? `Covered: ${filterLabel}` : "Covered Obligations"} ({filteredMatches.length})
              </span>
              <span className="text-xs text-gray-600 font-mono">sorted by match strength</span>
            </div>
            <p className="text-xs text-gray-500 mb-5">
              Your policy addresses these regulatory requirements.
            </p>

            {filteredMatches.length === 0 ? (
              <div className="text-center py-8 text-gray-600 text-sm">
                {filterLabel ? "No covered obligations in this area." : "No matches found."}
              </div>
            ) : (
              <div className="space-y-3 max-h-[32rem] overflow-y-auto">
                {filteredMatches.slice(0, 20).map((match, idx) => {
                  const score = match.coverage_score ?? match.best_match_score ?? 0;
                  const regLabel = REGULATION_LABELS[(match as { _reg: string })._reg] || (match as { _reg: string })._reg;
                  return (
                    <div key={`${(match as { _reg: string })._reg}-${match.regulation_section_id}-${idx}`} className="bg-black/30 border border-gray-800 rounded-lg overflow-hidden">
                      <div className="px-4 py-2 flex items-center gap-3 border-b border-gray-800/50 bg-green-500/5 flex-wrap">
                        <CheckCircle className="w-3.5 h-3.5 text-green-400 shrink-0" />
                        <span className={`text-xs font-bold font-mono ${
                          score >= 0.7 ? "text-green-400" : score >= 0.55 ? "text-amber-400" : "text-gray-400"
                        }`}>{(score * 100).toFixed(0)}% match</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded font-mono border bg-gray-800/50 text-gray-400 border-gray-700">{regLabel}</span>
                        <span className="text-[10px] text-gray-600 font-mono ml-auto">{match.classification}</span>
                      </div>
                      <div className="px-4 py-3 space-y-2">
                        <div>
                          <div className="text-[10px] text-gray-600 font-mono uppercase mb-1">Regulation Requirement</div>
                          <div className="text-xs text-gray-300 leading-relaxed">{match.regulation_title}</div>
                        </div>
                        {match.matched_policy_section && (
                          <div>
                            <div className="text-[10px] text-gray-600 font-mono uppercase mb-1">Matched Policy Clause</div>
                            <div className="text-xs text-green-300/90 leading-relaxed">{match.matched_policy_section}</div>
                          </div>
                        )}
                        {match.matched_policy_body && (
                          <div>
                            <div className="text-[10px] text-gray-600 font-mono uppercase mb-1">Reasoning</div>
                            <div className="text-xs text-gray-400 leading-relaxed">{match.matched_policy_body}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}

      {!result && !loading && (
        <div className="text-center py-20">
          <Shield className="w-16 h-16 text-gray-700 mx-auto mb-4" />
          <p className="text-gray-500">Select a policy document above and run the analysis</p>
          <p className="text-gray-600 text-xs mt-1">Your policy will be assessed against all 9 Canadian privacy regulations</p>
        </div>
      )}
    </div>
  );
}
