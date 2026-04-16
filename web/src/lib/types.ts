export type ClassificationLabel = "obligation" | "prohibition" | "permission" | "definition" | "procedural";

// Language-strength label on the regulation text itself. Not a risk.
export type SeveritySignal = "punitive" | "mandatory" | "procedural" | "definitional";

// Risk only exists on the policy ↔ regulation mapping edge
// (see /api/compliance/coverage). See CLAUDE.md §13.
export type RiskLevel = "low" | "medium" | "high" | "critical";
export type CoverageStatus = "covered" | "partial" | "gap";

export interface DashboardStats {
  total_sections: number;
  total_documents: number;
  classifications: Record<ClassificationLabel, number>;
  severity_signals: Record<SeveritySignal, number>;
  operational_areas: Record<string, number>;
  punitive_obligations: PunitiveObligation[];
  documents: DocumentSummary[];
}

export interface PunitiveObligation {
  section_id: string;
  title: string;
  body: string;
  document: string;
  severity_signal: SeveritySignal;
  classification: ClassificationLabel;
  operational_areas: string[];
}

export interface DocumentSummary {
  document_id: string;
  document_type: string;
  jurisdiction: string;
  regulator?: string;
  category: string;
  section_count: number;
  classification_breakdown: Record<ClassificationLabel, number>;
  severity_signal_breakdown: Record<SeveritySignal, number>;
  processed_date?: string;
  last_amended?: string;
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
  severity_signal: SeveritySignal | null;
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
  severity_signal: SeveritySignal | null;
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

// ── Comparison / Coverage Types ─────────────────────────────────────────────

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
  severity_signal: SeveritySignal;
  operational_areas: string[];
  coverage_status: CoverageStatus;
  coverage_score: number;
  best_match_score: number;   // alias for coverage_score
  residual_risk: RiskLevel;
  matched_policy_section: string | null;
  matched_policy_body: string | null;
  evidence_policy_section_ids: string[];
  is_covered: boolean;
}

export interface CoverageByArea {
  total: number;
  covered: number;
  percentage: number;
}

export interface CoverageByDomain extends CoverageByArea {
  domain: string;
  coverage: number;
}

export interface ComparisonResult {
  // New coverage contract
  policy_id: string;
  regulation_id: string;
  evaluated_at: string;
  overall_coverage: number;
  by_domain: CoverageByDomain[];
  gap_details: ComparisonMatch[];
  partial_details: ComparisonMatch[];
  // Legacy fields kept for compatibility
  score: number;
  total_obligations: number;
  covered: number;
  partial: number;
  gaps: number;
  matches: ComparisonMatch[];
  coverage_by_area: Record<string, CoverageByArea>;
  threshold: number;
}
