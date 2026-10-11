import re

from app.services.assistant.ombudsman_data import CITIES, OFFICES, STATES

ALIASES = {
    "kerala": "keralam",
    "orissa": "odisha",
    "pondicherry": "puducherry",
    "bangalore": "bengaluru",
    "cochin": "ernakulam",
    "kochi": "ernakulam",
    "bombay": "mumbai",
    "madras": "chennai",
    "calcutta": "kolkata",
    "uttaranchal": "uttarakhand",
    "new delhi": "delhi",
}


def _norm(text: str) -> str:
    lowered = (text or "").lower().replace("&", " and ")
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    lowered = f" {lowered.strip()} "
    for alias, real in ALIASES.items():
        lowered = lowered.replace(f" {alias} ", f" {real} ")
    return lowered


def _has(norm: str, phrase: str) -> bool:
    return f" {_norm(phrase).strip()} " in norm


MERGED_UT = "Dadra and Nagar Haveli and Daman and Diu"
MERGED_UT_WORDS = re.compile(r"\b(dadra|nagar haveli|daman|diu|silvassa)\b")


def find_offices(query: str) -> dict:
    norm = _norm(query)
    centers: list = []
    matched: list = []
    notes: list = []

    def add_center(name: str):
        if name not in centers:
            centers.append(name)

    for state in STATES:
        if _has(norm, state["name"]):
            matched.append(state["name"])
            for center in state["centers"]:
                add_center(center)
            if state.get("note"):
                notes.append(state["note"])

    for office in OFFICES:
        for covered in office["statesCovered"]:
            if _has(norm, covered):
                if covered not in matched:
                    matched.append(covered)
                add_center(office["center"])
        if _has(norm, office["center"]):
            if office["center"] not in matched:
                matched.append(office["center"])
            add_center(office["center"])

    if MERGED_UT_WORDS.search(norm):
        if MERGED_UT not in matched:
            matched.append(MERGED_UT)
        add_center("Ahmedabad")

    if isinstance(CITIES, dict):
        for city, center in CITIES.items():
            if _has(norm, city):
                if city.title() not in matched:
                    matched.append(city.title())
                add_center(center)

    by_center = {o["center"]: o for o in OFFICES}
    return {
        "offices": [by_center[c] for c in centers if c in by_center],
        "matched": matched,
        "notes": notes,
    }
