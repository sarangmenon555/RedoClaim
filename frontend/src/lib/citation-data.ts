export interface Citation {
  law: string; // "IRDAI Master Circular 2024" | "Consumer Protection Act, 2019" | etc.
  section: string; // "Para 17(b)" | "Section 2(11)" etc.
  title: string;
  summary: string;
  fullTextNote?: string; // where to verify the exact wording
}

// Static reference of the actual regulations the audit engine (gemini_service.py)
// cites in its prompts — so users can read the source law directly instead of
// just trusting the AI's citation. Written once, zero LLM cost per view.
export const CITATIONS: Citation[] = [
  {
    law: "IRDAI Master Circular on Protection of Policyholders' Interests, 2024",
    section: "Parts A, B and C - Settlement of Claims and Interest",
    title: "Insurer must decide a claim within a fixed time",
    summary:
      "Sets turnaround times for claim settlement: health reimbursement claims within 15 days of submission, death claims " +
      "within 15 days of intimation (45 days where an investigation is warranted), and, for motor and other retail general " +
      "claims, a decision within 7 days of the survey report. If a claim is not settled in time, interest at Bank Rate plus " +
      "2% per annum is payable from the date of receipt of the claim intimation until payment, on the insurer's own initiative.",
  },
  {
    law: "IRDAI Master Circular on Health Insurance, 2024",
    section: "Paras 15 and 16 - Cashless Authorisation and Discharge",
    title: "1-hour and 3-hour cashless response windows",
    summary:
      "The insurer must decide a cashless authorisation request immediately and within 1 hour, and grant final discharge " +
      "authorisation within 3 hours of the hospital's request. If discharge is delayed beyond 3 hours, the extra amount " +
      "charged by the hospital is borne by the insurer.",
  },
  {
    law: "IRDAI Master Circular on Protection of Policyholders' Interests, 2024",
    section: "No Rejection for Want of Documents",
    title: "A claim cannot be rejected or closed for want of documents",
    summary:
      "No claim shall be rejected or closed for want of documents or for delayed intimation of claim. In health insurance, " +
      "insurers and TPAs collect the required documents from the hospital and the policyholder is not required to submit them. " +
      "In motor and other retail general insurance, the customer submits only documents directly related to the claim.",
  },
  {
    law: "IRDAI Master Circular on Health Insurance Business, 2024",
    section: "Para 13 - Moratorium Period",
    title: "60-month moratorium on non-disclosure challenges",
    summary:
      "After a health policy has been continuously in force for 60 continuous months, a claim generally cannot be contested on grounds " +
      "of non-disclosure or misrepresentation, except in proven cases of established fraud. Verify the provision in the primary source.",
  },
  {
    law: "Insurance Act, 1938",
    section: "Section 45 — Life Insurance Incontestability",
    title: "3-year incontestability for life policies",
    summary:
      "Once a life insurance policy has been in force for 3 years from the date of issuance/revival, the " +
      "insurer generally cannot repudiate the claim for misstatement or suppression of fact, except for proven, " +
      "deliberate fraud on a material matter — and the burden of proving fraudulent intent lies with the insurer.",
  },
  {
    law: "Consumer Protection Act, 2019",
    section: "Section 2(11) — Deficiency in Service",
    title: "Legal definition of 'deficiency in service'",
    summary:
      "Defines 'deficiency' as any fault, imperfection, shortcoming, or inadequacy in the quality, nature, or " +
      "manner of performance of a service. An unjustified claim rejection or an unreasonably delayed decision " +
      "can be framed as a deficiency in service under this Act.",
  },
  {
    law: "Consumer Protection Act, 2019; Consumer Protection (Jurisdiction) Rules, 2021",
    section: "Jurisdiction - District, State and National Commissions",
    title: "Where to file a consumer complaint: decided by the value paid as consideration",
    summary:
      "The forum depends on the value of the goods or services paid as consideration, not on the claim amount: the District " +
      "Commission up to ₹50 lakh, the State Commission above ₹50 lakh up to ₹2 crore, and the National Commission above " +
      "₹2 crore. For an insurance policy the consideration is the premium paid, so most insurance complaints go to the District " +
      "Commission. The Supreme Court confirmed the consideration-based test in 2025. The filing fee follows the same value.",
  },
  {
    law: "Insurance Ombudsman Rules, 2017",
    section: "Rule 13 — Ombudsman's Power",
    title: "What the Insurance Ombudsman can and cannot do",
    summary:
      "The Ombudsman can pass awards on complaints regarding claim disputes up to a specified pecuniary limit, " +
      "acting as a faster, free alternative to litigation. Its award does not bar the policyholder from later " +
      "approaching a consumer forum or civil court if dissatisfied.",
  },
  {
    law: "Insurance Ombudsman Rules, 2017",
    section: "Rule 14 — Conditions for Complaint",
    title: "You must approach the insurer's GRO first",
    summary:
      "A complaint to the Ombudsman is maintainable only if the complainant has first approached the insurer's " +
      "Grievance Redressal Officer (GRO) and either received an unsatisfactory response or received no response " +
      "within one month, and files with the Ombudsman within 1 year of that.",
  },
  {
    law: "Motor Vehicles Act / Supreme Court precedent",
    section: "Swaran Singh v. National Insurance Co. (2004)",
    title: "A technical licence defect doesn't automatically void a motor claim",
    summary:
      "The Supreme Court held that an insurer must prove the driving-licence defect was material to the " +
      "accident and that the policyholder was aware of it, before a claim can be denied purely on licence " +
      "grounds — a minor technical/procedural lapse is often not sufficient by itself.",
  },
  {
    law: "Policy terms (room-rent sub-limit clauses)",
    section: "Proportionate Deduction — Room Rent",
    title: "How room-rent-cap deductions are supposed to be calculated",
    summary:
      "When actual room rent exceeds the policy's eligible limit, the standard method applies a proportionate " +
      "deduction across the ENTIRE admissible claim amount (not just the room charge) — deducting more than " +
      "this proportion, or deducting only from unrelated line items, is a common point of dispute.",
  },
];
