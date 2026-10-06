"""
Evidence sufficiency gate - RedoClaim.

Problem this solves: with an incomplete policy and a vague rejection letter,
the pipeline used to jump straight to "potential regulatory inconsistency" and
a "Deficiency in Service" classification. The correct order is:

    1. Is there enough evidence to judge anything?   -> INSUFFICIENT EVIDENCE
    2. What is missing?                              -> evidence gaps
    3. Only then: possible issues requiring verification.

Pure, deterministic logic - no LLM call. Combines what the documents actually
contain with the model's own `evidence_status` (if it returned one).
"""
import re
from typing import Optional

# Phrases that indicate the rejection letter points at a specific provision.
_PROVISION_PATTERNS = [
    r"\bclause\s*(no\.?)?\s*[\w.\-()]+",
    r"\bsection\s*\d+",
    r"\bexclusion\s*(no\.?|code)?\s*\d+",
    r"\bexclusion\s+[a-z]\)",
    r"\bpara(graph)?\s*\d+",
    r"\barticle\s*\d+",
    r"\bwaiting period of\s*\d+",
    r"\b\d+\s*(day|month|year)s?\s+waiting period",
    r"\bpre[- ]?existing\b.{0,80}\b(\d+\s*(month|year)s?)",
    r"\bsub[- ]?limit\b.{0,60}\d",
    r"\bco[- ]?pay(ment)?\b.{0,40}\d+\s*%",
    r"\bpolicy (wording|term|condition)s?\s*(no\.?)?\s*\d+",
]
_PROVISION_RE = re.compile("|".join(_PROVISION_PATTERNS), re.IGNORECASE)

SUFFICIENT = "sufficient"
PARTIAL = "partial"
INSUFFICIENT = "insufficient"

DEFAULT_DOCS_TO_OBTAIN = [
    "Complete policy wording / schedule including all exclusions and waiting periods",
    "The insurer's full rejection letter naming the specific clause relied on",
    "Hospital discharge summary and treatment records",
    "Claim form and all documents submitted to the insurer",
    "Customer Information Sheet (CIS) issued with the policy",
]


def _policy_has_substance(policy_clauses: Optional[dict]) -> bool:
    if not policy_clauses:
        return False
    for key in ("exclusions", "waiting_periods", "inclusions", "sub_limits"):
        if policy_clauses.get(key):
            return True
    return False


def assess_evidence(
    rejection_text: str,
    policy_clauses: Optional[dict],
    audit_result: Optional[dict] = None,
    cis_provided: bool = False,
) -> dict:
    """
    Returns:
      status          sufficient | partial | insufficient
      gaps            list[str]  what is missing, in plain words
      documents_to_obtain list[str]
      summary         one neutral sentence for the UI
    """
    audit_result = audit_result or {}
    gaps: list[str] = []

    policy_ok = _policy_has_substance(policy_clauses)
    if not policy_ok:
        gaps.append(
            "The policy wording supplied is missing or too incomplete to identify the "
            "exclusions or waiting periods the insurer may rely on."
        )

    text = rejection_text or ""
    names_provision = bool(_PROVISION_RE.search(text))
    if not names_provision:
        gaps.append(
            "The rejection does not identify the specific policy provision or exclusion "
            "it relies on."
        )

    if len(text.strip()) < 80:
        gaps.append("The rejection text is very short, so the reasons given are unclear.")

    # The model may flag insufficiency itself (it sees the full context).
    llm_status = str(audit_result.get("evidence_status") or "").lower()
    for g in (audit_result.get("evidence_gaps") or []):
        if isinstance(g, str) and g.strip() and g.strip() not in gaps:
            gaps.append(g.strip())

    if llm_status == INSUFFICIENT or (not policy_ok and not names_provision):
        status = INSUFFICIENT
    elif gaps or llm_status == PARTIAL:
        status = PARTIAL
    else:
        status = SUFFICIENT

    docs = list(audit_result.get("evidence_needed") or [])
    for d in DEFAULT_DOCS_TO_OBTAIN:
        if d not in docs and (status != SUFFICIENT):
            if d.startswith("Customer Information Sheet") and cis_provided:
                continue
            docs.append(d)

    summaries = {
        INSUFFICIENT: (
            "INSUFFICIENT EVIDENCE: the documents supplied are not enough to judge whether "
            "the rejection is consistent with the policy or with any regulatory requirement."
        ),
        PARTIAL: (
            "PARTIAL EVIDENCE: some findings below are provisional because parts of the "
            "supporting documents are missing."
        ),
        SUFFICIENT: "The documents supplied cover the reasons given for the rejection.",
    }
    return {
        "status": status,
        "gaps": gaps,
        "documents_to_obtain": docs,
        "summary": summaries[status],
    }


def apply_insufficient_evidence(audit_result: dict, assessment: dict) -> dict:
    """
    When evidence is INSUFFICIENT, demote legal-sounding findings to
    'possible issues requiring verification' so the product reports
    uncertainty first rather than legal escalation. Mutates and returns audit_result.
    """
    if assessment["status"] != INSUFFICIENT:
        return audit_result

    findings = audit_result.get("step2_regulatory_violations") or []
    audit_result["possible_issues_to_verify"] = [
        {
            "issue": f.get("violation") or f.get("issue") or "",
            "source": f.get("source") or f.get("regulation"),
            "note": (
                "Possible issue requiring verification once the missing documents are "
                "obtained. The adequacy of the insurer's explanation may warrant review "
                "under the applicable regulatory or grievance framework."
            ),
        }
        for f in findings if isinstance(f, dict)
    ]
    audit_result["step2_regulatory_violations"] = []
    audit_result["is_valid_rejection"] = None
    audit_result["strength_of_case"] = "insufficient"
    audit_result["strength_reasoning"] = assessment["summary"]
    audit_result["deficiency_in_service"] = False
    audit_result["product_liability_applicable"] = False
    audit_result["key_arguments"] = []
    audit_result["evidence_needed"] = assessment["documents_to_obtain"]
    redress = audit_result.get("step3_redressal") or {}
    redress["recommended_action"] = "gather_documents"
    redress["ejagriti_applicable"] = False
    redress["reasoning"] = (
        "Obtain the missing documents first and ask the insurer, in writing, to identify the "
        "exact provision relied on. Decide on any escalation after that."
    )
    audit_result["step3_redressal"] = redress
    return audit_result
