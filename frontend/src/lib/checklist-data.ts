export interface ChecklistItem {
  document: string;
  note?: string;
  critical?: boolean; // insurers most commonly cite this one's absence to delay/deny
}

export interface ChecklistSet {
  insuranceType: "health" | "motor" | "life";
  scenario: "rejection_appeal" | "preauth" | "settlement_dispute" | "fresh_claim";
  title: string;
  items: ChecklistItem[];
}

// Written once, served statically — no LLM call per page view. Compiled from
// commonly-requested documents across Indian insurers; expand as real
// patterns surface in the Ask AI tool or user feedback.
export const CHECKLISTS: ChecklistSet[] = [
  {
    insuranceType: "health",
    scenario: "fresh_claim",
    title: "Health Insurance — Filing a Fresh Claim",
    items: [
      { document: "Duly filled claim form (insurer's format)", critical: true },
      { document: "Original policy copy / policy schedule" },
      { document: "Hospital discharge summary", critical: true },
      { document: "All original hospital bills with itemized breakup", critical: true },
      { document: "Payment receipts for all bills" },
      { document: "Diagnostic reports (lab, imaging) relevant to the treatment" },
      { document: "Doctor's prescription and treatment advice notes" },
      { document: "Pharmacy bills for medicines purchased separately" },
      { document: "KYC documents (Aadhaar/PAN) of the policyholder" },
      { document: "Cancelled cheque or bank passbook copy for payout account" },
      { document: "FIR copy (only if the claim involves an accident)" },
    ],
  },
  {
    insuranceType: "health",
    scenario: "preauth",
    title: "Health Insurance — Cashless Pre-Authorization Request",
    items: [
      { document: "Pre-authorization form (hospital's TPA desk usually files this)", critical: true },
      { document: "Policy number and e-card / health card" },
      { document: "Doctor's admission advice with provisional diagnosis", critical: true },
      { document: "ID proof of the patient" },
      { document: "Estimated cost of treatment from the hospital" },
      { document: "Previous medical records if the condition is pre-existing/chronic" },
    ],
  },
  {
    insuranceType: "health",
    scenario: "rejection_appeal",
    title: "Health Insurance — Appealing a Claim Rejection",
    items: [
      { document: "The insurer's rejection/repudiation letter itself", critical: true },
      { document: "Complete claim file as originally submitted (keep a copy always)" },
      { document: "Any additional medical records addressing the insurer's stated reason", critical: true },
      { document: "Doctor's clarification letter if rejection cites 'pre-existing disease' or 'non-disclosure'" },
      { document: "Policy schedule and Customer Information Sheet (CIS) highlighting the relevant clause" },
      { document: "Proof of premium payments / continuous renewal history (for waiting-period disputes)" },
      { document: "Written request to the insurer's Grievance Redressal Officer (GRO), with acknowledgment" },
    ],
  },
  {
    insuranceType: "health",
    scenario: "settlement_dispute",
    title: "Health Insurance — Disputing a Partial Settlement",
    items: [
      { document: "The settlement letter with the insurer's deduction breakup", critical: true },
      { document: "Original itemized hospital bill (to cross-check each deduction)", critical: true },
      { document: "Room category and per-day room rent proof from the hospital" },
      { document: "Policy schedule showing sum insured, room rent cap, and co-payment clauses" },
      { document: "Written query to the insurer asking for a line-by-line deduction justification" },
    ],
  },
  {
    insuranceType: "motor",
    scenario: "fresh_claim",
    title: "Motor Insurance — Filing a Fresh Claim",
    items: [
      { document: "Duly filled claim form", critical: true },
      { document: "Copy of the policy / cover note" },
      { document: "Registration Certificate (RC) of the vehicle", critical: true },
      { document: "Valid driving licence of the driver at the time of the incident", critical: true },
      { document: "FIR copy (mandatory for theft or third-party injury claims)" },
      { document: "Repair estimate from an authorized garage" },
      { document: "Photographs of the damage" },
      { document: "Original bills and payment receipts after repair" },
    ],
  },
  {
    insuranceType: "motor",
    scenario: "rejection_appeal",
    title: "Motor Insurance — Appealing a Claim Rejection",
    items: [
      { document: "The insurer's rejection letter itself", critical: true },
      { document: "Driving licence — check the exact defect cited (expired vs never-held is a major legal difference)", critical: true },
      { document: "Any evidence the licence defect wasn't material to the accident (e.g. minor renewal delay)" },
      { document: "Original FIR and any police investigation report" },
      { document: "Survey report copy from the insurer's surveyor, if one was appointed" },
    ],
  },
  {
    insuranceType: "life",
    scenario: "fresh_claim",
    title: "Life Insurance — Filing a Death Claim",
    items: [
      { document: "Duly filled claim form (Death Claim Form A)", critical: true },
      { document: "Original policy document" },
      { document: "Death certificate issued by the municipal authority", critical: true },
      { document: "Nominee's/claimant's KYC and bank details" },
      { document: "Medical treatment records prior to death (for early-stage claims within 3 years)" },
      { document: "FIR and post-mortem report (for accidental or unnatural death)" },
      { document: "Employer's certificate or income proof (if required by policy terms)" },
    ],
  },
  {
    insuranceType: "life",
    scenario: "rejection_appeal",
    title: "Life Insurance — Appealing a Claim Rejection",
    items: [
      { document: "The insurer's repudiation letter itself", critical: true },
      { document: "Proof of policy's continuous force for 3+ years, if invoking the incontestability clause", critical: true },
      { document: "Medical records contesting any 'non-disclosure' or 'misstatement' claim" },
      { document: "Proof that any alleged non-disclosure was not material or not deliberate" },
      { document: "Original proposal form copy (to verify what was actually asked/disclosed at purchase)" },
    ],
  },
];
