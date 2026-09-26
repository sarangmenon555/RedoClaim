export interface FaqEntry {
  category: string;
  question: string;
  answer: string;
  relatedTool?: { label: string; href: string };
}

// Written once, served statically — no LLM call per page view. Expand this
// list over time from real rejection patterns seen in the Ask AI / Auditor
// tools; it costs nothing to keep growing since it's just JSON.
export const FAQ_ENTRIES: FaqEntry[] = [
  {
    category: "Pre-existing disease",
    question: "My claim was rejected for 'pre-existing disease non-disclosure' — is that valid?",
    answer:
      "Insurers can reject a claim on this ground only if you were actually diagnosed with, or had received " +
      "treatment/advice for, the condition BEFORE buying the policy — and if that fact was genuinely material " +
      "to underwriting. A rejection based on the condition merely appearing in your medical history without " +
      "proof of pre-policy diagnosis is often successfully challenged. After 8 years (the moratorium period " +
      "under IRDAI regulations), insurers generally cannot invoke non-disclosure at all, except in cases of " +
      "proven fraud.",
    relatedTool: { label: "Check your waiting periods", href: "/dashboard/waiting-period" },
  },
  {
    category: "Waiting period",
    question: "The insurer says my condition is still in the waiting period. How do I verify this myself?",
    answer:
      "Every policy states a specific waiting period per condition (commonly 2–4 years for named ailments, " +
      "and a shorter initial 30-day waiting period for everything else). Check your policy schedule or CIS " +
      "for the exact duration, then count forward from your policy's original inception date — not the most " +
      "recent renewal date, since continuous renewals carry your waiting-period clock forward.",
    relatedTool: { label: "Run the Waiting Period Calculator", href: "/dashboard/waiting-period" },
  },
  {
    category: "Documentation",
    question: "My claim was rejected for 'insufficient documentation' — what can I do?",
    answer:
      "Ask the insurer, in writing, exactly which document was missing or deficient — they're required to " +
      "specify this, not just issue a blanket rejection. Insurers are also required under IRDAI regulations " +
      "to request all necessary documents within a defined turnaround time after claim intimation, not " +
      "repeatedly ask for more documents to delay a decision. A pattern of successive 'more documents needed' " +
      "requests without a final decision is itself a valid ground for escalation.",
  },
  {
    category: "Cashless denial",
    question: "My cashless request was denied at the hospital — can I still claim reimbursement?",
    answer:
      "Yes. A cashless denial is not a final rejection of the claim itself — it only means the hospital wasn't " +
      "authorized to bill the insurer directly. You can pay out of pocket and file for reimbursement afterward, " +
      "using the same policy terms. If the reimbursement claim is then rejected for the same reason the cashless " +
      "request was denied, that reasoning can be challenged on its own merits.",
  },
  {
    category: "Room rent / sub-limits",
    question: "The insurer deducted a large amount citing a 'room rent cap' — is the full deduction fair?",
    answer:
      "Room rent caps typically trigger a 'proportionate deduction' — not just on the room charge, but " +
      "proportionately across your ENTIRE bill (surgery fees, medicines, consumables — everything), based on " +
      "the ratio between your actual room rent and the capped amount. Insurers sometimes apply this deduction " +
      "incorrectly or too broadly. Ask for a line-by-line breakup of exactly how the deduction was calculated.",
    relatedTool: { label: "Get an itemized payout estimate", href: "/dashboard/estimator" },
  },
  {
    category: "Motor claims",
    question: "My motor claim was rejected for a driving licence issue — is this always valid?",
    answer:
      "Not always. Courts (including the Supreme Court in Swaran Singh, 2004) have held that a technical " +
      "licence defect does not automatically void a claim unless the insurer proves the defect was material to " +
      "the accident and the policyholder knew about it. A minor procedural lapse (e.g. licence renewal delay " +
      "with no substantive change in driving competence) is frequently not sufficient grounds for a full denial.",
  },
  {
    category: "Life insurance",
    question: "My family's claim was rejected years after the policy started, citing non-disclosure. Can insurers do this?",
    answer:
      "Under the Insurance Act's incontestability provision, once a life policy has been in force continuously " +
      "for 3 years, the insurer generally cannot repudiate the claim for non-disclosure or misstatement — except " +
      "in cases of proven, deliberate fraud on a material fact. The burden of proving fraudulent intent (not " +
      "mere omission) sits with the insurer.",
  },
  {
    category: "Escalation & timelines",
    question: "How long does the insurer have to respond after I file a grievance?",
    answer:
      "Under the IRDAI Master Circular on grievance redressal, the insurer's Grievance Redressal Officer (GRO) " +
      "must respond within 15 days. If unresolved or unsatisfactory, you can escalate to the Insurance Ombudsman " +
      "or file on the IRDAI Bima Bharosa portal. Missing your own escalation windows can forfeit some remedies — " +
      "track your deadlines from the day of rejection, not the day you get around to filing.",
    relatedTool: { label: "See your claim's deadlines", href: "/dashboard/timeline" },
  },
  {
    category: "Escalation & timelines",
    question: "The Ombudsman also ruled against me — is that the end of the road?",
    answer:
      "No. An Ombudsman award is not the final word — you retain the right to approach a Consumer Disputes " +
      "Redressal Commission (District/State/National, depending on the claim amount) or a civil court, since " +
      "these are independent legal remedies under the Consumer Protection Act, not an appeal of the Ombudsman's " +
      "decision.",
    relatedTool: { label: "Generate a Consumer Forum complaint", href: "/dashboard/appeals" },
  },
];
