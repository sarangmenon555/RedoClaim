"""
No-Claim Bonus (NCB) Calculator — motor insurance, pure arithmetic. IRDAI
mandates a standard NCB slab structure that applies uniformly across
insurers for private car/two-wheeler own-damage premium. A renewal quote
that doesn't reflect the NCB a policyholder has earned is a common, quiet
downgrade — distinct from the health-focused Renewal Red-Flag Checker.
"""

# IRDAI-mandated standard NCB slabs for private car / two-wheeler policies —
# uniform across insurers, cumulative with each claim-free year, capped at 50%.
NCB_SLABS = [
    (0, 0),
    (1, 20),
    (2, 25),
    (3, 35),
    (4, 45),
    (5, 50),  # cap — does not increase beyond 50% regardless of further claim-free years
]


def _expected_ncb_percent(claim_free_years: int) -> int:
    years = max(0, min(claim_free_years, 5))
    for slab_years, pct in reversed(NCB_SLABS):
        if years >= slab_years:
            return pct
    return 0


def calculate_ncb(
    claim_free_years: int,
    od_premium_before_ncb: float,
    ncb_applied_by_insurer: float,
    had_claim_this_year: bool = False,
) -> dict:
    """
    claim_free_years: consecutive years without a claim on THIS policy
        (NCB is tied to the policyholder's claim history, and is portable
        across insurers with a valid NCB retention certificate — not tied
        to staying with the same insurer).
    od_premium_before_ncb: the Own Damage premium the insurer quoted BEFORE
        applying any NCB discount (shown separately in every motor quote).
    ncb_applied_by_insurer: the NCB percentage the insurer actually applied
        on this renewal quote.
    had_claim_this_year: if a claim was made in the immediately preceding
        year, NCB resets to 0% for the upcoming renewal — this is correct
        insurer behavior, not a downgrade.
    """
    if had_claim_this_year:
        expected_pct = 0
        note = "A claim was made in the preceding year, so NCB correctly resets to 0% for this renewal — this is standard, not a downgrade."
    else:
        expected_pct = _expected_ncb_percent(claim_free_years)
        note = None

    expected_discount = round(od_premium_before_ncb * (expected_pct / 100), 2)
    actual_discount = round(od_premium_before_ncb * (ncb_applied_by_insurer / 100), 2)
    shortfall = round(expected_discount - actual_discount, 2)

    is_shortchanged = shortfall > 1  # tolerate rounding noise

    return {
        "claim_free_years": claim_free_years,
        "expected_ncb_percent": expected_pct,
        "ncb_applied_by_insurer": ncb_applied_by_insurer,
        "expected_discount_amount": expected_discount,
        "actual_discount_amount": actual_discount,
        "shortfall_amount": max(shortfall, 0),
        "is_shortchanged": is_shortchanged,
        "note": note or (
            f"You're eligible for {expected_pct}% NCB but the quote applies only {ncb_applied_by_insurer}%. "
            f"This under-application is worth ₹{shortfall:,.0f} on this renewal — worth raising with the insurer."
            if is_shortchanged else
            f"The {ncb_applied_by_insurer}% NCB applied matches the calculated NCB after {claim_free_years} claim-free year(s)."
        ),
        "ncb_is_portable": "NCB is tied to you, not the insurer — a valid NCB retention/transfer certificate from your outgoing insurer lets you carry it to a new insurer without losing it.",
        "disclaimer": (
            "Based on IRDAI's standard NCB slab structure for private car/two-wheeler own-damage premium. "
            "Confirm the exact OD premium base and any add-on-specific NCB rules with your insurer's quote breakdown."
        ),
    }
