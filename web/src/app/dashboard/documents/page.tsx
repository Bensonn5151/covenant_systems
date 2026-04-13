"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, Loader2, AlertTriangle } from "lucide-react";
import { fetchDocuments } from "@/lib/api";
import type { DocumentSummary } from "@/lib/types";
import RiskBadge from "@/components/shared/RiskBadge";

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
        <h1 className="text-2xl font-bold text-white">Documents</h1>
        <p className="text-sm text-gray-500 mt-1">{docs.length} regulatory documents ingested</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {docs.map((doc) => {
          const highRisk = doc.risk_breakdown.high + (doc.risk_breakdown.critical || 0);
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
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-600 capitalize">{doc.category}</span>
                    <span className="text-xs text-gray-700">|</span>
                    <span className="text-xs text-gray-600">{doc.jurisdiction}</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 mt-3">
                <div className="text-center p-2 bg-black/30 rounded">
                  <div className="text-lg font-bold font-mono text-gray-300">{doc.section_count}</div>
                  <div className="text-[10px] text-gray-600">sections</div>
                </div>
                <div className="text-center p-2 bg-black/30 rounded">
                  <div className="text-lg font-bold font-mono text-blue-400">{doc.classification_breakdown.obligation}</div>
                  <div className="text-[10px] text-gray-600">obligations</div>
                </div>
                <div className="text-center p-2 bg-black/30 rounded">
                  <div className={`text-lg font-bold font-mono ${highRisk > 0 ? "text-red-400" : "text-green-400"}`}>{highRisk}</div>
                  <div className="text-[10px] text-gray-600">high risk</div>
                </div>
              </div>

              {highRisk > 0 && (
                <div className="flex items-center gap-1.5 mt-3">
                  <AlertTriangle className="w-3 h-3 text-amber-500" />
                  <span className="text-xs text-amber-500">{highRisk} sections need review</span>
                </div>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
