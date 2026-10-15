import re

from app.services.irdai.consumer_fees import FORUM_BASIS_NOTE, fee_table, forums

PPI = "IRDAI Master Circular on Protection of Policyholders' Interests, 2024"
HC = "IRDAI Master Circular on Health Insurance Business, 2024"
OPS = "IRDAI Master Circular on Operations and Allied Matters of Insurers, 2024"

ALLOWED_DOMAINS = {
    "irdai.gov.in",
    "bimabharosa.irdai.gov.in",
    "cioins.co.in",
    "e-jagriti.gov.in",
    "iib.gov.in",
    "nalsa.gov.in",
}

APP_PAGES = {
    "/dashboard": "Home (this chat)",
    "/dashboard/documents": "Documents",
    "/dashboard/timeline": "Timeline",
    "/dashboard/appeals": "Appeals",
    "/dashboard/e-jagriti": "e-Jagriti guide and fee finder",
    "/dashboard/ombudsman-finder": "Ombudsman finder",
    "/dashboard/faq": "FAQ",
    "/dashboard/auditor": "Rejection auditor",
    "/dashboard/settlement-audit": "Settlement audit",
    "/dashboard/preauth-check": "Cashless denial check",
    "/dashboard/analyzer": "Policy analyzer",
    "/dashboard/cis": "CIS scanner",
    "/dashboard/estimator": "Payout estimator",
    "/dashboard/waiting-period": "Waiting period check",
    "/dashboard/compare-policies": "Compare policies",
    "/dashboard/renewal-check": "Renewal check",
    "/dashboard/portability": "Portability guide",
    "/dashboard/copay-breakdown": "Co-pay breakdown",
    "/dashboard/ncb-check": "No-claim bonus check",
    "/dashboard/sum-insured-check": "Sum insured check",
    "/dashboard/explain": "Explain a term",
    "/dashboard/checklist": "Checklist",
    "/dashboard/citations": "Citations",
    "/dashboard/hospital-verify": "Hospital verify",
    "/dashboard/portfolio": "Portfolio",
    "/dashboard/redaction-helper": "Redaction helper",
}


def _fee_text() -> str:
    parts = []
    for row in fee_table():
        fee = "nil" if row["fee"] == 0 else f"Rs. {row['fee']:,}"
        parts.append(f"{row['range']}: {fee}")
    return "; ".join(parts)


def _forum_text() -> str:
    return "; ".join(f"{f['forum']}: {f['range']}" for f in forums())


FACTS = [
    {
        "id": "grievance_timeline",
        "title": "Insurer grievance timeline",
        "keywords": ["grievance", "gro", "complaint", "respond", "response", "reply", "resolve", "resolution", "acknowledg", "14", "verify", "deadline", "not responded", "no reply"],
        "text": (
            "An insurer must acknowledge a grievance immediately and resolve it, with a final letter of resolution, within 14 days (two weeks) "
            "of registration. It may ask the complainant for further details only once, within one week. A grievance may be closed if the "
            "complainant does not reply within eight weeks. The resolution letter must include the contact details of the Insurance Ombudsman, "
            "and if a complaint is not accepted it must give reasons with reference to the specific policy terms."
        ),
        "source": f"{PPI}; {OPS}, clause 24 and clause 23.5",
    },
    {
        "id": "bima_bharosa",
        "title": "Bima Bharosa portal",
        "keywords": ["bima bharosa", "bimabharosa", "igms", "portal", "track", "status", "grievance", "verify", "register"],
        "text": (
            "Bima Bharosa (bimabharosa.irdai.gov.in) is the IRDAI grievance portal. Insurers must integrate their grievance systems with it so that "
            "grievances can be registered and tracked online, and they must record on it grievances received by telephone, email, post or in person. "
            "The insurer's system must stay synchronised with Bima Bharosa."
        ),
        "source": f"{OPS}, clauses 23.6 and 23.7",
    },
    {
        "id": "cashless",
        "title": "Cashless authorisation and discharge",
        "keywords": ["cashless", "pre-auth", "preauth", "authoris", "authoriz", "discharge", "hospital", "tpa", "one hour", "3 hours", "three hours"],
        "text": (
            "An insurer must decide on a cashless authorisation request immediately and within one hour of receiving it, and must give final "
            "authorisation for discharge within three hours of the hospital's request. If discharge is delayed beyond three hours, any additional "
            "amount charged by the hospital is borne by the insurer from the shareholders' fund. Insurers and TPAs collect the required documents "
            "from the hospital; the policyholder is not required to submit them."
        ),
        "source": f"{HC}, Paras 15, 16 and 17",
    },
    {
        "id": "reimbursement_interest",
        "title": "Reimbursement timeline and interest",
        "keywords": ["reimbursement", "settle", "settlement", "interest", "delay", "delayed", "bank rate", "15 days", "paid"],
        "text": (
            "For health claims other than cashless, the insurer must settle the claim within 15 days of submission of the claim. If a claim is not "
            "settled within the specified timelines, the claimant is entitled to interest at Bank Rate plus 2% per annum from the date of receipt of "
            "the claim intimation until the date of payment, and the insurer must pay it on its own."
        ),
        "source": f"{PPI}, Part B",
    },
    {
        "id": "documents_rule",
        "title": "No rejection for want of documents",
        "keywords": ["document", "documents", "missing", "insufficient", "intimation", "delayed intimation", "late intimation", "reject", "rejected", "rejection"],
        "text": (
            "No claim shall be rejected or closed for want of documents or for delayed intimation of claim. In health insurance, insurers and TPAs "
            "collect the required documents from the hospital and the policyholder is not required to submit them. In motor and other retail general "
            "insurance, the customer submits only the documents directly related to the claim."
        ),
        "source": f"{PPI}, claims sections of Parts A, B and C; {HC}, Para 17",
    },
    {
        "id": "repudiation_rules",
        "title": "How a claim may be rejected",
        "keywords": ["repudiat", "reject", "rejected", "rejection", "partly", "disallow", "deduction", "specific clause", "committee", "reason"],
        "text": (
            "No health claim may be repudiated without the approval of the insurer's Product Management Committee or its three-member Claims Review "
            "Committee. When a claim is repudiated or partly disallowed, the details must be conveyed to the claimant in full, with reference to the "
            "specific terms and conditions of the policy document."
        ),
        "source": f"{HC}, Para 17",
    },
    {
        "id": "ombudsman",
        "title": "Insurance Ombudsman",
        "keywords": ["ombudsman", "bima lokpal", "award", "escalate", "cioins", "one year", "limit", "50 lakh"],
        "text": (
            "A policyholder who is not satisfied with the insurer's resolution can escalate to the Insurance Ombudsman of competent jurisdiction where "
            "the claim amount is up to Rs. 50 lakh. Filing is free: in person, online at cioins.co.in/Complaint/Online, or in writing by post or email. "
            "Under Rule 14 of the Insurance Ombudsman Rules, 2017 the complaint must generally be made within one year of the insurer's rejection or "
            "unsatisfactory reply, or after one month has passed without a reply to the written representation. A complaint is not maintainable on a "
            "matter pending before, or decided by, a court, consumer forum or arbitrator. The insurer must comply with an award within 30 days; if it "
            "does not, Rs. 5,000 per day is payable to the complainant, unless the insurer appeals within 30 days."
        ),
        "source": f"Insurance Ombudsman Rules, 2017; {PPI}, Part B; {HC}, Para 20",
    },
    {
        "id": "consumer_forum_fee",
        "title": "Consumer Commission forum and fee",
        "keywords": ["consumer", "e-jagriti", "ejagriti", "jagriti", "commission", "court", "fee", "forum", "district", "state commission", "national commission", "deficiency", "file", "filing", "online"],
        "text": (
            f"{FORUM_BASIS_NOTE} Forums by value paid as consideration: {_forum_text()}. Filing fee by value paid as consideration: {_fee_text()}. "
            "The legal basis for a complaint about an insurer's service is the Consumer Protection Act, 2019, Section 2(11) (deficiency in service). "
            "e-Jagriti (e-jagriti.gov.in) is the online portal for consumer complaints before the District, State and National Commissions, and "
            "RedoClaim has an e-Jagriti guide with a fee finder at /dashboard/e-jagriti. A limitation period applies to consumer complaints, so check "
            "it with the commission or an advocate."
        ),
        "source": "Consumer Protection Act, 2019; Consumer Protection (Jurisdiction) Rules, 2021; e-Jagriti fee schedule",
    },
    {
        "id": "portability",
        "title": "Portability",
        "keywords": ["port", "portability", "switch", "another insurer", "transfer", "new insurer"],
        "text": (
            "A policyholder can port a health indemnity policy, with all family members, to another insurer and transfer the credits gained, to the "
            "extent of the sum insured: no-claim bonus, specific waiting periods, waiting period for pre-existing diseases and moratorium period. The "
            "policyholder must apply at least 30 days before, and not earlier than 60 days from, the renewal due date; insurers may also consider a "
            "request made within 15 days of the renewal date, provided there is no break in the policy. The existing insurer must share the "
            "information within 72 hours through the Insurance Information Bureau of India (iib.gov.in), and the new insurer must decide within 5 days "
            "of receiving it. No charges are levied for porting in or porting out."
        ),
        "source": f"{HC}, Para 12; {PPI}, Part B, Chapter VI",
    },
    {
        "id": "moratorium_waiting",
        "title": "Moratorium and waiting periods",
        "keywords": ["moratorium", "waiting", "pre-existing", "ped", "non-disclosure", "misrepresentation", "fraud", "60 months", "5 years", "contest"],
        "text": (
            "No health insurance policy or claim can be contested on any ground of non-disclosure or misrepresentation, except established fraud, after "
            "60 months (5 years) of continuous coverage. Credits under ported and migrated policies count towards the moratorium period. The waiting "
            "period for pre-existing diseases can be at most 36 months (3 years). Waiting period credits carry forward on migration or portability, "
            "to the extent of the sum insured."
        ),
        "source": f"{HC}, Para 13 and Para 12; IRDAI (Insurance Products) Regulations, 2024",
    },
    {
        "id": "free_look_grace_renewal",
        "title": "Free look, grace period, cancellation and renewal",
        "keywords": ["free look", "grace", "cancel", "cancellation", "renew", "renewal", "premium due", "lapse", "migrate", "migration"],
        "text": (
            "The free look period is 30 days from receipt of the policy document, for policies of one year or more. A policyholder may cancel a policy "
            "at any time by giving 7 days' notice in writing. The grace period for paying premium is 15 days for monthly instalments and 30 days for "
            "quarterly, half-yearly or annual instalments, and credits are protected if the policy is renewed in the grace period. A health policy "
            "cannot be refused renewal because of claims in earlier years, and fresh underwriting is allowed only on an increase in sum insured. "
            "Insurers must send a renewal notice at least 30 days before the due date."
        ),
        "source": f"{HC}, Paras 5, 6, 8 and 10; {OPS}, clause 41.2",
    },
    {
        "id": "cis",
        "title": "Customer Information Sheet",
        "keywords": ["cis", "customer information sheet", "exclusions", "inclusions", "summary", "sub-limit", "deductible"],
        "text": (
            "Insurers must give every policyholder a Customer Information Sheet (CIS) with the policy and obtain acknowledgement. It explains in simple "
            "words the type of insurance, sum insured, coverage, a summary of exclusions, sub-limits, deductibles, waiting periods, free look period, "
            "renewal, migration, portability and moratorium, along with the claims procedure, policy servicing and grievance redressal, including "
            "the Insurance Ombudsman's contact details. The CIS is a summary and does not replace the policy document."
        ),
        "source": f"{HC}, Para 4; {OPS}, clause 40",
    },
    {
        "id": "motor_general_tat",
        "title": "Motor and general insurance claim timelines",
        "keywords": ["motor", "car", "vehicle", "surveyor", "survey", "accident", "own damage", "general insurance", "repair", "idv"],
        "text": (
            "A motor loss of Rs. 50,000 or more (Rs. 1 lakh or more for other retail general policies) must be surveyed by a registered surveyor. The "
            "surveyor must be allocated within 24 hours of the claim report and must submit the survey report within 15 days of allocation; if the "
            "surveyor is late, Rs. 500 per day is payable to the claimant. The insurer must decide within 7 days of receiving the survey report, or "
            "after expiry of 15 days from surveyor allocation, whichever is earlier. The insurer cannot repudiate a claim in full or in part where the "
            "breach of a warranty or condition is not relevant to the nature or circumstances of the loss, or for a delay by the policyholder that "
            "did not increase the assessed loss. Interest at Bank Rate plus 2% per annum applies if the claim is not settled in time."
        ),
        "source": f"{PPI}, Part C",
    },
    {
        "id": "life_tat",
        "title": "Life insurance claim timelines",
        "keywords": ["life", "death claim", "nominee", "maturity", "surrender", "term plan", "lic", "death"],
        "text": (
            "A death claim must be settled within 15 days of the date of intimation, or within 45 days where an investigation is warranted. A "
            "surrender or partial withdrawal request must be processed within 7 days of receipt. Interest at Bank Rate plus 2% per annum is payable "
            "from the date of receipt of intimation until payment if the claim is not settled in time."
        ),
        "source": f"{PPI}, Part A",
    },
    {
        "id": "unclaimed_amounts",
        "title": "Unclaimed amounts",
        "keywords": ["unclaimed", "forgotten", "old policy", "lying with insurer", "maturity amount"],
        "text": (
            "Amounts payable to policyholders that remain unpaid for twelve months because the policyholder cannot be contacted are treated as "
            "unclaimed amounts. Insurers must offer a searchable facility on their websites for unclaimed amounts of Rs. 1,000 or more. Amounts "
            "unclaimed for more than 10 years are transferred to the Senior Citizens' Welfare Fund, and consumers can claim them up to 25 years "
            "from the date of transfer."
        ),
        "source": f"{OPS}, clauses 29 and 30",
    },
    {
        "id": "multiple_policies",
        "title": "Claims under more than one health policy",
        "keywords": ["two policies", "multiple policies", "more than one policy", "double", "another policy"],
        "text": (
            "Under indemnity policies, a policyholder can claim under any policy of choice, and that insurer is the primary insurer. If its cover is "
            "less than the admissible claim, it must coordinate with the other insurers to settle the balance without hassle to the policyholder. "
            "Under benefit-based policies, the policyholder can claim from all insurers."
        ),
        "source": f"{HC}, Para 18",
    },
]

APP_PAGES_FACT = {
    "id": "app_pages",
    "title": "RedoClaim pages",
    "keywords": ["redoclaim", "app", "page", "feature", "where", "tool", "dashboard", "click", "find", "open"],
    "text": (
        "RedoClaim pages: "
        + "; ".join(f"{label} ({route})" for route, label in APP_PAGES.items())
        + ". These are the only pages RedoClaim has."
    ),
    "source": "RedoClaim",
}

_TOKEN = re.compile(r"[a-z0-9\-]+")


def retrieve_facts(query: str, history_text: str = "", limit: int = 4) -> list:
    haystack = f" {query.lower()} {history_text.lower()} "
    primary = query.lower()
    scored = []
    for fact in FACTS + [APP_PAGES_FACT]:
        score = 0
        for keyword in fact["keywords"]:
            if keyword in primary:
                score += 3
            elif keyword in haystack:
                score += 1
        if score:
            scored.append((score, fact))
    scored.sort(key=lambda item: item[0], reverse=True)
    chosen = [fact for _, fact in scored[:limit]]
    if not any(f["id"] == "app_pages" for f in chosen):
        chosen = chosen[: limit - 1] + [APP_PAGES_FACT] if len(chosen) >= limit else chosen + [APP_PAGES_FACT]
    return chosen


def strong_match(query: str) -> bool:
    primary = query.lower()
    return any(keyword in primary for fact in FACTS for keyword in fact["keywords"] if len(keyword) > 3)


def facts_text(facts: list) -> str:
    return "\n\n".join(f"[{f['title']}] {f['text']} (Source: {f['source']})" for f in facts)
