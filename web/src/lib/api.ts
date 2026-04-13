import type {
  DashboardStats,
  DocumentsListResponse,
  DocumentDetail,
  SearchResponse,
  KnowledgeGraphData,
  HealthResponse,
  SamplePolicy,
  ComparisonResult,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  return fetchAPI("/api/dashboard/stats");
}

export async function fetchDocuments(): Promise<DocumentsListResponse> {
  return fetchAPI("/api/dashboard/documents");
}

export async function fetchDocument(id: string): Promise<DocumentDetail> {
  return fetchAPI(`/api/dashboard/documents/${encodeURIComponent(id)}`);
}

export async function fetchSearch(query: string, topK = 10, category?: string): Promise<SearchResponse> {
  const params = new URLSearchParams({ query, top_k: String(topK) });
  if (category) params.set("category", category);
  return fetchAPI(`/search?${params}`);
}

export async function fetchKnowledgeGraph(): Promise<KnowledgeGraphData> {
  return fetchAPI("/api/knowledge-graph");
}

export async function fetchHealth(): Promise<HealthResponse> {
  return fetchAPI("/health");
}

export async function fetchSamplePolicies(): Promise<{ policies: SamplePolicy[] }> {
  return fetchAPI("/api/sample-policies");
}

export async function runComparison(samplePolicyId: string, regulationId = "pipeda"): Promise<ComparisonResult> {
  return fetchAPI("/api/compare", {
    method: "POST",
    body: JSON.stringify({ sample_policy_id: samplePolicyId, regulation_id: regulationId }),
  });
}

export async function runComparisonWithText(policyText: string, regulationId = "pipeda"): Promise<ComparisonResult> {
  return fetchAPI("/api/compare", {
    method: "POST",
    body: JSON.stringify({ policy_text: policyText, regulation_id: regulationId }),
  });
}

export async function runComparisonWithFile(file: File, regulationId = "pipeda"): Promise<ComparisonResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("regulation_id", regulationId);
  const res = await fetch(`${API_URL}/api/compare-upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}
