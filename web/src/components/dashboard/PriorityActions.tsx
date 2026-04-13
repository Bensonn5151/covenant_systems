import type { HighRiskSection } from "@/lib/types";
import RiskBadge from "@/components/shared/RiskBadge";
import ClassificationBadge from "@/components/shared/ClassificationBadge";

interface Props {
  items: HighRiskSection[];
}

export default function PriorityActions({ items }: Props) {
  return (
    <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
      <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">Priority Actions</span>
      <p className="text-xs text-gray-600 mt-1 mb-4">High-risk regulatory sections requiring attention</p>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {items.slice(0, 10).map((item) => (
          <div key={item.section_id} className="p-3 bg-black/30 border border-gray-800 rounded-lg hover:border-gray-700 transition-colors">
            <div className="flex items-center gap-2 mb-1.5">
              <RiskBadge level={item.risk_level} />
              <ClassificationBadge label={item.classification} />
              <span className="text-xs text-gray-600 ml-auto font-mono">{item.document}</span>
            </div>
            <div className="text-sm text-gray-300 font-medium">{item.title}</div>
            <div className="text-xs text-gray-500 mt-1 line-clamp-2">{item.body}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
