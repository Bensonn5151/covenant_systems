"use client";

import type { HeatmapCell, RegulationSummary, RiskLevel } from "@/lib/types";

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

function cellBg(risk: RiskLevel | null | undefined): string {
  if (!risk) return "bg-gray-800/40";
  switch (risk) {
    case "critical": return "bg-red-900/60";
    case "high": return "bg-red-500/35";
    case "medium": return "bg-amber-500/30";
    case "low": return "bg-green-500/25";
    default: return "bg-gray-800/40";
  }
}

function cellText(risk: RiskLevel | null | undefined): string {
  if (!risk) return "text-gray-600";
  switch (risk) {
    case "critical": return "text-red-300";
    case "high": return "text-red-300";
    case "medium": return "text-amber-300";
    case "low": return "text-green-300";
    default: return "text-gray-500";
  }
}

function scoreBg(score: number): string {
  if (score >= 75) return "text-green-400";
  if (score >= 50) return "text-amber-400";
  return "text-red-400";
}

interface Props {
  heatmap: Record<string, Record<string, HeatmapCell>>;
  summary: Record<string, RegulationSummary>;
  regulations: string[];
  operationalAreas: string[];
  onCellClick: (regulationId: string, area: string | null) => void;
  activeCell: { regulation: string; area: string | null } | null;
}

export default function RiskHeatmap({
  heatmap,
  summary,
  regulations,
  operationalAreas,
  onCellClick,
  activeCell,
}: Props) {
  return (
    <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">
            Risk Heatmap
          </span>
          <p className="text-xs text-gray-500 mt-1">
            Residual risk by operational area and regulation. Click a cell to filter gap details.
          </p>
        </div>
        <div className="flex items-center gap-3 text-[10px] font-mono text-gray-500">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-500/25 border border-green-500/30" /> Low</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-amber-500/30 border border-amber-500/35" /> Medium</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-500/35 border border-red-500/40" /> High</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-900/60 border border-red-800/50" /> Critical</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-gray-800/40 border border-gray-700" /> N/A</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="text-left text-[10px] text-gray-600 font-mono uppercase p-2 w-36 min-w-[9rem]" />
              {regulations.map((reg) => (
                <th
                  key={reg}
                  className="text-center text-[10px] text-gray-400 font-mono uppercase p-2 min-w-[5.5rem]"
                  title={reg.replace(/_/g, " ")}
                >
                  {REGULATION_LABELS[reg] || reg.split("__").pop()?.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {operationalAreas.map((area) => (
              <tr key={area}>
                <td className="text-xs text-gray-400 font-medium p-2 border-t border-gray-800/50">
                  {AREA_LABELS[area] || area.replace(/_/g, " ")}
                </td>
                {regulations.map((reg) => {
                  const cell = heatmap[reg]?.[area];
                  const isActive =
                    activeCell?.regulation === reg && activeCell?.area === area;
                  return (
                    <td key={reg} className="p-1 border-t border-gray-800/50">
                      <button
                        onClick={() => onCellClick(reg, area)}
                        className={`w-full rounded-md p-2 text-center transition-all border ${cellBg(cell?.worst_risk)} ${
                          isActive
                            ? "ring-2 ring-green-400 border-green-500/50"
                            : "border-transparent hover:border-gray-600"
                        }`}
                        title={
                          cell
                            ? `${REGULATION_LABELS[reg] || reg} / ${AREA_LABELS[area] || area}\nCoverage: ${cell.coverage_pct}%\nGaps: ${cell.gap_count}\nObligations: ${cell.obligation_count}\nWorst risk: ${cell.worst_risk || "none"}`
                            : "No data"
                        }
                      >
                        <span className={`text-xs font-mono font-bold ${cellText(cell?.worst_risk)}`}>
                          {cell && cell.obligation_count > 0
                            ? `${Math.round(cell.coverage_pct)}%`
                            : "—"}
                        </span>
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
            {/* Summary row */}
            <tr className="border-t-2 border-gray-700">
              <td className="text-xs text-gray-300 font-bold p-2 font-mono uppercase">
                Overall
              </td>
              {regulations.map((reg) => {
                const s = summary[reg];
                const isActive = activeCell?.regulation === reg && activeCell?.area === null;
                return (
                  <td key={reg} className="p-1">
                    <button
                      onClick={() => onCellClick(reg, null)}
                      className={`w-full text-center p-2 rounded-md transition-all border ${
                        isActive
                          ? "ring-2 ring-green-400 border-green-500/50 bg-gray-800/30"
                          : "border-transparent hover:border-gray-600 hover:bg-gray-800/20"
                      }`}
                      title={`Click to see all gaps for ${REGULATION_LABELS[reg] || reg}`}
                    >
                      <span className={`text-sm font-bold font-mono ${s ? scoreBg(s.score) : "text-gray-600"}`}>
                        {s ? `${s.score}%` : "—"}
                      </span>
                      {s && s.gaps > 0 && (
                        <div className="text-[10px] text-red-400/80 mt-0.5">
                          {s.gaps} gap{s.gaps !== 1 ? "s" : ""}
                        </div>
                      )}
                    </button>
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
