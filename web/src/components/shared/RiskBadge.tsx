import type { RiskLevel } from "@/lib/types";

const colors: Record<RiskLevel, string> = {
  critical: "bg-red-500/20 text-red-400 border-red-500/40",
  high: "bg-red-500/15 text-red-400 border-red-500/30",
  medium: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  low: "bg-green-500/15 text-green-400 border-green-500/30",
};

export default function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono border ${colors[level] || colors.low}`}>
      {level}
    </span>
  );
}
