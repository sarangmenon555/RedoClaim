// ─── AUTH ──────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "user" | "admin";
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ─── DOCUMENTS ─────────────────────────────────────────────────────────────
export type DocType =
  | "policy"
  | "rejection_letter"
  | "discharge_summary"
  | "hospital_bill"
  | "insurer_letter"
  // Motor insurance documents
  | "survey_report"
  | "rc_book"
  | "driving_licence"
  | "fir"
  | "repair_estimate"
  // Life insurance documents
  | "death_certificate"
  | "nominee_id"
  | "medical_report"
  | "other";

export type InsuranceType = "health" | "motor" | "life";
export type OcrStatus = "pending" | "processing" | "done" | "failed";

export interface Document {
  id: string;
  file_name: string;
  doc_type: DocType;
  insurance_type?: InsuranceType;
  ocr_status: OcrStatus;
  embedding_status: OcrStatus;
  ocr_text?: string;           // raw OCR text — needed by audit endpoint
  extracted_clauses?: PolicyClauses;
  risk_flags?: RiskFlag[];
  summary?: string;
  created_at: string;
}

export interface PolicyClauses {
  policy_type: string;
  insurer_name: string;
  sum_insured: string;
  waiting_periods: WaitingPeriod[];
  exclusions: Exclusion[];
  sub_limits: SubLimit[];
  room_rent_cap: { limit: string; type: string };
  co_payment: {
    percentage: string;
    applies_to?: string;   // age/condition e.g. "applicable only if insured age >= 60 years"
    conditions: string;
    note?: string;
  };
  pre_existing_disease_waiting: string;
  moratorium_period: string;
  claim_restrictions: string[];
  network_hospitals: string;
  portability_allowed: boolean;
  risky_clauses: RiskFlag[];
  plain_english_summary: string;
  // CIS-specific fields
  is_cis?: boolean;
  plain_english_inclusions?: string;
  plain_english_exclusions?: string;
  inception_date?: string;
}

export interface WaitingPeriod {
  condition: string;
  duration: string;
  risk_level: "high" | "medium" | "low";
}

export interface Exclusion {
  clause: string;
  exclusion?: string;   // alternate key used in CIS scan
  description: string;
  risk_level: "high" | "medium" | "low";
}

export interface SubLimit {
  item: string;
  limit: string;
  note: string;
}

export interface RiskFlag {
  clause: string;
  why_risky: string;
  irdai_reference: string;
}

// ─── CLAIMS ────────────────────────────────────────────────────────────────
export type ClaimStatus =
  | "submitted"
  | "under_review"
  | "rejected"
  | "appealing"
  | "resolved"
  | "escalated";

export interface Claim {
  id: string;
  policy_number?: string;
  insurer_name: string;
  claim_amount?: number;
  insurance_type: InsuranceType;
  status: ClaimStatus;
  rejection_reason_raw?: string;
  irdai_violation?: boolean;
  audit_report?: AuditReport;
  claim_date?: string;
  rejection_date?: string;
  gro_deadline?: string;
  irdai_deadline?: string;
  created_at: string;
}

// ─── AUDIT ─────────────────────────────────────────────────────────────────
export interface AuditReport {
  hierarchy_of_evidence: {
    step1_sla: SLACheck;
    step2_regulations: {
      audit: AuditResult;
      moratorium: MoratoriumCheck;
      cis_check: CISCheck;
      deficiency_in_service: DeficiencyCheck;
    };
    step3_redressal: EscalationPaths;
  };
  rejection_category: string;
  portability_advice?: PortabilityAdvice;
  rag_context_used: boolean;
  generated_at: string;
}

export interface AuditResult {
  rejection_reason_category: string;
  rejection_reason_summary: string;
  is_valid_rejection: boolean;
  step2_regulatory_violations: IRDAIViolation[];
  confidence: "high" | "medium" | "low";
  strength_of_case: "strong" | "moderate" | "weak";
  key_arguments: string[];
  evidence_needed: string[];
  step3_redressal?: { recommended_action: string };
}

export interface IRDAIViolation {
  violation: string;
  regulation: string;
  severity: "high" | "medium" | "low";
  argument?: string;
}

export interface SLACheck {
  sla_violations: SLAViolation[];
  violations_found: number;
  interest_applicable: boolean;
  deadlines: {
    gro_deadline?: string;
    ombudsman_deadline?: string;
    days_left_for_gro?: number;
    days_left_for_ombudsman?: number;
  };
}

export interface SLAViolation {
  type: string;
  regulation: string;
  detail: string;
  severity: "high" | "medium" | "low";
  interest_applicable?: boolean;
  interest_note?: string;
  edaakhil_trigger?: boolean;
}

export interface MoratoriumCheck {
  moratorium_applies: boolean;
  years_covered?: number;
  argument?: string;
  strength?: string;
  counter_to_insurer?: string;
}

export interface CISCheck {
  cis_violation: boolean;
  argument?: string;
}

export interface DeficiencyCheck {
  deficiency_in_service: boolean;
  statement?: string;
  product_liability_note?: string;
}

export interface EscalationPaths {
  recommended_immediate_action?: string;
  escalation_path: EscalationStep[];
}

export interface EscalationStep {
  step: number;
  route: string;
  deadline: string;
  how: string;
  cost: string;
  regulation?: string;
  eligible?: boolean;
  edaakhil_now_applicable?: boolean;
  relief_available?: string[];
}

export interface PortabilityAdvice {
  when_to_consider_porting: string;
  key_rights: string[];
  how_to_port: string[];
  regulation: string;
}

// ─── APPEALS ───────────────────────────────────────────────────────────────
export type AppealType =
  | "gro"
  | "insurer_escalation"
  | "ombudsman"
  | "bima_bharosa"
  | "consumer_court";

export interface Appeal {
  id: string;
  appeal_type: AppealType;
  letter_content?: string;
  legal_references?: IRDAIViolation[];
  submitted_at?: string;
  response_received: boolean;
  outcome?: string;
  created_at: string;
}

// ─── API ────────────────────────────────────────────────────────────────────
export interface ApiError {
  detail: string;
  status: number;
}

export interface UploadResponse {
  document_id: string;
  file_name: string;
  status: string;
  message: string;
}

export interface AuditResponse {
  claim_id: string;
  report: AuditReport;
  ai_disclaimer: {
    disclaimer: string;
    verify_at: string;
    free_legal_aid: string;
  };
  summary: {
    insurance_type: InsuranceType;
    is_valid_rejection: boolean;
    total_violations_found: number;
    sla_violations: number;
    irdai_violations: number;
    strength_of_case: "strong" | "moderate" | "weak";
    recommended_action?: string;
    moratorium_shield: boolean;
    deficiency_in_service: boolean;
    cis_violation: boolean;
    interest_applicable: boolean;
    edaakhil_applicable: boolean;
    // Motor-specific
    surveyor_issues?: { report_provided: boolean; issues: string[]; demand_note: string };
    depreciation_applicable?: boolean;
    zero_dep_check?: string;
    // Life-specific
    incontestability_applies?: boolean;
    section_45_applicable?: boolean;
    cause_of_death_relevance?: { undisclosed_condition_related_to_death: boolean | "unknown"; note: string };
  };
}

export interface AppealResponse {
  appeal_id: string;
  appeal_type: AppealType;
  letter: string;
  legal_references: IRDAIViolation[];
  generation_time_ms: number;
}