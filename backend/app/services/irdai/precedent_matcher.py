"""
Legal Precedent Matcher — a curated, static library of real Ombudsman and
consumer-forum judgment summaries, matched to a user's fact pattern by
rejection category and keyword overlap. No LLM call for the matching
itself — this is closer to a compiled case-law index than a generative
task, and a bare regulation citation is far less persuasive than "3
policyholders won near-identical cases."

Case summaries are illustrative/representative of well-known precedent
patterns — always verify current citation validity before relying on one
in an actual filing, since case law updates and specific case numbers
should be confirmed against primary sources (Ombudsman award archives,
NCDRC/SCDRC judgment databases).
"""
import re

PRECEDENTS = [
    {
        "id": "swaran-singh-2004",
        "category": "motor",
        "case_name": "National Insurance Co. Ltd. v. Swaran Singh & Ors. (2004)",
        "court": "Supreme Court of India",
        "keywords": ["driving licence", "driving license", "expired licence", "invalid licence", "motor claim rejected"],
        "summary": (
            "Held that an insurer cannot repudiate a motor claim solely on a technical defect in the driver's "
            "licence unless the insurer proves the defect was material to the cause of the accident and that "
            "the policyholder was aware of it. A minor procedural lapse alone is insufficient grounds for denial."
        ),
        "how_to_use": "Cite when a motor claim is rejected purely for a licence technicality with no proven link to the accident cause.",
    },
    {
        "id": "moratorium-60-months",
        "category": "health",
        "case_name": "IRDAI Health Insurance Regulations — Moratorium Provision",
        "court": "IRDAI (Regulatory, applied consistently in Ombudsman awards)",
        "keywords": ["non-disclosure", "pre-existing disease", "60 months", "5 years", "moratorium", "concealment"],
        "summary": (
            "IRDAI health-insurance material describes a moratorium of 60 continuous months. Once a health policy has been continuously "
            "renewed for that period, a claim cannot be repudiated for non-disclosure or misrepresentation except "
            "in cases of clearly established, deliberate fraud — mere non-disclosure alone does not suffice "
            "after the moratorium period."
        ),
        "how_to_use": "Consider when a rejection for non-disclosure/PED comes after 60+ continuous months of coverage; verify the provision and the continuity of cover first.",
    },
    {
        "id": "incontestability-3-year",
        "category": "life",
        "case_name": "Life Insurance Corporation of India v. various — Section 45 Incontestability line of cases",
        "court": "Various High Courts / Supreme Court",
        "keywords": ["life insurance", "3 years", "misstatement", "fraud", "incontestable"],
        "summary": (
            "Courts have repeatedly held that after a life policy has run for 3 years, the burden shifts sharply "
            "to the insurer to prove deliberate, fraudulent suppression of a MATERIAL fact — an honest mistake or "
            "an immaterial omission does not justify repudiation at this stage."
        ),
        "how_to_use": "Cite when a life/death claim is repudiated for non-disclosure after the policy has run 3+ years.",
    },
    {
        "id": "room-rent-proportionate",
        "category": "health",
        "case_name": "Representative Ombudsman awards on proportionate deduction disputes",
        "court": "Insurance Ombudsman (multiple centers)",
        "keywords": ["room rent", "proportionate deduction", "sub-limit", "cap"],
        "summary": (
            "Ombudsman awards have frequently corrected insurer calculations where a proportionate deduction was "
            "applied incorrectly — either deducted from the wrong base, applied twice, or calculated using the "
            "wrong eligible-rent figure — resulting in the policyholder being awarded the shortfall."
        ),
        "how_to_use": "Cite when disputing a room-rent-cap deduction that looks miscalculated against the policy's own stated formula.",
    },
    {
        "id": "cashless-tat-breach",
        "category": "health",
        "case_name": "Representative awards on cashless facility TAT breaches",
        "court": "Insurance Ombudsman (multiple centers)",
        "keywords": ["cashless", "pre-authorization", "delay", "tat", "turnaround time"],
        "summary": (
            "Cases where an insurer/TPA failed to respond to a cashless request within the IRDAI-mandated "
            "turnaround time (1 hour initial, 3 hours discharge) have been treated as a service deficiency in "
            "their own right, independent of whether the underlying treatment was otherwise covered."
        ),
        "how_to_use": "Cite alongside a pre-authorization denial when the insurer also breached the response-time requirement.",
    },
    {
        "id": "repeated-document-demands",
        "category": "general",
        "case_name": "Representative awards on serial document requisition as a delay tactic",
        "court": "Insurance Ombudsman (multiple centers)",
        "keywords": ["documents", "delay", "repeated requests", "more documents", "insufficient documentation"],
        "summary": (
            "Where an insurer repeatedly requested additional documents in successive rounds over an extended "
            "period without a final decision, this pattern has been treated as an unreasonable delay amounting "
            "to deficiency in service, separate from the merits of the claim itself."
        ),
        "how_to_use": "Cite when a claim has been stuck in repeated 'more documents needed' cycles for an extended period.",
    },
]


def match_precedents(rejection_category: str, free_text: str = "", limit: int = 3) -> list[dict]:
    """
    Matches by category first (exact or 'general'), then ranks by keyword
    overlap with the free_text fact pattern the user provides (e.g. the
    rejection letter text or a short description of their situation).
    """
    text = (free_text or "").lower()
    category = (rejection_category or "").lower()

    scored = []
    for p in PRECEDENTS:
        if p["category"] not in (category, "general"):
            continue
        score = 1 if p["category"] == category else 0  # category match is worth more than keyword match
        score += sum(1 for kw in p["keywords"] if kw in text)
        if score > 0 or not text:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:limit]]
