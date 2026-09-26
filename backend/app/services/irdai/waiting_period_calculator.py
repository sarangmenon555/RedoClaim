"""
Waiting Period Calculator — pure date arithmetic over the `waiting_periods`
clauses your Policy Analyzer already extracts, plus the policy's inception
date. No LLM call: given "2 years" + an inception date, whether the period
has lapsed is just arithmetic, and arithmetic should be shown as arithmetic,
not an AI guess.

A common rejection reason (`waiting_period` in rejection_reason_category)
is a claim inside PED/specific-disease waiting periods — this lets a user
check that BEFORE filing a claim, or verify an insurer's rejection was
actually correct after the fact.
"""
import re
from datetime import date, datetime, timedelta
from typing import Optional


def _parse_date(value) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_duration_to_days(duration: str) -> Optional[int]:
    """'2 years' / '48 months' / '90 days' / '30-day initial period' → days."""
    if not duration:
        return None
    s = str(duration).strip().lower()

    year_match = re.search(r"(\d+(?:\.\d+)?)\s*year", s)
    if year_match:
        return round(float(year_match.group(1)) * 365)

    month_match = re.search(r"(\d+(?:\.\d+)?)\s*month", s)
    if month_match:
        return round(float(month_match.group(1)) * 30)

    day_match = re.search(r"(\d+(?:\.\d+)?)\s*day", s)
    if day_match:
        return round(float(day_match.group(1)))

    week_match = re.search(r"(\d+(?:\.\d+)?)\s*week", s)
    if week_match:
        return round(float(week_match.group(1)) * 7)

    return None


def calculate_waiting_periods(
    extracted_clauses: dict,
    inception_date_override: Optional[str] = None,
    as_of: Optional[date] = None,
) -> dict:
    """
    Returns, for every waiting_period clause found on the policy:
      condition, duration (as stated), duration_days (parsed), lapses_on,
      status (lapsed|active|unknown), days_remaining

    as_of defaults to today — pass a specific date to check "was this
    lapsed on the day I got treated" rather than "is it lapsed today".
    """
    extracted_clauses = extracted_clauses or {}
    as_of = as_of or date.today()

    inception_raw = inception_date_override or extracted_clauses.get("inception_date")
    inception = _parse_date(inception_raw)

    results = []
    for wp in (extracted_clauses.get("waiting_periods") or []):
        condition = wp.get("condition", "Unspecified condition")
        duration = wp.get("duration", "")
        risk_level = wp.get("risk_level", "medium")
        duration_days = _parse_duration_to_days(duration)

        entry = {
            "condition": condition,
            "duration_as_stated": duration,
            "risk_level": risk_level,
        }

        if inception is None:
            entry["status"] = "unknown"
            entry["note"] = "Policy inception date not available — cannot compute whether this has lapsed."
        elif duration_days is None:
            entry["status"] = "unknown"
            entry["note"] = f"Could not parse a duration from '{duration}' — check this clause manually."
        else:
            lapses_on = inception + timedelta(days=duration_days)
            entry["lapses_on"] = lapses_on.isoformat()
            if as_of >= lapses_on:
                entry["status"] = "lapsed"
                entry["note"] = f"This waiting period ended on {lapses_on.isoformat()} — should now be covered."
            else:
                entry["status"] = "active"
                days_remaining = (lapses_on - as_of).days
                entry["days_remaining"] = days_remaining
                entry["note"] = (
                    f"Still within the waiting period — {days_remaining} day(s) remaining "
                    f"(lapses on {lapses_on.isoformat()}). A claim for this condition filed now "
                    "is likely to be validly rejected on this ground."
                )

        results.append(entry)

    return {
        "inception_date": inception.isoformat() if inception else None,
        "checked_as_of": as_of.isoformat(),
        "waiting_periods": results,
        "disclaimer": (
            "Computed from the waiting-period clauses this tool extracted from your policy document "
            "and the inception date on file. Verify against your actual policy schedule/CIS before "
            "relying on this — extraction can miss or misread a clause."
        ),
    }
