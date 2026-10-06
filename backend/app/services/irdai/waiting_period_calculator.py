"""
Waiting Period Calculator - date arithmetic PLUS an explicit exception stage.

Stage order (never skip a stage):

    1. Parse each waiting-period clause and the policy inception date.
    2. Work out whether the period is still running (calendar-month aware).
    3. EXCEPTION STAGE: if it is still running, check whether the policy carries
       an exception (most importantly an accident exception) and whether the
       evidence supplied shows the treatment is within that exception.
    4. Only then decide the status.

Possible statuses per clause:
    lapsed                          period already over
    applies                         running, and no exception identified
    exception_applies               running, but an exception appears to apply
    may_apply_insufficient_evidence running; policy has an exception but the
                                    evidence does not show whether it applies
    unclear                         clause/inception could not be read

The calculator never says a claim "is likely validly rejected": a running
waiting period is reported as one that "may affect" the claim, and every
output tells the user to verify against the full policy wording.
"""
import re
from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Optional

# --- statuses ----------------------------------------------------------
LAPSED = "lapsed"
APPLIES = "applies"
EXCEPTION_APPLIES = "exception_applies"
MAY_APPLY_INSUFFICIENT = "may_apply_insufficient_evidence"
UNCLEAR = "unclear"

_ACCIDENT_EXCEPTION_RE = re.compile(
    r"\b(accident|accidental|accidents)\b", re.IGNORECASE
)
# Words in a policy line that signal "this is a carve-out from the waiting period".
_EXCEPTION_CUE_RE = re.compile(
    r"\b(except|exception|excluding|excluded from waiting|not apply|does not apply|"
    r"waived|waiver|shall not apply|not applicable|exempt|covered from (day|inception))\b",
    re.IGNORECASE,
)

# Evidence that a treatment followed an accident (checked in claim documents).
_ACCIDENT_EVIDENCE_RE = re.compile(
    r"\b(accident|accidental|road traffic|rta\b|collision|medico[- ]?legal|mlc\b|"
    r"fir\b|skid(ded)?|fell from|fall from|slipped and fell|traumatic injury|"
    r"fracture (due|following|after) )",
    re.IGNORECASE,
)
_ACCIDENT_NEGATION_RE = re.compile(
    r"\b(no (history of )?accident|not (an |due to |caused by )?accident|non[- ]?accident|"
    r"without any accident|degenerative)\b",
    re.IGNORECASE,
)


def _parse_date(value) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s).date()
    except ValueError:
        return None


def _add_months(d: date, months: int) -> date:
    """Calendar-aware month addition (24 months from 15 Mar 2025 = 15 Mar 2027)."""
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def _lapse_date(inception: date, duration: str) -> Optional[date]:
    """'2 years' / '24 months' / '90 days' / '30-day initial period' -> date it lapses."""
    if not duration:
        return None
    s = str(duration).strip().lower()

    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:year|yr)", s)
    if m:
        return _add_months(inception, round(float(m.group(1)) * 12))
    m = re.search(r"(\d+(?:\.\d+)?)\s*month", s)
    if m:
        return _add_months(inception, round(float(m.group(1))))
    m = re.search(r"(\d+(?:\.\d+)?)\s*week", s)
    if m:
        return inception + timedelta(days=round(float(m.group(1)) * 7))
    m = re.search(r"(\d+(?:\.\d+)?)\s*day", s)
    if m:
        return inception + timedelta(days=round(float(m.group(1))))
    return None


def _clause_text(*parts) -> str:
    out = []
    for p in parts:
        if isinstance(p, str):
            out.append(p)
        elif isinstance(p, (list, tuple)):
            out.extend(str(x) for x in p if x)
        elif isinstance(p, dict):
            out.extend(str(x) for x in p.values() if x)
    return " ".join(out)


def find_policy_exceptions(extracted_clauses: dict, wp: dict) -> list[str]:
    """
    Exceptions that apply to this waiting-period clause. Looks at:
      - the clause's own `exceptions` / `exception` / `note`
      - the policy-wide `waiting_period_exceptions` list
      - claim_restrictions lines that pair "waiting" with an accident carve-out
    Returns short human-readable descriptions (empty list = none identified).
    """
    found: list[str] = []

    own_list = wp.get("exceptions") or ([wp["exception"]] if wp.get("exception") else [])
    for e in own_list:
        if isinstance(e, dict):
            e = e.get("exception") or e.get("description") or e.get("clause") or ""
        if e and str(e).strip():
            found.append(str(e).strip())

    note = wp.get("note")
    if isinstance(note, str) and _EXCEPTION_CUE_RE.search(note) and note.strip() not in found:
        found.append(note.strip())

    for e in (extracted_clauses.get("waiting_period_exceptions") or []):
        if isinstance(e, dict):
            applies_to = str(e.get("applies_to") or "").lower()
            cond = str(wp.get("condition") or "").lower()
            if applies_to and applies_to not in ("all", "any", "all waiting periods") and cond and \
               applies_to not in cond and cond not in applies_to:
                continue
            e = e.get("exception") or e.get("description") or e.get("clause") or ""
        if e and str(e).strip() and str(e).strip() not in found:
            found.append(str(e).strip())

    for line in (extracted_clauses.get("claim_restrictions") or []):
        if isinstance(line, str) and "waiting" in line.lower() and _ACCIDENT_EXCEPTION_RE.search(line) \
           and _EXCEPTION_CUE_RE.search(line) and line.strip() not in found:
            found.append(line.strip())

    return found


def _is_accident_exception(text: str) -> bool:
    return bool(_ACCIDENT_EXCEPTION_RE.search(text or ""))


def assess_accident_evidence(claim_context: Optional[dict]) -> dict:
    """
    Decide, from what the user told us and/or the claim documents they chose,
    whether the treatment appears accident-related.
      related: True | False | None (unknown)
      source:  'user' | 'documents' | None
    """
    ctx = claim_context or {}
    explicit = ctx.get("accident_related")
    accident_date = _parse_date(ctx.get("accident_date"))

    if explicit is True:
        return {"related": True, "source": "user", "accident_date": accident_date}
    if explicit is False:
        return {"related": False, "source": "user", "accident_date": accident_date}

    texts = [t for t in (ctx.get("evidence_texts") or []) if isinstance(t, str) and t.strip()]
    joined = "\n".join(texts)
    if joined and _ACCIDENT_EVIDENCE_RE.search(joined) and not _ACCIDENT_NEGATION_RE.search(joined):
        return {"related": True, "source": "documents", "accident_date": accident_date}
    return {"related": None, "source": None, "accident_date": accident_date}


def calculate_waiting_periods(
    extracted_clauses: dict,
    inception_date_override: Optional[str] = None,
    as_of: Optional[date] = None,
    claim_context: Optional[dict] = None,
) -> dict:
    """
    claim_context (all optional):
      accident_related   True | False | None
      accident_date      date-like; checked against the policy inception
      evidence_texts     OCR text of claim documents to scan for accident evidence
    """
    extracted_clauses = extracted_clauses or {}
    as_of = as_of or date.today()
    inception = _parse_date(inception_date_override or extracted_clauses.get("inception_date"))
    evidence = assess_accident_evidence(claim_context)

    results = []
    all_exceptions: list[str] = []

    for wp in (extracted_clauses.get("waiting_periods") or []):
        condition = wp.get("condition", "Unspecified condition")
        duration = wp.get("duration", "")
        entry = {
            "condition": condition,
            "duration_as_stated": duration,
            "risk_level": wp.get("risk_level", "medium"),
            "exceptions_found": [],
        }

        # ---- Stage 1/2: parse + arithmetic -------------------------------
        if inception is None:
            entry["status"] = UNCLEAR
            entry["note"] = (
                "Waiting period clause identified, but the policy inception date is not "
                "available, so whether it has lapsed cannot be computed."
            )
            results.append(entry)
            continue

        lapses_on = _lapse_date(inception, duration)
        if lapses_on is None:
            entry["status"] = UNCLEAR
            entry["note"] = (
                f"The waiting-period clause ('{duration or 'no duration stated'}') could not be "
                "read as a duration. Check the clause in the policy wording directly."
            )
            results.append(entry)
            continue

        entry["lapses_on"] = lapses_on.isoformat()
        entry["duration_days"] = (lapses_on - inception).days

        if as_of >= lapses_on:
            entry["status"] = LAPSED
            entry["note"] = f"This waiting period ended on {lapses_on.isoformat()} and should no longer restrict the claim."
            results.append(entry)
            continue

        days_remaining = (lapses_on - as_of).days
        entry["days_remaining"] = days_remaining
        running = f"{days_remaining} day(s) remaining (lapses on {lapses_on.isoformat()})"

        # ---- Stage 3: EXCEPTION STAGE ------------------------------------
        exceptions = find_policy_exceptions(extracted_clauses, wp)
        entry["exceptions_found"] = exceptions
        for e in exceptions:
            if e not in all_exceptions:
                all_exceptions.append(e)
        accident_exception = any(_is_accident_exception(e) for e in exceptions)

        if accident_exception:
            accident_date = evidence["accident_date"]
            predates_policy = bool(accident_date and accident_date < inception)

            if evidence["related"] is True and predates_policy:
                entry["status"] = APPLIES
                entry["note"] = (
                    f"Waiting period identified: {duration}, {running}. The policy has an accident "
                    f"exception, but the accident date ({accident_date.isoformat()}) is before the policy "
                    "commenced, so the exception may not help here. Verify the dates and the exact "
                    "exception wording in the complete policy."
                )
            elif evidence["related"] is True:
                basis = (
                    "the information you supplied indicates"
                    if evidence["source"] == "user"
                    else "the supplied claim documents indicate"
                )
                after = (
                    f" (accident date {accident_date.isoformat()}, after policy commencement)"
                    if accident_date and accident_date >= inception else ""
                )
                entry["status"] = EXCEPTION_APPLIES
                entry["note"] = (
                    f"Waiting period identified: {duration}. However, the policy contains an accident "
                    f"exception, and {basis} the treatment followed an accident{after}. "
                    f"Therefore, the {duration} waiting period may not apply to this claim. Verify the "
                    "accident-related exception against the complete policy wording and the medical records."
                )
            elif evidence["related"] is False:
                entry["status"] = APPLIES
                entry["note"] = (
                    f"Waiting period identified: {duration}, {running}. The policy has an accident "
                    "exception, but you indicated the treatment is not accident-related, so the waiting "
                    "period may affect this claim. Check the complete policy wording and the medical "
                    "records before drawing any conclusion."
                )
            else:
                entry["status"] = MAY_APPLY_INSUFFICIENT
                entry["note"] = (
                    f"Waiting period identified: {duration}, {running}. The policy contains an accident "
                    "exception, but no evidence has been supplied showing whether this treatment is "
                    "accident-related, so it cannot be determined whether the waiting period applies. "
                    "If the treatment followed an accident after the policy commenced, the waiting period "
                    "may not apply. Verify against the complete policy wording and the medical records."
                )
        elif exceptions:
            entry["status"] = MAY_APPLY_INSUFFICIENT
            entry["note"] = (
                f"Waiting period identified: {duration}, {running}. The policy mentions an exception "
                f"to this period ({'; '.join(exceptions)[:240]}). Whether it applies to this claim cannot "
                "be determined from the information supplied. Verify against the complete policy wording."
            )
        else:
            entry["status"] = APPLIES
            entry["note"] = (
                f"Waiting period identified: {duration}, {running}. No exception to this waiting "
                "period was found in the extracted clauses, so it may affect a claim for this "
                "condition during this period. Extraction can miss clauses - check the complete "
                "policy wording for exceptions before drawing any conclusion."
            )

        results.append(entry)

    return {
        "inception_date": inception.isoformat() if inception else None,
        "checked_as_of": as_of.isoformat(),
        "waiting_periods": results,
        "exceptions_identified": all_exceptions,
        "accident_evidence": {
            "treatment_accident_related": evidence["related"],
            "source": evidence["source"],
        },
        "exception_stage_run": True,
        "disclaimer": (
            "Computed from the waiting-period clauses and exceptions extracted from your policy and "
            "the inception date on file. This is not a decision on any claim. Extraction can miss or "
            "misread a clause or exception - verify against the complete policy wording, the CIS and "
            "the medical records before relying on it."
        ),
    }
