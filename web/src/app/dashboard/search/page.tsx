"use client";

import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import { fetchSearch } from "@/lib/api";
import type { SearchResult } from "@/lib/types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [topK, setTopK] = useState(10);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await fetchSearch(query, topK);
      setResults(data.results);
      setSearched(true);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Regulatory Search</h1>
        <p className="text-sm text-gray-500 mt-1">Semantic search across all regulatory documents</p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search regulations... e.g. 'beneficial ownership requirements'"
            className="w-full pl-10 pr-4 py-3 bg-gray-900/60 border border-gray-800 rounded-lg text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-green-500/50 focus:ring-1 focus:ring-green-500/20"
          />
        </div>
        <select
          value={topK}
          onChange={(e) => setTopK(Number(e.target.value))}
          className="bg-gray-900/60 border border-gray-800 rounded-lg px-3 text-sm text-gray-400 focus:outline-none"
        >
          <option value={5}>Top 5</option>
          <option value={10}>Top 10</option>
          <option value={20}>Top 20</option>
        </select>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="px-6 py-3 bg-green-500 text-black font-mono font-bold text-sm rounded-lg hover:bg-green-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Search"}
        </button>
      </form>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-6 h-6 animate-spin text-green-500" />
          <span className="ml-2 text-sm text-gray-400">Searching...</span>
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="text-center py-16 text-gray-500 text-sm">No results found for &ldquo;{query}&rdquo;</div>
      )}

      {!loading && results.length > 0 && (
        <div className="space-y-3">
          <div className="text-xs text-gray-500 font-mono">{results.length} results</div>
          {results.map((r, i) => (
            <div key={r.section_id} className="bg-gray-900/40 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xs font-mono text-gray-600">#{i + 1}</span>
                <div className="flex-1">
                  <span className="text-sm font-medium text-gray-200">{r.title}</span>
                  <span className="text-xs text-gray-600 ml-2 font-mono">{r.document.replace(/_/g, " ")}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full bg-green-500 rounded-full" style={{ width: `${r.score * 100}%` }} />
                  </div>
                  <span className="text-xs font-mono text-green-400">{(r.score * 100).toFixed(1)}%</span>
                </div>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed line-clamp-3">{r.body}</p>
            </div>
          ))}
        </div>
      )}

      {!searched && !loading && (
        <div className="text-center py-20">
          <Search className="w-12 h-12 text-gray-700 mx-auto mb-4" />
          <p className="text-gray-500 text-sm">Enter a query to search across all regulatory documents</p>
          <div className="mt-4 flex flex-wrap gap-2 justify-center">
            {["money laundering requirements", "data breach notification", "customer due diligence", "consent obligations"].map((q) => (
              <button
                key={q}
                onClick={() => { setQuery(q); }}
                className="px-3 py-1.5 text-xs bg-gray-800/50 border border-gray-700 rounded-full text-gray-400 hover:text-green-400 hover:border-green-500/30 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
