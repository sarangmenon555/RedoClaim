# RedoClaim

AI-assisted insurance claim analysis and grievance drafting for policyholders in India.

---

## What is RedoClaim?

RedoClaim helps policyholders read and understand an insurance claim rejection. Upload your rejection letter, your policy PDF, or your Customer Information Sheet, and RedoClaim extracts the relevant text with OCR, compares it with the regulatory sources in its knowledge base, and produces an AI-assisted analysis referencing the IRDAI Master Circular on Health Insurance, 2024, together with editable grievance and appeal drafts for your review.

RedoClaim is currently focused on Indian health insurance.

RedoClaim is an AI-assisted research and document-analysis tool. It does not make official legal or regulatory determinations, approve or reject claims, or guarantee claim outcomes. Users should verify important findings, citations and deadlines against applicable primary sources.

---

## Why it exists

Claim rejection letters are often hard to read, and the grievance and complaint routes that follow them are not widely understood. RedoClaim is meant to help policyholders understand the coverage, exclusions and conditions described in their policy, see which regulatory provisions may be relevant, and prepare a well-organised grievance or appeal that they can review, correct and send themselves.

---

## Features

### Analysis

- **Policy Analyzer**: extracts waiting periods, exclusions, sub-limits, room rent caps, co-payment triggers and other clauses from policy documents, and flags clauses that deserve a closer read.
- **CIS Scanner**: reads the Customer Information Sheet and lists the inclusions and exclusions it describes, with reference to the IRDAI Master Circular on Health Insurance, 2024.
- **Rejection Analysis**: a structured evidence-based analysis in three stages:
  1. **Timeline & TAT Analysis**: do the documented dates appear consistent with the applicable timelines?
  2. **Potential Regulatory Inconsistencies**: does the rejection appear inconsistent with applicable IRDAI provisions?
  3. **Redressal route**: which grievance or complaint forum (GRO, Insurance Ombudsman, IRDAI Bima Bharosa, or Consumer Commission via e-Jagriti) may be relevant?

  Each finding is presented with its source, the relevant provision, evidence from the uploaded document and a verification note (see "How findings are presented" below).
- **Settlement Second Opinion**: for partial settlements, reviews the settlement letter and checks whether each deduction the insurer made appears consistent with the policy clauses on record.
- **Pre-Auth Denial Check**: for a cashless pre-authorisation denial at admission, reviews whether the stated reason appears consistent with the policy and whether the documented timing appears consistent with the applicable cashless timeline. It also explains that paying and claiming reimbursement remains an option.
- **Payout Estimator**: an itemised estimate of what a claim may be worth, calculated from the clauses already extracted from your policy (sum insured, co-payment, sub-limits, room rent cap). Every figure traces to a specific clause, and assumptions are stated as assumptions.
- **Co-pay / Deductible Breakdown**: a pre-claim planning tool. Enter your hospital bill and room rent to see the proportionate room-rent deduction and co-payment calculated.
- **Waiting Period Check**: checks each waiting-period clause on your policy against its inception date and shows which conditions are still within the waiting period and which have lapsed.
- **Compare Policies**: side-by-side comparison of two or three analysed policies, covering sum insured, room rent cap, co-payment and PED waiting period.
- **Renewal Red-Flag Check**: compares last year's policy with this year's renewal and highlights adverse changes such as a reduced sum insured, new exclusions, a smaller room-rent cap or a disproportionate premium increase.
- **Sum Insured Adequacy Check**: compares your sum insured with typical major-treatment costs for your city tier and family profile.
- **Hospital Network Check**: crowdsourced reports from other users on whether a hospital is currently in an insurer's cashless network. Reports are unverified and can be out of date.
- **All My Policies**: every policy and claim across your account and the family members you add, in one view.
- **Is it worth pursuing?**: a rough, transparent estimate that weighs case strength, the value of the claim and the effort of the recommended route. It is not a prediction of outcome.
- **Ask AI**: a free-form assistant that uses function calling to look up your actual claim status, a document's extracted clauses and RedoClaim's regulation knowledge base instead of guessing, works out applicable deadlines, and can save an appeal draft to your account.
- **Explain a Term**: paste any insurance term or policy clause and get a plain-language explanation.
- **Document quality checks**: uploads are checked for blur, low resolution, missing pages and unreadable pages before analysis, so a poor scan does not silently produce a confident-looking but wrong result.

### Action

- **Appeal Drafter**: generates editable grievance and appeal drafts for user review:
  - GRO (Grievance Redressal Officer) letters
  - Insurance Ombudsman complaints
  - Insurer escalation letters
  - IRDAI Bima Bharosa complaints
  - e-Jagriti consumer-complaint drafts

  Drafts reference IRDAI provisions where supplied by the analysis. Drafts are kept as versions, you can mark a preferred version, and you can record the outcome.
- **Follow-up Letter Generator**: a template-based reminder for a grievance whose applicable timeline has passed with no logged response.
- **Precedent Matcher**: matches your fact pattern against a curated library of illustrative Ombudsman and consumer-forum case summaries. Verify any case citation against primary sources before relying on it.
- **Portability Advisor**: explains health insurance portability provisions, including waiting period credits and continuity benefits, with a step-by-step guide.
- **e-Jagriti Guide**: a walkthrough of filing a consumer complaint online, including forum selection by claim value.
- **Ombudsman Jurisdiction Finder**: choose your State or UT to find the Insurance Ombudsman office and contact details for your jurisdiction.
- **Common Rejection Reasons**: a reference library of frequent rejection reasons in India and the options available for each.
- **Document Completeness Checklist**: a checklist of documents to gather up front, to reduce repeated document requests.
- **Regulatory Citation Library**: readable summaries of the IRDAI circulars, Consumer Protection Act, 2019 sections and Ombudsman Rules that the analysis refers to, with links to primary sources.
- **Document Redaction Helper**: flags text that looks like sensitive personal data before you share a document. It is pattern-matching only and does not guarantee detection of every format.
- **NCB Checker**: a motor-insurance renewal reference calculator for the No-Claim Bonus discount that appears applicable.

### Tracking

- **Timeline Tracker**: helps track applicable claim and grievance timelines, along with Ombudsman filing and Consumer Commission limitation periods. Each timeline is shown with its basis rather than as a single universal deadline, for example:

  ```
  Applicable timeline: 15 days
  Basis: [specific applicable provision/source]
  ```
- **Case timeline and PDF export**: a per-claim event timeline and an exportable PDF case summary containing the claim details, analysis findings and drafts.
- **My Documents**: all uploaded documents and their analysis status.

### Platform

- **Multilingual output**: analysis reports, appeal drafts and the Ask AI assistant can be delivered in English, Hindi, Malayalam, Tamil, Telugu and Kannada, powered by Sarvam AI. Translation is performed only when a translated report is requested. Static interface text is localised separately.
- **Accounts and privacy controls**: registration, login, password reset, profile settings and account deletion.
- **Demo mode**: try the tool without signing up.
- **Admin dashboard**: aggregate usage statistics for operators.

---

## How findings are presented

Each finding is intended to show:

```
Finding -> Source -> Relevant provision -> Evidence from the uploaded document -> Verification note
```

For example:

```
Potential inconsistency identified
Source:       IRDAI Master Circular on Health Insurance, 2024
Provision:    [specific section]
Evidence:     [relevant extracted policy or rejection text]
Verification: Review against the current primary source before relying on this finding.
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js |
| Backend | FastAPI (async, Python 3.11) |
| LLM (reasoning, extraction, drafting) | OpenAI GPT-5 Nano, via function calling |
| Embeddings | OpenAI `text-embedding-3-small` (truncated to 768-dim) |
| Vector DB (regulation retrieval / RAG) | Qdrant |
| Primary database | PostgreSQL (Neon), via SQLAlchemy (async) + Alembic migrations |
| Object storage (uploaded documents) | MinIO (S3-compatible) |
| Multilingual translation | Sarvam AI |
| Background jobs | Celery |

---

## Regulatory Coverage and Sources

RedoClaim's knowledge base references:

- IRDAI Master Circular on Health Insurance, 2024
- IRDAI (Health Insurance) Regulations, 2016 (as amended)
- Insurance Ombudsman Rules, 2017
- Consumer Protection Act, 2019 (insurance grievances)
- IRDAI Bima Bharosa guidelines

Primary regulatory and government sources take precedence over anything shown by RedoClaim where they differ.

---

## Disclaimer

RedoClaim provides AI-assisted analysis for informational purposes. It does not make official determinations about whether an insurer has violated a law, regulation, policy term or regulatory requirement, and it identifies potential issues for the user's review only. It is not a substitute for legal advice. AI output can be wrong, OCR can misread documents, and regulations change. Verify all citations and applicable deadlines, and seek professional assistance from a qualified insurance lawyer or consumer rights advocate for complex or high-value matters.