import type { ClassificationLabel } from "@/lib/types";

const colors: Record<ClassificationLabel, string> = {
  obligation: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  prohibition: "bg-red-500/15 text-red-400 border-red-500/30",
  permission: "bg-green-500/15 text-green-400 border-green-500/30",
  definition: "bg-purple-500/15 text-purple-400 border-purple-500/30",
  procedural: "bg-gray-500/15 text-gray-400 border-gray-500/30",
};

export default function ClassificationBadge({ label }: { label: ClassificationLabel }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono border ${colors[label] || colors.procedural}`}>
      {label}
    </span>
  );
}
