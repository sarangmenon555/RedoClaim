export interface Citation {
  law: string; // "IRDAI Master Circular 2024" | "Consumer Protection Act 2019" | etc.
  section: string; // "Chapter II, Para 8.3" | "Section 2(11)" etc.
  title: string;
  summary: string;
  fullTextNote?: string; // where to verify the exact wording
}

// Static reference of the actual regulations the audit engine (gemini_service.py)
// cites in its prompts — so users can read the source law directly instead of
// just trusting the AI's citation. Written once, zero LLM cost per view.
export const CITATIONS: Citation[] = [
  {
    law: "IRDAI Master Circular on Health Insurance, 2024",
    section: "Turnaround Time (TAT) for Claim Settlement",
    title: "Insurer must decide a claim within a fixed time",
    summary:
      "Requires insurers to settle or reject a claim within a specified turnaround time after receiving all " +
      "necessary documents. Missing this deadline can itself be grounds for escalation, and may attract " +
      "interest on the delayed amount under IRDAI's protection-of-policyholders regulations.",
  },
  {
    law: "IRDAI Master Circular on Health Insurance, 2024",
    section: "Cashless Facility — Pre-Authorization TAT",
    title: "1-hour and 3-hour cashless response windows",
    summary:
      "Insurers/TPAs must respond to an initial cashless pre-authorization request within 1 hour, and to a " +
      "final discharge authorization request within 3 hours of receiving complete information from the hospital.",
  },
  {
    law: "IRDAI (Protection of Policyholders' Interests) Regulations",
    section: "Document Requisition",
    title: "Insurer cannot repeatedly demand new documents to delay a decision",
    summary:
      "Insurers are required to call for all necessary claim documents at one go (or within a limited number " +
      "of rounds), rather than serially demanding more documents over an extended period, which is a documented " +
      "delay tactic.",
  },
  {
    law: "IRDAI Master Circular, 2024",
    section: "Moratorium Period (Health Insurance)",
    title: "8-year moratorium on non-disclosure challenges",
    summary:
      "After a health policy has been continuously in force for 8 years, no claim can be contested on grounds " +
      "of non-disclosure or misrepresentation, except in proven cases of established fraud.",
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
    law: "Consumer Protection Act, 2019",
    section: "Jurisdiction — District/State/National Commissions",
    title: "Where to file a consumer complaint, by claim value",
    summary:
      "Consumer disputes are filed at the District Commission, State Commission, or National Commission " +
      "depending on the value of goods/services and compensation claimed. An insurance claim dispute qualifies " +
      "as a 'deficiency in service' complaint under this Act.",
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
      "within the stipulated period (commonly 30 days), and files with the Ombudsman within 1 year of that.",
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
    law: "IRDAI Master Circular on Health Insurance, 2024",
    section: "Proportionate Deduction — Room Rent",
    title: "How room-rent-cap deductions are supposed to be calculated",
    summary:
      "When actual room rent exceeds the policy's eligible limit, the standard method applies a proportionate " +
      "deduction across the ENTIRE admissible claim amount (not just the room charge) — deducting more than " +
      "this proportion, or deducting only from unrelated line items, is a common point of dispute.",
  },
];
