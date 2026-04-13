"use client";

import { useEffect, useState } from "react";
import { Loader2, GitBranch, Filter } from "lucide-react";
import { fetchKnowledgeGraph } from "@/lib/api";
import type { KnowledgeGraphData, GraphNode, GraphEdge } from "@/lib/types";
import StatCard from "@/components/shared/StatCard";

export default function KnowledgeGraphPage() {
  const [data, setData] = useState<KnowledgeGraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"nodes" | "edges">("nodes");
  const [domainFilter, setDomainFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");

  useEffect(() => {
    fetchKnowledgeGraph()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-6 h-6 animate-spin text-green-500" />
      </div>
    );
  }

  const domains = Object.entries(data.stats.domains).sort(([, a], [, b]) => b - a);
  const edgeTypes = [...new Set(data.edges.map((e) => e.type))];

  const filteredNodes = data.nodes.filter((n) => {
    if (domainFilter && !n.domains.includes(domainFilter)) return false;
    return true;
  });

  const filteredEdges = data.edges.filter((e) => {
    if (typeFilter && e.type !== typeFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Knowledge Graph</h1>
        <p className="text-sm text-gray-500 mt-1">Regulatory relationship mapping</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Nodes" value={data.stats.nodes_count} icon={<GitBranch className="w-4 h-4" />} />
        <StatCard label="Edges" value={data.stats.edges_count} icon={<GitBranch className="w-4 h-4" />} color="text-purple-400" />
        <StatCard label="Domains" value={Object.keys(data.stats.domains).length} color="text-blue-400" />
        <StatCard label="Edge Types" value={edgeTypes.length} color="text-amber-400" />
      </div>

      {/* Domain breakdown */}
      <div className="bg-gray-900/40 border border-gray-800 rounded-xl p-6">
        <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">Domain Distribution</span>
        <div className="flex gap-3 mt-4 flex-wrap">
          {domains.map(([domain, count]) => (
            <button
              key={domain}
              onClick={() => setDomainFilter(domainFilter === domain ? "" : domain)}
              className={`px-4 py-2 rounded-lg text-sm font-mono transition-colors border ${
                domainFilter === domain
                  ? "bg-green-500/15 border-green-500/30 text-green-400"
                  : "bg-gray-800/50 border-gray-700 text-gray-400 hover:text-white"
              }`}
            >
              {domain} <span className="text-xs opacity-60">({count})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900/40 p-1 rounded-lg border border-gray-800 w-fit">
        <button
          onClick={() => setTab("nodes")}
          className={`px-4 py-2 rounded text-sm font-mono transition-colors ${
            tab === "nodes" ? "bg-green-500/15 text-green-400" : "text-gray-500 hover:text-white"
          }`}
        >
          Nodes ({filteredNodes.length})
        </button>
        <button
          onClick={() => setTab("edges")}
          className={`px-4 py-2 rounded text-sm font-mono transition-colors ${
            tab === "edges" ? "bg-green-500/15 text-green-400" : "text-gray-500 hover:text-white"
          }`}
        >
          Edges ({filteredEdges.length})
        </button>
      </div>

      {/* Edge type filter */}
      {tab === "edges" && (
        <div className="flex gap-2 flex-wrap">
          <Filter className="w-4 h-4 text-gray-600 mt-1" />
          {edgeTypes.map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(typeFilter === t ? "" : t)}
              className={`px-3 py-1 rounded text-xs font-mono transition-colors border ${
                typeFilter === t
                  ? "bg-purple-500/15 border-purple-500/30 text-purple-400"
                  : "bg-gray-800/50 border-gray-700 text-gray-500 hover:text-white"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      )}

      {/* Table */}
      <div className="bg-gray-900/40 border border-gray-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
          {tab === "nodes" ? (
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-gray-900">
                <tr className="text-xs text-gray-500 font-mono uppercase border-b border-gray-800">
                  <th className="text-left p-3">ID</th>
                  <th className="text-left p-3">Document</th>
                  <th className="text-left p-3">Section</th>
                  <th className="text-left p-3">Domains</th>
                  <th className="text-left p-3">Text</th>
                </tr>
              </thead>
              <tbody>
                {filteredNodes.slice(0, 100).map((n) => (
                  <tr key={n.id} className="border-b border-gray-800/50 hover:bg-gray-800/20">
                    <td className="p-3 font-mono text-xs text-green-400">{n.id}</td>
                    <td className="p-3 text-gray-400">{n.source_document}</td>
                    <td className="p-3 text-gray-500 font-mono">{n.section_number}</td>
                    <td className="p-3">
                      <div className="flex gap-1">
                        {n.domains.map((d) => (
                          <span key={d} className="px-1.5 py-0.5 text-[10px] bg-blue-500/10 text-blue-400 rounded">{d}</span>
                        ))}
                      </div>
                    </td>
                    <td className="p-3 text-gray-500 text-xs max-w-xs truncate">{n.text}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-gray-900">
                <tr className="text-xs text-gray-500 font-mono uppercase border-b border-gray-800">
                  <th className="text-left p-3">From</th>
                  <th className="text-left p-3">To</th>
                  <th className="text-left p-3">Type</th>
                  <th className="text-left p-3">Confidence</th>
                  <th className="text-left p-3">Description</th>
                </tr>
              </thead>
              <tbody>
                {filteredEdges.slice(0, 100).map((e, i) => (
                  <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/20">
                    <td className="p-3 font-mono text-xs text-green-400">{e.from}</td>
                    <td className="p-3 font-mono text-xs text-purple-400">{e.to}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 text-xs bg-amber-500/10 text-amber-400 rounded font-mono">{e.type}</span>
                    </td>
                    <td className="p-3 font-mono text-xs text-gray-400">{(e.confidence * 100).toFixed(0)}%</td>
                    <td className="p-3 text-gray-500 text-xs max-w-xs truncate">{e.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
