import type { PunitiveObligation } from "@/lib/types";
import SeverityBadge from "@/components/shared/SeverityBadge";
import ClassificationBadge from "@/components/shared/ClassificationBadge";

interface Props {
  items: PunitiveObligation[];
}

export default function PriorityActions({ items }: Props) {
  return (
    <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
      <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">Punitive Obligations</span>
      <p className="text-xs text-gray-600 mt-1 mb-4">
        Obligations and prohibitions with the strongest enforcement language.
        Run a compliance analysis to see which ones your policy covers.
      </p>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {items.slice(0, 10).map((item) => (
          <div key={item.section_id} className="p-3 bg-black/30 border border-gray-800 rounded-lg hover:border-gray-700 transition-colors">
            <div className="flex items-center gap-2 mb-1.5">
              <SeverityBadge signal={item.severity_signal} />
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
