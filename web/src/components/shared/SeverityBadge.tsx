import type { SeveritySignal } from "@/lib/types";

// Language-strength indicator on a regulation obligation/prohibition.
// This is NOT a risk rating — see CLAUDE.md §13.
const colors: Record<SeveritySignal, string> = {
  punitive:     "bg-purple-500/15 text-purple-300 border-purple-500/30",
  mandatory:    "bg-blue-500/15   text-blue-300   border-blue-500/30",
  procedural:   "bg-gray-500/15   text-gray-300   border-gray-500/30",
  definitional: "bg-gray-700/30   text-gray-400   border-gray-700/50",
};

export default function SeverityBadge({ signal }: { signal: SeveritySignal | null | undefined }) {
  if (!signal) return null;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono border ${colors[signal] || colors.mandatory}`}
      title="Language strength of the regulation text (not a risk rating)"
    >
      {signal}
    </span>
  );
}
