"""
Claim Prioritisation Aid ("Is it worth pursuing?") — rule-based and
deterministic, reusing a claim's ALREADY-COMPUTED audit_report
(strength_of_case, regulatory inconsistencies found, suggested redressal
route). No new LLM call.

This is an INFORMATIONAL aid. It lays out the factors side by side
(case strength rated by the Auditor, inconsistencies found, the suggested
route and its rough effort). It deliberately does NOT:
  - output a verdict such as "worth fighting" / "not worth fighting",
  - predict the outcome, or
  - let a small claim amount lower the result — whether to pursue a
    grievance is the user's decision.

If the audit lacks the inputs, it says so instead of defaulting to a verdict.
"""

# Rough hours of the user's own time if self-filed — a static assumption.
_ROUTE_EFFORT_HOURS = {
    "gro_appeal": 2,
    "ombudsman": 6,
    "consumer_court": 15,
    "accept": 0,
}

_ROUTE_LABELS = {
    "gro_appeal": "Insurer's Grievance Redressal Officer (GRO)",
    "ombudsman": "Insurance Ombudsman",
    "consumer_court": "Consumer Forum / District Commission",
    "accept": "No escalation route suggested by the audit",
}

_STRENGTH_LABELS = {"strong", "moderate", "weak"}

STANDARD_NOTICE = (
    "This is an informational prioritisation aid, not a recommendation that you should or should not pursue "
    "your rights."
)


def advise_cost_benefit(
    claim_amount: float,
    audit_report: dict,
    hourly_value: float = 500.0,  # kept for API compatibility; no longer used
) -> dict:
    audit_report = audit_report or {}

    strength_raw = str(audit_report.get("strength_of_case") or "").strip().lower()
    strength = strength_raw if strength_raw in _STRENGTH_LABELS else None
    route_raw = (audit_report.get("step3_redressal") or {}).get("recommended_action")
    route = route_raw if route_raw in _ROUTE_EFFORT_HOURS else None
    violations = audit_report.get("step2_regulatory_violations")

    missing = []
    if strength is None:
        missing.append("case-strength rating")
    if route is None:
        missing.append("suggested redressal route")
    if violations is None:
        missing.append("regulatory review results")
    violation_count = len(violations or [])

    effort_hours = _ROUTE_EFFORT_HOURS.get(route) if route else None
    route_label = _ROUTE_LABELS.get(route) if route else None

    factors = [
        {"label": "Claim amount", "value": f"₹{claim_amount:,.0f}"},
        {"label": "Case strength rated by the Auditor", "value": strength.capitalize() if strength else "Not available"},
        {
            "label": "Potential regulatory inconsistencies identified",
            "value": str(violation_count) if violations is not None else "Not available",
        },
        {"label": "Route suggested by the audit", "value": route_label or "Not available"},
        {
            "label": "Rough effort if you file yourself",
            "value": f"~{effort_hours} hour(s)" if effort_hours is not None else "Not available",
        },
    ]

    if missing:
        headline = "Not enough information in the audit to lay out these factors reliably."
        reasoning = "Missing: " + ", ".join(missing) + ". Re-run the Auditor on this claim to fill these in."
    else:
        headline = "Here are the factors to weigh — the decision is yours."
        reasoning = (
            f"The Auditor rated the case '{strength}' and identified {violation_count} potential regulatory "
            f"inconsistency(ies). The route suggested by the audit is {route_label}, which we roughly estimate "
            f"at {effort_hours} hour(s) of your own time if self-filed. The claim amount is ₹{claim_amount:,.0f}. "
            "These factors are shown side by side; none is weighted against your right to raise a grievance."
        )

    return {
        "claim_amount": claim_amount,
        "case_strength": strength,
        "recommended_route": route,
        "recommended_route_label": route_label,
        "estimated_effort_hours": effort_hours,
        "regulatory_violations_found": violation_count,
        "potential_inconsistencies_found": violation_count,
        "verdict": "insufficient_information" if missing else "informational",
        "insufficient_information": bool(missing),
        "missing_inputs": missing,
        "headline": headline,
        "factors": factors,
        "reasoning": reasoning,
        "standard_notice": STANDARD_NOTICE,
        "disclaimer": (
            f"{STANDARD_NOTICE} It is not a prediction of outcome. Case strength comes from the AI-assisted audit "
            "and may be wrong. Effort figures are rough, static assumptions. Official routes such as the GRO and "
            "Ombudsman are free to file yourself; a Consumer Forum complaint may involve nominal fees. Check each "
            "channel's current official eligibility rules before filing."
        ),
    }
