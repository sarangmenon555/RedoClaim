"""
Claim escalation timeline model - RedoClaim.

One shared model used by the health, motor and life rules engines so the
three never drift apart. It keeps FOUR different kinds of timeline entry
strictly separate, because mixing them up produces dangerous output
(e.g. "GRO deadline within 5 days" when 5 days was merely the date the
grievance happened to be filed):

  event        something that happened (claim rejected, grievance filed)
  tat          a turnaround time the INSURER must meet (GRO resolution)
  conditional  a route whose availability depends on eligibility rules
  limitation   a window within which the POLICYHOLDER must act

What this model deliberately does NOT do:
  * invent a deadline for filing a grievance with the insurer's GRO -
    no specific filing deadline is established from the information held.
  * hard-code a short Insurance Ombudsman deadline (e.g. 45 days).
    Ombudsman eligibility and time limits depend on the Ombudsman rules;
    generally a complaint may be made within one year of the relevant
    rejection/decision or expiry of the applicable insurer-response period,
    subject to eligibility requirements.
  * compute a consumer-law limitation date. Limitation depends on the cause
    of action and circumstances; users are told to take legal guidance.
"""
from datetime import datetime, timedelta
from typing import Optional

# Bump when the meaning of the stored gro_deadline / irdai_deadline columns
# changes. Claims saved before this model (version missing) hold the OLD,
# incorrect "rejection + 15 days" / "rejection + 45 days" values; callers use
# `current_deadline()` so those stale values are never shown as deadlines.
TIMELINE_MODEL_VERSION = 2

# Insurer grievance-resolution turnaround. Bima Bharosa material: resolve
# within 15 days of receipt; some IRDAI health-insurance FAQ text lists 14
# days for the decision. We show ~15 days and tell the user to verify.
GRO_RESPONSE_TAT_DAYS = 15

# Conservative, INDICATIVE outer date for the Ombudsman window, counted from
# the claim rejection. The actual window runs from the relevant
# rejection/decision or expiry of the insurer-response period, so the real
# date can only be later than this - never earlier.
OMBUDSMAN_INDICATIVE_WINDOW_DAYS = 365

GRO_FILING_NOTE = (
    "No specific deadline for filing a grievance with the insurer has been "
    "established from the information provided."
)
OMBUDSMAN_CONDITIONAL_NOTE = (
    "Insurance Ombudsman: eligibility and time limits depend on the applicable "
    "Ombudsman rules. Generally, a complaint may be made within one year of the "
    "relevant rejection/decision or expiry of the applicable insurer-response "
    "period, subject to eligibility requirements (for example, the insurer's own "
    "grievance channel having been approached first). Check the exact conditions "
    "with the Council for Insurance Ombudsmen before relying on any date."
)
OMBUDSMAN_WINDOW_NOTE = (
    "Indicative, conservative date only (one year counted from the rejection). "
    "The actual window is counted from the relevant rejection/decision or the "
    "expiry of the insurer-response period, so verify it against the Ombudsman "
    "procedure."
)
CONSUMER_LAW_NOTE = (
    "Consumer-law limitation may apply. This depends on the cause of action and "
    "the legal context; obtain appropriate legal guidance rather than relying on "
    "an automated estimate."
)
TAT_BREACH_CAVEAT = (
    "A missed turnaround time does not by itself establish that the underlying "
    "claim or cashless decision is invalid."
)


def naive(dt: Optional[datetime]) -> Optional[datetime]:
    """Drop tzinfo so aware (DB/pydantic) and naive datetimes can be compared."""
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if getattr(dt, "tzinfo", None) else dt


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def build_timeline(
    rejection_date: Optional[datetime],
    grievance_date: Optional[datetime] = None,
    now: Optional[datetime] = None,
) -> dict:
    """
    Returns a dict that is stored/served as `deadlines`:

      gro_deadline        insurer's grievance-RESPONSE date (a TAT, not a
                          policyholder filing deadline). Only when a
                          grievance filing date is known.
      ombudsman_deadline  indicative conservative Ombudsman window end.
      timeline_items      ordered, typed entries (event|tat|conditional|limitation)
      timeline_model_version
    """
    now = naive(now) or datetime.now()
    rejection_date = naive(rejection_date)
    grievance_date = naive(grievance_date)

    out: dict = {"timeline_model_version": TIMELINE_MODEL_VERSION}
    items: list[dict] = []

    if rejection_date:
        items.append({
            "key": "claim_rejected", "kind": "event",
            "label": "Claim rejected / decision received",
            "date": _iso(rejection_date), "note": None,
        })

    if grievance_date:
        gap = (grievance_date - rejection_date).days if rejection_date else None
        items.append({
            "key": "gro_filed", "kind": "event",
            "label": "GRO grievance filed",
            "date": _iso(grievance_date),
            "note": (
                (f"Filed {gap} day(s) after the rejection. " if gap is not None and gap >= 0 else "")
                + GRO_FILING_NOTE
            ),
        })
        response_due = grievance_date + timedelta(days=GRO_RESPONSE_TAT_DAYS)
        out["gro_deadline"] = response_due
        out["days_until_gro_response_due"] = (response_due - now).days
        items.append({
            "key": "gro_response_tat", "kind": "tat",
            "label": "Insurer grievance-resolution TAT (approx. 15 days from receipt)",
            "date": _iso(response_due),
            "overdue": response_due < now,
            "note": (
                "This is the time the insurer has to respond, not a deadline for you. "
                "Subject to the applicable framework - some IRDAI material states 14 days "
                "for the decision; verify the period for your insurer and complaint channel."
            ),
        })
    else:
        items.append({
            "key": "gro_not_filed", "kind": "info",
            "label": "No GRO grievance recorded yet",
            "date": None,
            "note": GRO_FILING_NOTE,
        })

    items.append({
        "key": "ombudsman_eligibility", "kind": "conditional",
        "label": "Insurance Ombudsman - eligibility",
        "date": None, "note": OMBUDSMAN_CONDITIONAL_NOTE,
    })

    if rejection_date:
        window_end = rejection_date + timedelta(days=OMBUDSMAN_INDICATIVE_WINDOW_DAYS)
        out["ombudsman_deadline"] = window_end
        out["days_left_for_ombudsman_window"] = max(0, (window_end - now).days)
        items.append({
            "key": "ombudsman_window", "kind": "limitation",
            "label": "Ombudsman filing window (indicative, conservative)",
            "date": _iso(window_end), "note": OMBUDSMAN_WINDOW_NOTE,
        })

    items.append({
        "key": "consumer_law", "kind": "info",
        "label": "Consumer-law limitation",
        "date": None, "note": CONSUMER_LAW_NOTE,
    })

    out["timeline_items"] = items
    return out


def current_deadline(claim, field: str):
    """
    Return claim.<field> ('gro_deadline' | 'irdai_deadline') only if the claim
    was saved under the current timeline model. Older claims hold the previous
    incorrect values (rejection+15d / rejection+45d), which must not be shown
    as deadlines.
    """
    value = getattr(claim, field, None)
    if value is None:
        return None
    report = getattr(claim, "audit_report", None) or {}
    try:
        version = report["hierarchy_of_evidence"]["step1_sla"]["deadlines"].get("timeline_model_version")
    except (KeyError, TypeError, AttributeError):
        version = None
    return value if version == TIMELINE_MODEL_VERSION else None
