"""
Settlement second-opinion guard - RedoClaim.

A deduction can be ARITHMETICALLY consistent without being ESTABLISHED by the
policy. The classic case is room-rent proportionate deduction: 37.5% x the whole
bill is correct maths, but it is only a justified deduction if the policy says the
percentage applies to those charges. If the supplied wording does not say which
charges are affected, the tool must report "arithmetic consistent, scope
unverified" - never "justified".
"""
import re
from typing import Optional

_PROPORTIONATE_RE = re.compile(
    r"proportionate|pro[- ]?rata|room[- ]?rent|room (category|rent) (cap|limit|eligib)|icu (rent|charges?) (cap|limit)",
    re.IGNORECASE,
)
_VAGUE_SCOPE_RE = re.compile(
    r"as (specified|defined|stated|provided|mentioned|per|laid down)( in| by)?( the)?( policy| schedule| terms)?|"
    r"as per (the )?(policy|schedule|terms)|subject to policy",
    re.IGNORECASE,
)


def inr(n: float) -> str:
    """Indian digit grouping: 125000 -> Rs. 1,25,000."""
    n = int(round(n))
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return f"Rs. {'-' if n < 0 else ''}{s}"


def proportionate_math(actual: float, eligible: float, base: float) -> dict:
    ratio = eligible / actual if actual else 1.0
    deduction = base * (1 - ratio) if actual > eligible else 0.0
    return {
        "actual_room_rent": actual,
        "eligible_room_rent": eligible,
        "excess_room_rent": max(0.0, actual - eligible),
        "deduction_percent": round((1 - ratio) * 100, 2) if actual > eligible else 0.0,
        "base_amount": base,
        "computed_deduction": round(deduction, 2),
    }


def _scope_established(review: dict, policy_clauses: dict) -> bool:
    """
    True only if the policy text itself says WHICH charges the proportionate
    deduction applies to: a non-empty list of affected charges, backed by an
    excerpt that is verified present in the policy, and not just "as specified
    in the policy".
    """
    charges = list(review.get("charges_in_scope_per_policy") or [])
    pd = (policy_clauses or {}).get("proportionate_deduction") or {}
    if not charges and pd.get("scope_specified") and pd.get("charges_affected"):
        charges = list(pd["charges_affected"])
    if not charges:
        return False
    evidence = review.get("policy_evidence") or {}
    if evidence.get("excerpt") and evidence.get("excerpt_verified") is False:
        return False
    if not evidence.get("excerpt") and not pd.get("excerpt"):
        return False
    text = " ".join(str(c) for c in charges) + " " + str(evidence.get("excerpt") or pd.get("excerpt") or "")
    # An enumerated list of charges is a scope; a bare "as specified in the policy" is not.
    if _VAGUE_SCOPE_RE.search(text) and len(charges) <= 1 and not re.search(r"\b(all|entire|whole|total)\b", text, re.I):
        return False
    return True


def review_settlement(result: dict, policy_clauses: dict, claim_amount: float, settled_amount: float) -> dict:
    """Mutates and returns result with a reliable `settlement_assessment`."""
    deductions = result.get("deductions_reviewed") or []
    review = result.get("proportionate_deduction_review") or {}
    prop_entries = [
        d for d in deductions
        if isinstance(d, dict) and _PROPORTIONATE_RE.search(str(d.get("stated_reason", "")))
    ]
    present = bool(review.get("present")) or bool(prop_entries)
    verification: list[str] = []

    if present:
        actual = review.get("actual_room_rent")
        eligible = review.get("eligible_room_rent")
        base = review.get("amount_base_applied")
        insurer_ded = review.get("insurer_deduction")
        if insurer_ded is None and prop_entries:
            insurer_ded = prop_entries[0].get("amount_deducted")
        scope_ok = _scope_established(review, policy_clauses)

        calc = None
        arithmetic_ok = None
        if all(isinstance(x, (int, float)) and x for x in (actual, eligible, base)):
            calc = proportionate_math(float(actual), float(eligible), float(base))
            if isinstance(insurer_ded, (int, float)):
                arithmetic_ok = abs(calc["computed_deduction"] - float(insurer_ded)) <= 1.0

        check = {
            "arithmetic": calc,
            "insurer_deduction": insurer_ded,
            "arithmetic_consistent": arithmetic_ok,
            "scope_established_in_policy": scope_ok,
            "charges_in_scope_per_policy": review.get("charges_in_scope_per_policy") or [],
            "policy_evidence": review.get("policy_evidence"),
        }

        if not scope_ok:
            pct = calc["deduction_percent"] if calc else None
            base_s = inr(base) if isinstance(base, (int, float)) else "the billed amount"
            msg = (
                f"The {inr(insurer_ded) if isinstance(insurer_ded, (int, float)) else 'proportionate'} deduction is "
                + (f"mathematically consistent with applying {pct:g}% to {base_s}, but " if arithmetic_ok and pct is not None
                   else "stated by the insurer, but ")
                + "the supplied policy extract does not establish that the proportionate deduction applies to the "
                  "entire bill or to which specific charges. "
                "The exact proportionate-deduction clause and the list of affected charges must be verified "
                f"before concluding that the {inr(settled_amount)} settlement is correct."
            )
            check["message"] = msg
            verification.append(msg)
            verification.append(
                "Ask the insurer in writing to quote the clause and list the charges it treated as linked to room-rent eligibility."
            )
            for d in prop_entries:
                d["justified_by_policy"] = None
                d["basis_status"] = "arithmetic_consistent_scope_unverified" if arithmetic_ok else "unverified"
                d["explanation"] = (str(d.get("explanation") or "") + " [Scope of this deduction is not established by the supplied policy text.]").strip()
            result["settlement_assessment"] = (
                "arithmetic_consistent_scope_unverified" if arithmetic_ok is not False else "questionable"
            )
            result["is_settlement_likely_correct"] = None
            result["confidence"] = "low"
            result["recommended_action"] = "verify_policy_wording"
        else:
            check["message"] = "The policy text identifies the charges the proportionate deduction applies to."
        result["proportionate_deduction_check"] = check

    if "settlement_assessment" not in result:
        if result.get("is_settlement_likely_correct") is True:
            result["settlement_assessment"] = "consistent_with_policy"
        elif result.get("is_settlement_likely_correct") is False:
            result["settlement_assessment"] = "questionable"
        else:
            result["settlement_assessment"] = "insufficient_evidence"

    if verification:
        result["verification_required"] = verification
        # The summary sentence must not contradict the guard.
        result["reasoning"] = (
            verification[0] + " " + str(result.get("reasoning") or "")
        ).strip()
    return result
