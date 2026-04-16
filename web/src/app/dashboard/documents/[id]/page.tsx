"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeft, Loader2, ChevronDown, ChevronRight } from "lucide-react";
import Link from "next/link";
import { fetchDocument } from "@/lib/api";
import type { GoldSection } from "@/lib/types";
import ClassificationBadge from "@/components/shared/ClassificationBadge";
import SeverityBadge from "@/components/shared/SeverityBadge";

export default function DocumentDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [sections, setSections] = useState<GoldSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState("");

  useEffect(() => {
    fetchDocument(id)
      .then((d) => setSections(d.sections))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  const toggle = (sectionId: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(sectionId)) next.delete(sectionId);
      else next.add(sectionId);
      return next;
    });
  };

  const filtered = filter
    ? sections.filter((s) =>
        s.title.toLowerCase().includes(filter.toLowerCase()) ||
        s.body.toLowerCase().includes(filter.toLowerCase()) ||
        s.classification.includes(filter.toLowerCase())
      )
    : sections;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-6 h-6 animate-spin text-green-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/dashboard/documents" className="text-gray-500 hover:text-white transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white">{id.replace(/_/g, " ")}</h1>
          <p className="text-sm text-gray-500">{sections.length} sections</p>
        </div>
      </div>

      <input
        type="text"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter sections..."
        className="w-full px-4 py-2.5 bg-gray-900/60 border border-gray-800 rounded-lg text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-green-500/50"
      />

      <div className="text-xs text-gray-500 font-mono">{filtered.length} sections shown</div>

      <div className="space-y-2">
        {filtered.map((s) => (
          <div key={s.section_id} className="bg-gray-900/40 border border-gray-800 rounded-lg overflow-hidden">
            <button
              onClick={() => toggle(s.section_id)}
              className="w-full flex items-center gap-3 p-4 text-left hover:bg-gray-800/30 transition-colors"
            >
              {expanded.has(s.section_id) ? (
                <ChevronDown className="w-4 h-4 text-gray-500 shrink-0" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-500 shrink-0" />
              )}
              <span className="text-xs text-gray-600 font-mono w-10 shrink-0">{s.section_number}</span>
              <span className="text-sm text-gray-300 flex-1 truncate">{s.title}</span>
              <div className="flex items-center gap-2 shrink-0">
                <ClassificationBadge label={s.classification} />
                <SeverityBadge signal={s.severity_signal} />
              </div>
            </button>
            {expanded.has(s.section_id) && (
              <div className="px-4 pb-4 pl-14 border-t border-gray-800/50">
                <p className="text-sm text-gray-400 leading-relaxed mt-3 whitespace-pre-wrap">{s.body}</p>
                {s.operational_areas.length > 0 && (
                  <div className="flex gap-1.5 mt-3 flex-wrap">
                    {s.operational_areas.map((area) => (
                      <span key={area} className="px-2 py-0.5 text-[10px] bg-gray-800 text-gray-500 rounded font-mono">
                        {area.replace(/_/g, " ")}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
