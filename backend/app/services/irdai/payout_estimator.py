"""
Expected payout estimator — pure arithmetic over policy clauses your
Policy Analyzer already extracted (sum insured, co-payment, sub-limits,
room rent cap), applied to a claim amount.

Deliberately NOT another LLM call: every number here is traceable to a
specific extracted clause, so a user (or their lawyer) can see exactly
why the estimate is what it is. Where a real deduction can't be computed
without data we don't have (e.g. room-rent proportionate deduction needs
the actual room rent and full bill breakup), we say so explicitly as an
assumption rather than inventing a number.
"""
import re


def _parse_percentage(value) -> float:
    """'20%' / 'NIL' / 20 / None → float percent, 0.0 for NIL/unparseable."""
    if not value:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().lower()
    if s in ("nil", "none", "n/a", "0", ""):
        return 0.0
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", s)
    return float(match.group(1)) if match else 0.0


def _parse_amount(value) -> float | None:
    """'₹5,00,000' / 'Rs. 500000' / '5 lakhs' / 'NIL' → float rupees, None if uncapped/unparseable."""
    if not value:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().lower()
    if "nil" in s or "no limit" in s or "unlimited" in s:
        return None
    lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*lakh", s)
    if lakh_match:
        return float(lakh_match.group(1)) * 100_000
    crore_match = re.search(r"(\d+(?:\.\d+)?)\s*crore", s)
    if crore_match:
        return float(crore_match.group(1)) * 10_000_000
    digits = re.sub(r"[^\d.]", "", s)
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def estimate_payout(claim_amount: float, extracted_clauses: dict, patient_age: int | None = None) -> dict:
    """
    Returns an itemized, transparent estimate:
      claim_amount, estimated_payout, estimated_payout_range,
      total_deductions, deductions (each with reason + amount),
      assumptions (things we flagged but couldn't compute precisely),
      disclaimer
    """
    extracted_clauses = extracted_clauses or {}
    deductions: list[dict] = []
    assumptions: list[str] = []
    remaining = claim_amount

    # ── Sum insured cap ──────────────────────────────────────────
    sum_insured = _parse_amount(extracted_clauses.get("sum_insured"))
    if sum_insured is not None and claim_amount > sum_insured:
        cut = claim_amount - sum_insured
        deductions.append({"reason": "Claim exceeds policy sum insured", "amount": round(cut, 2)})
        remaining = sum_insured

    # ── Room rent cap — flagged, not computed (needs actual bill breakup) ──
    room_rent = extracted_clauses.get("room_rent_cap") or {}
    if room_rent and room_rent.get("type") not in (None, "none", ""):
        assumptions.append(
            f"Room rent cap of {room_rent.get('limit', 'unspecified')} applies. If your actual room rent "
            "exceeded this, insurers typically apply a *proportionate deduction* across the entire bill, "
            "not just the room charge — this estimate does NOT calculate that reduction since it needs your "
            "actual room rent and full bill breakup. Treat this estimate as an upper bound if you stayed in "
            "a higher room category than the cap allows."
        )

    # ── Co-payment ────────────────────────────────────────────────
    co_pay = extracted_clauses.get("co_payment") or {}
    co_pay_pct = _parse_percentage(co_pay.get("percentage"))
    applies_to = co_pay.get("applies_to", "") or ""
    if co_pay_pct > 0 and patient_age is not None and applies_to:
        age_match = re.search(r"(\d+)", applies_to)
        if age_match and patient_age < int(age_match.group(1)):
            assumptions.append(
                f"Policy has a {co_pay_pct:.0f}% co-payment for age {age_match.group(1)}+, but the patient "
                f"age given ({patient_age}) is below that — co-payment likely does NOT apply, so it is not "
                "deducted below."
            )
            co_pay_pct = 0.0
    if co_pay_pct > 0:
        cut = remaining * (co_pay_pct / 100)
        deductions.append({
            "reason": f"Co-payment ({co_pay_pct:.0f}%)" + (f" — {applies_to}" if applies_to else ""),
            "amount": round(cut, 2),
        })
        remaining -= cut

    # ── Sub-limits — flagged per item, not deducted (don't have itemized bill) ──
    for sl in (extracted_clauses.get("sub_limits") or []):
        limit_amt = _parse_amount(sl.get("limit"))
        if limit_amt is not None:
            assumptions.append(
                f"Sub-limit on '{sl.get('item', 'this item')}': capped at {sl.get('limit')}. If this "
                "specific item's actual cost exceeded that cap, the excess isn't payable — not deducted "
                "here since we don't have your itemized hospital bill."
            )

    # ── Pre-existing disease waiting period — binary risk flag, not a number ──
    ped_waiting = extracted_clauses.get("pre_existing_disease_waiting")
    if ped_waiting and str(ped_waiting).strip().lower() not in ("nil", "none", "n/a", ""):
        assumptions.append(
            f"Pre-existing disease waiting period on file: {ped_waiting}. If this claim relates to a "
            "pre-existing condition still within that period, the ENTIRE claim may be excluded — this "
            "estimate assumes that is not the case."
        )

    remaining = max(remaining, 0.0)
    total_deductions = sum(d["amount"] for d in deductions)
    # A ±10% band reflects the assumptions above that couldn't be turned into
    # exact deductions (room-rent proportion, sub-limit overlaps) — this is a
    # range to reason with, not a precise legal calculation.
    low = round(remaining * 0.9, 2)
    high = round(remaining, 2)

    return {
        "claim_amount": claim_amount,
        "estimated_payout": round(remaining, 2),
        "estimated_payout_range": [low, high],
        "total_deductions": round(total_deductions, 2),
        "deductions": deductions,
        "assumptions": assumptions,
        "disclaimer": (
            "This is a rough estimate based only on the policy clauses this tool has extracted from your "
            "document. It is NOT a guarantee of what the insurer will actually pay, does not account for "
            "your itemized hospital bill or proportionate room-rent deductions, and may miss clauses this "
            "tool didn't extract correctly. Use it to judge whether escalating a rejection is worth "
            "pursuing — not as a final number."
        ),
    }
