import logging
import re

from app.services.assistant.verified_facts import ALLOWED_DOMAINS

logger = logging.getLogger(__name__)

_DASHES = re.compile(r"[\u2010-\u2015\u2212]")

_WORD_NUMBERS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
    "nine": "9", "ten": "10", "twelve": "12", "fourteen": "14", "fifteen": "15", "thirty": "30",
    "sixty": "60", "ninety": "90",
}
_WORD_RE = re.compile(r"\b(" + "|".join(_WORD_NUMBERS) + r")\b(?=\s+(?:hours?|days?|weeks?|months?|years?|lakh|crore))", re.I)

_UNIT = r"(lakhs?|crores?|hours?|hrs?|days?|weeks?|months?|years?|%|percent|per cent)"
NUM_UNIT = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)[\s\-]*" + _UNIT + r"(?![a-z])", re.I)
RUPEE = re.compile(r"(?:\u20b9|rs\.?|inr)\s*(\d[\d,]*(?:\.\d+)?)\s*(lakhs?|crores?)?", re.I)
CITE = re.compile(r"\b(?:regulations?|para(?:graph)?|clause|section|rule|rules)\s+\d+[\w().\-]*", re.I)
DOMAIN = re.compile(r"\b(?:[a-z0-9\-]+\.)+(?:gov\.in|co\.in|org\.in|nic\.in|in|com|org|net)\b", re.I)

BAD_PHRASES = [
    r"e-?dcdrc",
    r"calculate_deadline",
    r"\bmy claims\b",
    r"insurer response",
    r"consumer protection \(fees\) rules",
    r"regulation 5\.2\.1",
    r"protection of policy-?holders.{0,3} interests\) regulations,? 2020",
]


def _norm(text: str) -> str:
    text = _DASHES.sub("-", text or "")
    return _WORD_RE.sub(lambda m: _WORD_NUMBERS[m.group(1).lower()], text)


def _unit(unit: str) -> str:
    u = unit.lower()
    if u.startswith(("hour", "hr")):
        return "hour"
    if u.startswith("day"):
        return "day"
    if u.startswith("week"):
        return "week"
    if u.startswith("month"):
        return "month"
    if u.startswith("year"):
        return "year"
    if u.startswith("lakh"):
        return "lakh"
    if u.startswith("crore"):
        return "crore"
    return "%"


def _num(value: str) -> str:
    cleaned = value.replace(",", "")
    try:
        number = float(cleaned)
    except ValueError:
        return cleaned
    return str(int(number)) if number == int(number) else str(number)


def _rupees(value: str, scale: str) -> float:
    base = float(_num(value))
    if scale:
        base *= 100_000 if scale.lower().startswith("lakh") else 10_000_000
    return base


def _allowed(allowed_text: str, user_text: str = "") -> dict:
    text = _norm(allowed_text)
    units = {(_num(m.group(1)), _unit(m.group(2))) for m in NUM_UNIT.finditer(text)}
    rupees = {_rupees(m.group(1), m.group(2) or "") for m in RUPEE.finditer(text)}
    user_numbers = {_num(n) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", _norm(user_text))}
    return {"units": units, "rupees": rupees, "numbers": user_numbers, "lower": text.lower()}


def line_problems(line: str, allowed: dict) -> list:
    problems = []
    text = _norm(line)
    lowered = text.lower()
    for pattern in BAD_PHRASES:
        if re.search(pattern, lowered):
            problems.append(f"known-wrong phrase: {pattern}")
    for match in NUM_UNIT.finditer(text):
        number, unit = _num(match.group(1)), _unit(match.group(2))
        if (number, unit) not in allowed["units"] and number not in allowed["numbers"]:
            problems.append(f"unsupported figure: {match.group(0)}")
    for match in RUPEE.finditer(text):
        value = _rupees(match.group(1), match.group(2) or "")
        if value >= 100 and value not in allowed["rupees"] and _num(match.group(1)) not in allowed["numbers"]:
            problems.append(f"unsupported amount: {match.group(0)}")
    for match in CITE.finditer(text):
        cite = re.sub(r"\s+", " ", match.group(0).lower())
        if cite not in allowed["lower"]:
            problems.append(f"unsupported citation: {match.group(0)}")
    for match in DOMAIN.finditer(text):
        domain = match.group(0).lower()
        if domain in allowed["lower"]:
            continue
        if not any(domain == d or domain.endswith("." + d) for d in ALLOWED_DOMAINS):
            problems.append(f"unverified address: {domain}")
    return problems


def check_answer(answer: str, allowed_text: str, fallback_text: str = "", user_text: str = "") -> dict:
    allowed = _allowed(allowed_text, user_text)
    kept, dropped, flags = [], 0, []
    for raw in (answer or "").split("\n"):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            kept.append(line)
            continue
        if stripped.startswith("|") or re.fullmatch(r"[-=_*\s]{3,}", stripped):
            dropped += 1
            flags.append("table or divider removed")
            continue
        problems = line_problems(stripped, allowed)
        if problems:
            dropped += 1
            flags.extend(problems)
        else:
            kept.append(line)
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()
    original_len = len((answer or "").strip())
    too_little = dropped > 0 and (len(cleaned) < 25 or len(cleaned) < 0.3 * original_len)
    if too_little:
        notice = "I could not verify enough to answer that fully, so here is what I can confirm."
        cleaned = (notice + "\n\n" + fallback_text).strip() if fallback_text else notice
        return {"answer": cleaned, "dropped": dropped, "flags": flags, "fallback": True}
    if dropped:
        cleaned += "\n\nI left out some details because I could not verify them. Please check irdai.gov.in or ask a licensed advocate about those points."
    if flags:
        logger.warning("Guard removed %d line(s): %s", dropped, "; ".join(dict.fromkeys(flags))[:600])
    return {"answer": cleaned, "dropped": dropped, "flags": flags, "fallback": False}
