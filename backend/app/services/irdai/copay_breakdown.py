"""
Co-pay / Deductible Breakdown Tool — a pre-claim-planning sibling to the
Payout Estimator. The Payout Estimator works from a claim amount alone and
can only FLAG a room-rent cap as an assumption, because it doesn't have
your actual hospital bill breakup. This tool takes your actual bill line
items + the room rent you actually paid, so it can compute the
proportionate deduction precisely — the exact calculation insurers use.

Still pure arithmetic, no LLM call.
"""
from app.services.irdai.payout_estimator import _parse_amount, _parse_percentage


def calculate_copay_breakdown(
    extracted_clauses: dict,
    total_bill_amount: float,
    actual_room_rent_per_day: float,
    days_admitted: int,
    bill_items: list[dict] | None = None,
    patient_age: int | None = None,
) -> dict:
    """
    bill_items (optional): [{"item": "Surgeon fees", "amount": 50000}, ...]
    Without itemized bill_items, the proportionate deduction is applied to
    the whole bill (the standard IRDAI-compliant method); with bill_items,
    each line is broken out individually so the user can see exactly where
    the cut lands.
    """
    extracted_clauses = extracted_clauses or {}
    deductions = []
    notes = []
    remaining = total_bill_amount

    # ── Proportionate room-rent deduction — the actual formula insurers use ──
    room_rent_cap = extracted_clauses.get("room_rent_cap") or {}
    cap_type = (room_rent_cap.get("type") or "none").lower()
    proportion = 1.0

    if cap_type == "per_day":
        eligible_rent = _parse_amount(room_rent_cap.get("limit"))
        if eligible_rent and actual_room_rent_per_day > eligible_rent:
            proportion = eligible_rent / actual_room_rent_per_day
            notes.append(
                f"Your actual room rent (₹{actual_room_rent_per_day:,.0f}/day) exceeds the policy's eligible "
                f"room rent (₹{eligible_rent:,.0f}/day). Under the standard proportionate-deduction formula, "
                f"you're eligible for {proportion*100:.1f}% of associated medical expenses, not just the room charge."
            )
    elif cap_type == "percentage":
        sum_insured = _parse_amount(extracted_clauses.get("sum_insured"))
        pct = _parse_percentage(room_rent_cap.get("limit"))
        if sum_insured and pct:
            eligible_rent = sum_insured * (pct / 100) / max(days_admitted, 1)
            if actual_room_rent_per_day > eligible_rent:
                proportion = eligible_rent / actual_room_rent_per_day
                notes.append(
                    f"Policy caps room rent at {pct:.1f}% of sum insured per day (₹{eligible_rent:,.0f}/day). "
                    f"Your actual rent (₹{actual_room_rent_per_day:,.0f}/day) exceeds this, so the proportionate "
                    f"formula reduces your eligible amount to {proportion*100:.1f}%."
                )

    if proportion < 1.0:
        if bill_items:
            breakdown = []
            total_eligible = 0.0
            for item in bill_items:
                amt = float(item.get("amount", 0) or 0)
                eligible = round(amt * proportion, 2)
                cut = round(amt - eligible, 2)
                breakdown.append({"item": item.get("item", "Item"), "billed": amt, "eligible": eligible, "cut": cut})
                total_eligible += eligible
            deductions.append({
                "reason": f"Proportionate deduction ({proportion*100:.1f}% eligible) applied per line item",
                "amount": round(total_bill_amount - total_eligible, 2),
                "line_items": breakdown,
            })
            remaining = total_eligible
        else:
            eligible_total = round(total_bill_amount * proportion, 2)
            deductions.append({
                "reason": f"Proportionate deduction ({proportion*100:.1f}% eligible, applied to full bill)",
                "amount": round(total_bill_amount - eligible_total, 2),
            })
            remaining = eligible_total

    # ── Co-payment ────────────────────────────────────────────────
    co_pay = extracted_clauses.get("co_payment") or {}
    co_pay_pct = _parse_percentage(co_pay.get("percentage"))
    applies_to = co_pay.get("applies_to", "") or ""
    if co_pay_pct > 0 and patient_age is not None and applies_to:
        import re
        age_match = re.search(r"(\d+)", applies_to)
        if age_match and patient_age < int(age_match.group(1)):
            notes.append(f"Co-payment ({co_pay_pct:.0f}%) applies only for age {age_match.group(1)}+ — not applied since patient is {patient_age}.")
            co_pay_pct = 0.0
    if co_pay_pct > 0:
        cut = round(remaining * (co_pay_pct / 100), 2)
        deductions.append({"reason": f"Co-payment ({co_pay_pct:.0f}%)" + (f" — {applies_to}" if applies_to else ""), "amount": cut})
        remaining -= cut

    # ── Sum insured cap ──────────────────────────────────────────
    sum_insured = _parse_amount(extracted_clauses.get("sum_insured"))
    if sum_insured is not None and remaining > sum_insured:
        cut = round(remaining - sum_insured, 2)
        deductions.append({"reason": "Remaining amount exceeds policy sum insured", "amount": cut})
        remaining = sum_insured

    remaining = max(round(remaining, 2), 0.0)
    total_deducted = round(total_bill_amount - remaining, 2)

    return {
        "total_bill_amount": total_bill_amount,
        "estimated_insurer_payout": remaining,
        "your_out_of_pocket": total_deducted,
        "deductions": deductions,
        "notes": notes,
        "disclaimer": (
            "Computed from your policy's extracted clauses and the bill figures you entered. The proportionate "
            "room-rent formula shown here is the standard IRDAI-compliant method most insurers use, but exact "
            "insurer practice can vary — treat this as a close estimate for planning, not a guaranteed final amount."
        ),
    }
