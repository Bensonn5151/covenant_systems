export type ClassificationLabel = "obligation" | "prohibition" | "permission" | "definition" | "procedural";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface DashboardStats {
  total_sections: number;
  total_documents: number;
  classifications: Record<ClassificationLabel, number>;
  risk_levels: Record<RiskLevel, number>;
  operational_areas: Record<string, number>;
  compliance_health_score: number;
  high_risk_sections: HighRiskSection[];
  documents: DocumentSummary[];
}

export interface HighRiskSection {
  section_id: string;
  title: string;
  body: string;
  document: string;
  risk_level: RiskLevel;
  classification: ClassificationLabel;
  operational_areas: string[];
}

export interface DocumentSummary {
  document_id: string;
  document_type: string;
  jurisdiction: string;
  category: string;
  section_count: number;
  risk_breakdown: Record<RiskLevel, number>;
  classification_breakdown: Record<ClassificationLabel, number>;
  processed_date?: string;
}

export interface DocumentDetail {
  document_id: string;
  sections: GoldSection[];
  total_sections: number;
}

export interface GoldSection {
  section_id: string;
  section_number: string;
  title: string;
  body: string;
  level: number;
  classification: ClassificationLabel;
  classification_confidence: number;
  risk_level: RiskLevel;
  operational_areas: string[];
  document_type: string;
  jurisdiction: string;
  category: string;
}

export interface SearchResult {
  section_id: string;
  title: string;
  body: string;
  score: number;
  document: string;
}

export interface SearchResponse {
  results: SearchResult[];
  query: string;
  count: number;
}

export interface KnowledgeGraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: {
    nodes_count: number;
    edges_count: number;
    domains: Record<string, number>;
  };
  domains_config: Record<string, unknown>;
}

export interface GraphNode {
  id: string;
  type: string;
  source_document: string;
  section_number: string;
  text: string;
  domains: string[];
  risk_level: string;
}

export interface GraphEdge {
  from: string;
  to: string;
  type: string;
  description: string;
  confidence: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  documents: {
    bronze: number;
    silver: number;
    gold: number;
  };
}

export interface DocumentsListResponse {
  documents: DocumentSummary[];
  total: number;
}

// ── Comparison Types ────────────────────────────────────────────────────────

export interface SamplePolicy {
  id: string;
  name: string;
  filename: string;
  sections_count: number;
}

export interface ComparisonMatch {
  regulation_section_id: string;
  regulation_title: string;
  regulation_body: string;
  classification: ClassificationLabel;
  risk_level: RiskLevel;
  operational_areas: string[];
  best_match_score: number;
  matched_policy_section: string | null;
  matched_policy_body: string | null;
  is_covered: boolean;
}

export interface CoverageByArea {
  total: number;
  covered: number;
  percentage: number;
}

export interface ComparisonResult {
  score: number;
  total_obligations: number;
  covered: number;
  gaps: number;
  matches: ComparisonMatch[];
  gap_details: ComparisonMatch[];
  coverage_by_area: Record<string, CoverageByArea>;
  regulation_id: string;
  threshold: number;
}
