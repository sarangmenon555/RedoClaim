import re
from datetime import datetime
from typing import Any, Optional

FLOAT_KEYS = {
    "claim_amount", "settled_amount", "treatment_amount", "total_bill_amount",
    "room_rent_per_day", "years_covered", "od_premium_before_ncb",
    "ncb_applied_by_insurer", "sum_insured",
}
INT_KEYS = {"days_admitted", "patient_age", "claim_free_years"}
BOOL_KEYS = {"gro_filed", "accident_related", "had_claim_this_year"}
DATE_KEYS = {
    "claim_date", "rejection_date", "gro_filed_date", "policy_inception_date",
    "as_of_date", "accident_date", "documents_complete_date",
}
TEXT_KEYS = {
    "insurer_name", "policy_number", "insurance_type", "patient_name",
    "patient_relationship", "reason_for_porting", "term", "city_tier",
    "appeal_type", "fact_pattern", "state",
}
LIST_KEYS = {"family_ages"}

ALLOWED_KEYS = FLOAT_KEYS | INT_KEYS | BOOL_KEYS | DATE_KEYS | TEXT_KEYS | LIST_KEYS

_MULTIPLIERS = {"lakh": 100_000, "lakhs": 100_000, "lac": 100_000, "lacs": 100_000,
                "crore": 10_000_000, "crores": 10_000_000, "cr": 10_000_000}

_DATE_FORMATS = (
    "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y",
    "%d %b %Y", "%d %B %Y", "%B %d, %Y", "%b %d, %Y", "%d %b, %Y", "%d %B, %Y",
)

_CITY_TIERS = {
    "metro": "metro", "metropolitan": "metro", "tier1": "tier1", "tier 1": "tier1",
    "tier-1": "tier1", "tier2": "tier2", "tier 2": "tier2", "tier-2": "tier2",
    "tier3": "tier2", "tier 3": "tier2", "town": "tier2", "village": "tier2",
}

_APPEAL_TYPES = {"gro", "insurer_escalation", "ombudsman", "bima_bharosa", "consumer_court"}
_RELATIONSHIPS = {"self", "spouse", "child", "parent", "other"}
_INSURANCE_TYPES = {"health", "motor", "life"}


def to_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    match = re.search(r"(\d[\d,]*\.?\d*)\s*([A-Za-z]+)?", value)
    if not match:
        return None
    try:
        number = float(match.group(1).replace(",", ""))
    except ValueError:
        return None
    word = (match.group(2) or "").lower()
    return number * _MULTIPLIERS.get(word, 1)


def to_int(value: Any) -> Optional[int]:
    number = to_float(value)
    if number is None:
        return None
    return int(round(number))


def to_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "y", "1"}:
            return True
        if lowered in {"false", "no", "n", "0"}:
            return False
    return None


def to_date_str(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or text.lower() in {"null", "none", "unknown", "n/a"}:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "")).date().isoformat()
    except ValueError:
        return None


def to_text(value: Any, limit: int = 300) -> Optional[str]:
    if value is None or isinstance(value, (bool, dict, list)):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "unknown", "n/a", "not stated"}:
        return None
    return text[:limit]


def to_int_list(value: Any) -> Optional[list[int]]:
    if isinstance(value, str):
        value = re.findall(r"\d+", value)
    if not isinstance(value, list):
        return None
    ages = []
    for item in value:
        number = to_int(item)
        if number is not None and 0 <= number <= 110:
            ages.append(number)
    return ages[:12] or None


def clean_params(raw: Any) -> dict:
    if not isinstance(raw, dict):
        return {}
    cleaned: dict = {}
    for key, value in raw.items():
        if key not in ALLOWED_KEYS or value is None:
            continue
        if key in FLOAT_KEYS:
            parsed = to_float(value)
            if parsed is not None and parsed >= 0:
                cleaned[key] = parsed
        elif key in INT_KEYS:
            parsed = to_int(value)
            if parsed is not None and 0 <= parsed <= 100_000:
                cleaned[key] = parsed
        elif key in BOOL_KEYS:
            parsed = to_bool(value)
            if parsed is not None:
                cleaned[key] = parsed
        elif key in DATE_KEYS:
            parsed = to_date_str(value)
            if parsed:
                cleaned[key] = parsed
        elif key in LIST_KEYS:
            parsed = to_int_list(value)
            if parsed:
                cleaned[key] = parsed
        else:
            parsed = to_text(value, 1500 if key in {"fact_pattern", "reason_for_porting"} else 300)
            if not parsed:
                continue
            if key == "city_tier":
                parsed = _CITY_TIERS.get(parsed.lower())
            elif key == "appeal_type":
                parsed = parsed.lower().replace(" ", "_")
                parsed = parsed if parsed in _APPEAL_TYPES else None
            elif key == "patient_relationship":
                parsed = parsed.lower()
                parsed = parsed if parsed in _RELATIONSHIPS else None
            elif key == "insurance_type":
                parsed = parsed.lower()
                parsed = parsed if parsed in _INSURANCE_TYPES else None
            if parsed:
                cleaned[key] = parsed
    return cleaned


def inr(value: Any) -> str:
    number = to_float(value)
    if number is None:
        return str(value)
    whole = int(round(abs(number)))
    digits = str(whole)
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        digits = f"{head},{tail}"
    return f"{'-' if number < 0 else ''}\u20b9{digits}"


def as_lines(value: Any, limit: int = 6) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, dict):
        parts = [str(v) for v in value.values() if isinstance(v, (str, int, float)) and str(v).strip()]
        return [" - ".join(parts)] if parts else []
    if isinstance(value, list):
        lines: list[str] = []
        for item in value:
            lines.extend(as_lines(item, limit))
            if len(lines) >= limit:
                break
        return lines[:limit]
    return [str(value)]


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
