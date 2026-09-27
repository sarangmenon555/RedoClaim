"""
Claim Cost-Benefit Advisor — pure arithmetic + rule-based logic over a
claim's ALREADY-COMPUTED audit_report (strength_of_case, IRDAI violations
found, recommended redressal route). No new LLM call: the audit engine
already did the hard judgment work when it first analyzed the rejection;
this just weighs that judgment against effort/cost to give a plain
"is this worth fighting" verdict.

Time/effort estimates below are rough, static assumptions (self-filing via
GRO/Ombudsman/E-Daakhil is free and doesn't strictly require a lawyer) —
clearly labeled as such so the user can adjust their own judgment.
"""

# Effort estimates for redressal routes: hours of the user's own time, if
# self-filed (which is how GRO, Ombudsman, and E-Daakhil are designed to be
# used — no lawyer fee is assumed).
_ROUTE_EFFORT_HOURS = {
    "gro_appeal": 2,
    "ombudsman": 6,
    "consumer_court": 15,
    "accept": 0,
}

_ROUTE_LABELS = {
    "gro_appeal": "GRO Appeal (insurer's Grievance Redressal Officer)",
    "ombudsman": "Insurance Ombudsman",
    "consumer_court": "Consumer Forum / District Commission",
    "accept": "Accept the insurer's decision",
}

_STRENGTH_SCORE = {"strong": 3, "moderate": 2, "weak": 1}


def advise_cost_benefit(
    claim_amount: float,
    audit_report: dict,
    hourly_value: float = 500.0,
) -> dict:
    """
    hourly_value: what the user's own time is roughly worth per hour, for
    converting effort into a comparable rupee figure. Defaults to a modest
    ₹500/hr — the user can override this in the UI.
    """
    audit_report = audit_report or {}
    strength = (audit_report.get("strength_of_case") or "moderate").lower()
    recommended_route = (audit_report.get("step3_redressal", {}) or {}).get("recommended_action", "gro_appeal")
    violations = audit_report.get("step2_regulatory_violations") or []
    is_valid_rejection = audit_report.get("is_valid_rejection", True)

    effort_hours = _ROUTE_EFFORT_HOURS.get(recommended_route, 4)
    effort_cost = effort_hours * hourly_value

    strength_score = _STRENGTH_SCORE.get(strength, 2)
    # Simple weighting: stronger case + more regulatory violations found +
    # larger claim amount all push toward "worth fighting". This is a
    # transparent scoring rule, not a hidden model — the reasoning is shown
    # to the user alongside the verdict.
    violation_bonus = min(len(violations), 3) * 0.5
    amount_factor = min(claim_amount / max(effort_cost, 1), 10)  # cap influence

    score = strength_score + violation_bonus + min(amount_factor, 5)

    if is_valid_rejection is True and strength == "weak" and not violations:
        verdict = "not_worth_fighting"
        headline = "The insurer's decision appears to hold up — fighting this is unlikely to succeed."
    elif score >= 6:
        verdict = "strongly_worth_fighting"
        headline = "Strong case relative to the effort required — this is worth pursuing."
    elif score >= 4:
        verdict = "worth_fighting"
        headline = "Reasonable case for the effort involved — worth pursuing, especially since escalation is free."
    else:
        verdict = "marginal"
        headline = "A borderline case — the claim amount is small relative to the effort, but escalation costs nothing but time."

    return {
        "claim_amount": claim_amount,
        "case_strength": strength,
        "recommended_route": recommended_route,
        "recommended_route_label": _ROUTE_LABELS.get(recommended_route, recommended_route),
        "estimated_effort_hours": effort_hours,
        "estimated_effort_value": round(effort_cost, 2),
        "regulatory_violations_found": len(violations),
        "verdict": verdict,
        "headline": headline,
        "reasoning": (
            f"Case strength is rated '{strength}' with {len(violations)} regulatory violation(s) identified. "
            f"The recommended route ({_ROUTE_LABELS.get(recommended_route, recommended_route)}) is estimated to take "
            f"roughly {effort_hours} hour(s) of your own time if self-filed (no lawyer fee assumed) — "
            f"worth about ₹{effort_cost:,.0f} at ₹{hourly_value:,.0f}/hour, against a claim of ₹{claim_amount:,.0f}."
        ),
        "disclaimer": (
            "This is a rough, transparent estimate based on your own time value and the case strength already "
            "computed by the Auditor — not a guarantee of outcome. GRO and Ombudsman routes are free to file "
            "yourself; a Consumer Forum complaint may involve nominal court fees depending on claim value."
        ),
    }
