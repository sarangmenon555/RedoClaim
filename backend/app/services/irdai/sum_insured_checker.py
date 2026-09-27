"""
Sum Insured Adequacy Checker — deterministic. Compares a policy's sum
insured against static, compiled benchmark figures (typical hospitalization
costs by city tier and family composition) rather than calling an LLM,
since this is a lookup-and-compare problem, not a judgment problem.

Benchmark figures are approximate, compiled once from general healthcare
cost surveys — NOT a live pricing feed. Treat as a sanity-check floor, not
a precise recommendation.
"""

# Approximate benchmark hospitalization cost (₹) for a single major medical
# event (e.g. a cardiac procedure or major surgery), by city tier. These are
# static, compiled estimates — meant as a floor check, not a precise figure.
CITY_TIER_BASE_COST = {
    "metro": 800_000,      # Delhi NCR, Mumbai, Bengaluru, Chennai, Kolkata, Hyderabad, Pune
    "tier1": 500_000,      # other state capitals, large cities
    "tier2": 300_000,      # smaller cities and towns
}

# Age-based multiplier — older members have statistically higher-cost
# treatment needs (cardiac, orthopedic, oncology being the common big-ticket ones).
def _age_multiplier(age: int) -> float:
    if age >= 60:
        return 1.6
    if age >= 45:
        return 1.3
    if age >= 18:
        return 1.0
    return 0.8  # children — typically lower average cost per episode


def check_sum_insured_adequacy(
    sum_insured: float,
    city_tier: str,
    family_members: list[dict],  # [{"age": 34, "relationship": "self"}, ...]
) -> dict:
    """
    family_members: list of {"age": int}. For a family floater, the
    benchmark uses the OLDEST member's age multiplier, since that member
    drives the highest-risk cost scenario the sum insured needs to cover.
    """
    city_tier = city_tier if city_tier in CITY_TIER_BASE_COST else "tier1"
    base_cost = CITY_TIER_BASE_COST[city_tier]

    oldest_age = max((m.get("age", 30) for m in family_members), default=30)
    multiplier = _age_multiplier(oldest_age)

    recommended_minimum = round(base_cost * multiplier, -3)  # round to nearest 1000
    # For a family floater covering multiple members, add a buffer since
    # sum insured is shared across everyone on the policy.
    if len(family_members) > 1:
        recommended_minimum = round(recommended_minimum * (1 + 0.25 * (len(family_members) - 1)), -3)

    ratio = sum_insured / recommended_minimum if recommended_minimum else 0

    if ratio >= 1.2:
        verdict = "adequate"
        headline = "Your sum insured looks comfortably adequate for your city tier and family profile."
    elif ratio >= 0.8:
        verdict = "borderline"
        headline = "Your sum insured is roughly in range, but a single major hospitalization could still stretch it thin."
    else:
        verdict = "likely_inadequate"
        headline = "Your sum insured looks low relative to typical major-treatment costs for your profile — consider a top-up or super top-up policy."

    return {
        "sum_insured": sum_insured,
        "city_tier": city_tier,
        "family_size": len(family_members),
        "oldest_member_age": oldest_age,
        "recommended_minimum": recommended_minimum,
        "adequacy_ratio": round(ratio, 2),
        "verdict": verdict,
        "headline": headline,
        "disclaimer": (
            "Based on approximate, compiled benchmark hospitalization costs by city tier and age — not a live "
            "pricing feed or medical cost database. Treat this as a rough sanity check, not a precise "
            "recommendation; actual treatment costs vary widely by hospital, procedure, and city."
        ),
    }
