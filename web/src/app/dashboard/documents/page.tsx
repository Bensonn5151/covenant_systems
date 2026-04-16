"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, Loader2 } from "lucide-react";
import { fetchDocuments } from "@/lib/api";
import type { DocumentSummary, SeveritySignal } from "@/lib/types";

// A 4-segment micro-bar showing the distribution of severity signals across
// a regulation. Purely descriptive — it characterizes the LANGUAGE of the
// regulation, not risk. See CLAUDE.md §13.
const SIGNAL_ORDER: SeveritySignal[] = ["punitive", "mandatory", "procedural", "definitional"];
const SIGNAL_COLORS: Record<SeveritySignal, string> = {
  punitive: "bg-purple-500/70",
  mandatory: "bg-blue-500/70",
  procedural: "bg-gray-500/60",
  definitional: "bg-gray-700/60",
};
const SIGNAL_LABELS: Record<SeveritySignal, string> = {
  punitive: "Punitive",
  mandatory: "Mandatory",
  procedural: "Procedural",
  definitional: "Definitional",
};

function SignalBar({ breakdown }: { breakdown: Record<SeveritySignal, number> }) {
  const total = SIGNAL_ORDER.reduce((sum, s) => sum + (breakdown[s] || 0), 0);
  if (total === 0) {
    return <div className="h-1.5 bg-gray-800 rounded-full" />;
  }
  return (
    <div className="flex h-1.5 rounded-full overflow-hidden bg-gray-800">
      {SIGNAL_ORDER.map((s) => {
        const n = breakdown[s] || 0;
        if (n === 0) return null;
        const pct = (n / total) * 100;
        return (
          <div
            key={s}
            className={SIGNAL_COLORS[s]}
            style={{ width: `${pct}%` }}
            title={`${SIGNAL_LABELS[s]}: ${n}`}
          />
        );
      })}
    </div>
  );
}

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocuments()
      .then((d) => setDocs(d.documents))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-6 h-6 animate-spin text-green-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Regulations</h1>
        <p className="text-sm text-gray-500 mt-1">
          {docs.length} regulatory documents in the catalog. Risk is evaluated only when a policy is compared to a regulation —
          visit <Link href="/dashboard" className="text-green-400 hover:underline">Compliance Analysis</Link>.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {docs.map((doc) => {
          const ob = doc.classification_breakdown.obligation ?? 0;
          const pr = doc.classification_breakdown.prohibition ?? 0;
          const df = doc.classification_breakdown.definition ?? 0;
          return (
            <Link
              key={doc.document_id}
              href={`/dashboard/documents/${doc.document_id}`}
              className="bg-gray-900/40 border border-gray-800 rounded-xl p-5 hover:border-green-500/30 transition-all group"
            >
              <div className="flex items-start gap-3 mb-3">
                <FileText className="w-5 h-5 text-gray-600 mt-0.5 group-hover:text-green-500 transition-colors" />
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-200 group-hover:text-white truncate">
                    {doc.document_id.replace(/_/g, " ")}
                  </h3>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    {doc.document_type && (
                      <span className="text-[10px] px-1.5 py-0.5 bg-gray-800 text-gray-400 rounded font-mono uppercase">
                        {doc.document_type}
                      </span>
                    )}
                    <span className="text-xs text-gray-600">{doc.jurisdiction || "—"}</span>
                    {doc.regulator && (
                      <>
                        <span className="text-xs text-gray-700">·</span>
                        <span className="text-xs text-gray-600">{doc.regulator}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-4 gap-2 mt-3">
                <div className="text-center p-2 bg-black/30 rounded">
                  <div className="text-lg font-bold font-mono text-gray-300">{doc.section_count}</div>
                  <div className="text-[10px] text-gray-600">sections</div>
                </div>
                <div className="text-center p-2 bg-black/30 rounded">
                  <div className="text-lg font-bold font-mono text-blue-400">{ob}</div>
                  <div className="text-[10px] text-gray-600">obligations</div>
                </div>
                <div className="text-center p-2 bg-black/30 rounded">
                  <div className="text-lg font-bold font-mono text-purple-400">{pr}</div>
                  <div className="text-[10px] text-gray-600">prohibitions</div>
                </div>
                <div className="text-center p-2 bg-black/30 rounded">
                  <div className="text-lg font-bold font-mono text-gray-400">{df}</div>
                  <div className="text-[10px] text-gray-600">definitions</div>
                </div>
              </div>

              <div className="mt-4">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] text-gray-600 font-mono uppercase tracking-wider">
                    Language strength
                  </span>
                  {doc.last_amended && (
                    <span className="text-[10px] text-gray-600 font-mono">
                      amended {doc.last_amended}
                    </span>
                  )}
                </div>
                <SignalBar breakdown={doc.severity_signal_breakdown} />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
