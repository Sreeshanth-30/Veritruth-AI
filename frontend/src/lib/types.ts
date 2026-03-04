/* ──────────────────────────────────────────────────────────── */
/*  VeriTruth AI — TypeScript Type Definitions                 */
/* ──────────────────────────────────────────────────────────── */

// ── Auth ──────────────────────────────────────────────────────
export type UserRole = "student" | "educator" | "researcher" | "journalist" | "admin";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  role: UserRole;
  avatar_url?: string;
  institution?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  analysis_count_today?: number;
}

export interface AuthResponse {
  user: User;
  tokens: {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
  };
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role?: UserRole;
  institution?: string;
}

// ── Analysis ─────────────────────────────────────────────────
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type AnalysisStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface ClaimVerification {
  claim_text: string;
  verdict: "SUPPORTED" | "REFUTED" | "PARTIALLY_SUPPORTED" | "UNVERIFIABLE";
  confidence: number;
  evidence: string;
  sources: EvidenceSource[];
}

export interface EvidenceSource {
  title: string;
  url: string;
  publisher: string;
  credibility_score: number;
}

export interface SuspiciousPassage {
  text: string;
  score: number;
  reason: string;
}

export interface PropagandaTechnique {
  technique: string;
  confidence: number;
  instances: string[];
}

export interface SentimentBreakdown {
  overall_sentiment: string;
  sentiment_score: number;
  emotions: Record<string, number>;
  manipulation_score: number;
  manipulation_flags: string[];
}

export interface DeepfakeResult {
  is_deepfake: boolean;
  confidence: number;
  analysis_details: Record<string, unknown>;
}

export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: string;
  color: string;
}

export interface KnowledgeGraphEdge {
  source: string;
  target: string;
  label: string;
}

export interface KnowledgeGraphData {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  conflicts: number;
  verified: number;
}

export interface ExplainabilityData {
  tokens: { token: string; shap_value: number }[];
  top_features: { feature: string; importance: number }[];
}

export interface AnalysisResult {
  id: string;
  user_id: string;
  status: AnalysisStatus;
  input_type: string;
  title?: string;
  source_url?: string;
  author?: string;
  risk_level: RiskLevel;
  fake_probability: number;
  confidence_score: number;
  classification_label: string;
  propaganda_score: number;
  credibility_score: number;
  bias_score: number;
  claim_count: number;
  verified_true_count: number;
  verified_false_count: number;
  detected_claims: ClaimVerification[];
  fact_verification_results: ClaimVerification[];
  propaganda_techniques: PropagandaTechnique[];
  sentiment_breakdown: SentimentBreakdown;
  suspicious_passages: SuspiciousPassage[];
  evidence_references: EvidenceSource[];
  explainability_data: ExplainabilityData;
  knowledge_graph_data: KnowledgeGraphData;
  created_at: string;
  completed_at?: string;
}

export interface AnalysisListItem {
  id: string;
  title?: string;
  source_url?: string;
  risk_level: RiskLevel;
  fake_probability: number;
  status: AnalysisStatus;
  created_at: string;
  input_type: string;
}

// ── Admin ────────────────────────────────────────────────────
export interface DashboardStats {
  total_analyses: number;
  analyses_today: number;
  total_users: number;
  average_fake_probability: number;
  high_risk_percentage: number;
  top_risk_domains: DomainRisk[];
}

export interface DomainRisk {
  domain: string;
  credibility_score: number;
  fake_count: number;
  is_blacklisted: boolean;
}

export interface TrendDataPoint {
  date: string;
  count: number;
  avg_risk: number;
}

export interface AnalyticsData {
  trends: TrendDataPoint[];
  top_topics: { topic: string; count: number; avg_risk: number }[];
  risk_distribution: Record<RiskLevel, number>;
}

// ── WebSocket ────────────────────────────────────────────────
export interface AnalysisProgress {
  analysis_id: string;
  stage: string;
  progress: number;
  detail: string;
  ts: string;
}
