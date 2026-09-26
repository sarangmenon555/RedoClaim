"""
Policy Comparison Tool — sibling to the Payout Estimator: reuses clauses
your Policy Analyzer already extracted for each document and lines them up
side by side. No new LLM call needed since the extraction already happened
at upload time; this just structures what you already have.
"""
from app.services.irdai.payout_estimator import _parse_amount, _parse_percentage


_COMPARE_FIELDS = [
    ("sum_insured", "Sum Insured", "amount"),
    ("room_rent_cap", "Room Rent Cap", "room_rent"),
    ("co_payment", "Co-payment", "co_pay"),
    ("pre_existing_disease_waiting", "PED Waiting Period", "raw"),
]


def compare_policies(documents: list[dict]) -> dict:
    """
    documents: list of {"document_id", "file_name", "extracted_clauses"}
    Returns a row-per-attribute comparison plus a locally-generated list of
    notable differences (e.g. "Policy A has a higher room rent cap").
    """
    rows = []
    for field_key, label, kind in _COMPARE_FIELDS:
        row = {"attribute": label, "values": []}
        for doc in documents:
            clauses = doc.get("extracted_clauses") or {}
            raw = clauses.get(field_key)
            if kind == "amount":
                parsed = _parse_amount(raw)
                display = f"₹{parsed:,.0f}" if parsed is not None else (str(raw) if raw else "Not found")
            elif kind == "room_rent":
                rr = raw or {}
                display = f"{rr.get('limit', 'Not found')} ({rr.get('type', 'n/a')})" if rr else "Not found"
            elif kind == "co_pay":
                cp = raw or {}
                pct = _parse_percentage(cp.get("percentage")) if cp else 0
                display = f"{pct:.0f}%" + (f" — {cp.get('applies_to')}" if cp.get("applies_to") else "") if pct else "None"
            else:
                display = str(raw) if raw not in (None, "") else "Not found"
            row["values"].append({"document_id": doc.get("document_id"), "file_name": doc.get("file_name"), "display": display})
        rows.append(row)

    # Exclusions/waiting-periods count as a quick "which policy is stricter" signal
    exclusion_counts = []
    for doc in documents:
        clauses = doc.get("extracted_clauses") or {}
        exclusion_counts.append({
            "document_id": doc.get("document_id"),
            "file_name": doc.get("file_name"),
            "exclusion_count": len(clauses.get("exclusions") or []),
            "waiting_period_count": len(clauses.get("waiting_periods") or []),
            "sub_limit_count": len(clauses.get("sub_limits") or []),
        })

    return {
        "comparison_rows": rows,
        "exclusion_summary": exclusion_counts,
        "disclaimer": (
            "Built from each document's already-extracted policy clauses — verify against the actual "
            "policy schedules before deciding, since extraction can miss or misread a clause."
        ),
    }
