"""
Estimated eligible amount — pure arithmetic over policy clauses your Policy
Analyzer already extracted (sum insured, co-payment, sub-limits, room rent
cap), applied to a claim amount.

Deliberately NOT another LLM call. Every deduction names the clause it came
from and the value that was extracted, so a user (or their lawyer) can check
it against the policy. Anything we can't compute from the data we have is
listed as an assumption — and when key clauses are missing, we decline to
give a number at all rather than echo the claim amount back with a range.

This is NOT a prediction of the actual settlement. Insurers assess claims
against the itemised bill, the full policy and their own processes.
"""
import re

RESULT_LABEL = "Estimated eligible amount (not a settlement)"

_UNITS = {"lakh": 100_000, "lakhs": 100_000, "lac": 100_000, "lacs": 100_000,
          "crore": 10_000_000, "crores": 10_000_000, "cr": 10_000_000}
_AMOUNT_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr)?\b", re.I)


def _is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in ("", "n/a", "na", "not specified", "not mentioned", "unknown")
    if isinstance(value, (dict, list)):
        return len(value) == 0
    return False


def _parse_percentage(value) -> float | None:
    """'20%' / 'NIL' / 20 → float percent. 0.0 for NIL/none, None if blank or unparseable."""
    if _is_blank(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().lower()
    if s in ("nil", "none", "0", "0%"):
        return 0.0
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", s)
    return float(match.group(1)) if match else None


def _find_amounts(value) -> list[float]:
    """All rupee amounts found in a string, in order of appearance. Bare numbers < 1000 with no unit are ignored."""
    if isinstance(value, (int, float)):
        return [float(value)]
    if _is_blank(value):
        return []
    s = str(value)
    amounts = []
    for num, unit in _AMOUNT_RE.findall(s):
        try:
            n = float(num.replace(",", ""))
        except ValueError:
            continue
        if unit:
            amounts.append(n * _UNITS[unit.lower()])
        elif n >= 1000:
            amounts.append(n)
    return amounts


def _parse_amount(value) -> float | None:
    """First usable rupee amount, or None if uncapped/unparseable ('NIL', 'no limit', 'As per schedule')."""
    if isinstance(value, str) and re.search(r"\b(nil|no limit|unlimited)\b", value, re.I):
        return None
    amounts = _find_amounts(value)
    return amounts[0] if amounts else None


def _age_threshold(applies_to: str) -> int | None:
    """Pull an age threshold out of text like 'applicable only if insured age >= 60 years'."""
    m = re.search(r"age[^0-9]{0,30}(\d{2,3})", applies_to, re.I) or \
        re.search(r"(\d{2,3})\s*(?:\+|years|yrs|and above|or above|or older)", applies_to, re.I)
    return int(m.group(1)) if m else None


def estimate_payout(claim_amount: float, extracted_clauses: dict, patient_age: int | None = None) -> dict:
    extracted_clauses = extracted_clauses or {}
    deductions: list[dict] = []
    assumptions: list[str] = []
    missing: list[str] = []
    uncomputed = 0  # unresolved factors that widen the range
    remaining = claim_amount

    # ── Sum insured cap ──────────────────────────────────────────
    raw_si = extracted_clauses.get("sum_insured")
    si_amounts = _find_amounts(raw_si)
    sum_insured = _parse_amount(raw_si)
    if sum_insured is None:
        missing.append("sum insured (could not read an amount from the policy)")
    else:
        if len(set(si_amounts)) > 1:
            assumptions.append(
                f"The sum-insured clause mentions more than one amount ('{raw_si}'). We used the first "
                f"(₹{sum_insured:,.0f}). Please check which figure applies to you."
            )
            uncomputed += 1
        if claim_amount > sum_insured:
            deductions.append({
                "reason": "Claim exceeds policy sum insured",
                "amount": round(claim_amount - sum_insured, 2),
                "clause": "Sum insured",
                "extracted_value": str(raw_si),
            })
            remaining = sum_insured

    # ── Room rent cap — flagged, not computed ────────────────────
    room_rent = extracted_clauses.get("room_rent_cap")
    if isinstance(room_rent, str):
        room_rent = {"limit": room_rent, "type": "stated"} if not _is_blank(room_rent) else None
    if _is_blank(room_rent) or not isinstance(room_rent, dict):
        missing.append("room-rent cap (not extracted)")
    elif room_rent.get("type") not in (None, "none", ""):
        assumptions.append(
            f"Room rent cap of {room_rent.get('limit', 'unspecified')} applies. If your actual room rent "
            "exceeded this, insurers typically apply a *proportionate deduction* across the entire bill, "
            "not just the room charge — this estimate does NOT calculate that reduction since it needs your "
            "actual room rent and full bill breakup. Treat this estimate as an upper bound if you stayed in "
            "a higher room category than the cap allows."
        )
        uncomputed += 1

    # ── Co-payment ────────────────────────────────────────────────
    co_pay = extracted_clauses.get("co_payment")
    if isinstance(co_pay, str):
        co_pay = {"percentage": co_pay}
    if _is_blank(co_pay) or not isinstance(co_pay, dict):
        missing.append("co-payment (not extracted — may be nil or may apply)")
        co_pay_pct = 0.0
        co_pay = {}
    else:
        co_pay_pct = _parse_percentage(co_pay.get("percentage"))
        if co_pay_pct is None:
            missing.append("co-payment percentage (could not be read)")
            co_pay_pct = 0.0
    applies_to = (co_pay.get("applies_to") or "").strip()
    if co_pay_pct > 0:
        threshold = _age_threshold(applies_to) if applies_to else None
        age_conditional = threshold is not None or bool(re.search(r"\bage\b", applies_to, re.I))
        apply_copay = True
        if age_conditional and patient_age is None:
            missing.append("patient age (the co-payment depends on age)")
            assumptions.append(
                f"The {co_pay_pct:.0f}% co-payment depends on age ('{applies_to}') but no age was entered. "
                "It is deducted below as a precaution — enter the patient's age to refine this."
            )
            uncomputed += 1
        elif threshold is not None and patient_age is not None and patient_age < threshold:
            assumptions.append(
                f"Policy has a {co_pay_pct:.0f}% co-payment for age {threshold}+, but the patient age given "
                f"({patient_age}) is below that — co-payment likely does NOT apply, so it is not deducted below."
            )
            apply_copay = False
        elif applies_to and not age_conditional:
            assumptions.append(
                f"The co-payment is conditional ('{applies_to}'). It is deducted below; please check whether "
                "that condition applies to your case."
            )
            uncomputed += 1
        if apply_copay:
            cut = remaining * (co_pay_pct / 100)
            deductions.append({
                "reason": f"Co-payment ({co_pay_pct:.0f}%)" + (f" — {applies_to}" if applies_to else ""),
                "amount": round(cut, 2),
                "clause": "Co-payment",
                "extracted_value": f"{co_pay.get('percentage')}" + (f", {applies_to}" if applies_to else ""),
            })
            remaining -= cut

    # ── Sub-limits — flagged per item, not deducted ──────────────
    for sl in (extracted_clauses.get("sub_limits") or []):
        if _parse_amount(sl.get("limit")) is not None:
            assumptions.append(
                f"Sub-limit on '{sl.get('item', 'this item')}': capped at {sl.get('limit')}. If this "
                "specific item's actual cost exceeded that cap, the excess isn't payable — not deducted "
                "here since we don't have your itemized hospital bill."
            )
            uncomputed += 1

    # ── Pre-existing disease waiting period — risk flag, not a number ──
    ped_waiting = extracted_clauses.get("pre_existing_disease_waiting")
    if not _is_blank(ped_waiting) and str(ped_waiting).strip().lower() not in ("nil", "none"):
        assumptions.append(
            f"Pre-existing disease waiting period on file: {ped_waiting}. If this claim relates to a "
            "pre-existing condition still within that period, the ENTIRE claim may be excluded — this "
            "estimate assumes that is not the case."
        )
        uncomputed += 1

    # ── Always-on limitations ────────────────────────────────────
    assumptions.append(
        "Not considered: earlier claims in this policy year that may have reduced your available sum insured, "
        "items the insurer treats as non-payable, any deductible, and exclusions or waiting periods other "
        "than those listed above."
    )

    # ── Can we responsibly give a number? ────────────────────────
    can_estimate = sum_insured is not None or not _is_blank(co_pay)
    confidence = "insufficient" if not can_estimate else ("low" if missing or uncomputed >= 3 else "moderate")

    base = {
        "claim_amount": claim_amount,
        "label": RESULT_LABEL,
        "can_estimate": can_estimate,
        "confidence": confidence,
        "missing_inputs": missing,
        "assumptions": assumptions,
        "disclaimer": (
            "This is a rough estimate of the amount that may be eligible under the policy clauses this tool "
            "extracted from your document. It is NOT the actual settlement. The insurer's own assessment — "
            "against your itemised bill, the full policy terms and its internal process — may differ, "
            "including paying less, more, or nothing. The tool may also have misread or missed clauses. "
            "Treat this as an informational aid only and confirm with your insurer."
        ),
    }

    if not can_estimate:
        return {**base, "estimated_payout": None, "estimated_payout_range": None,
                "total_deductions": None, "deductions": [], "range_note": None}

    remaining = max(remaining, 0.0)
    width = min(0.05 + 0.05 * uncomputed + (0.05 if missing else 0.0), 0.35)
    return {
        **base,
        "estimated_payout": round(remaining, 2),
        "estimated_payout_range": [round(remaining * (1 - width), 2), round(remaining, 2)],
        "total_deductions": round(sum(d["amount"] for d in deductions), 2),
        "deductions": deductions,
        "range_note": (
            f"The lower end is {width * 100:.0f}% below the upper end, widening with each unresolved factor "
            "listed above. It is a rough band, not a guaranteed floor — actual deductions can be larger."
        ),
    }
