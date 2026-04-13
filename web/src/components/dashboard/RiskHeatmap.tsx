"use client";

interface Props {
  data: Record<string, number>;
}

function getColor(count: number, max: number) {
  const ratio = count / max;
  if (ratio > 0.6) return "bg-red-500/30 border-red-500/40 text-red-400";
  if (ratio > 0.3) return "bg-amber-500/20 border-amber-500/30 text-amber-400";
  return "bg-green-500/15 border-green-500/25 text-green-400";
}

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

export default function RiskHeatmap({ data }: Props) {
  const max = Math.max(...Object.values(data), 1);
  const sorted = Object.entries(data).sort(([, a], [, b]) => b - a);

  return (
    <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
      <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">Risk by Operational Area</span>
      <div className="grid grid-cols-2 gap-2 mt-4">
        {sorted.map(([area, count]) => (
          <div
            key={area}
            className={`p-3 rounded-lg border ${getColor(count, max)} transition-colors`}
          >
            <div className="text-xs font-medium">{AREA_LABELS[area] || area.replace(/_/g, " ")}</div>
            <div className="text-lg font-bold font-mono mt-1">{count}</div>
            <div className="text-[10px] opacity-60">sections flagged</div>
          </div>
        ))}
      </div>
    </div>
  );
}
