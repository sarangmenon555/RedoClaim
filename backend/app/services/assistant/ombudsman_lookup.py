import re

from app.services.assistant.ombudsman_data import CITIES, OFFICES, STATES

ALIASES = {
    "kerala": "keralam",
    "orissa": "odisha",
    "pondicherry": "puducherry",
    "bangalore": "bengaluru",
    "cochin": "kochi",
    "bombay": "mumbai",
    "madras": "chennai",
    "calcutta": "kolkata",
    "uttaranchal": "uttarakhand",
    "new delhi": "delhi",
    "trivandrum": "thiruvananthapuram",
    "calicut": "kozhikode",
    "vizag": "visakhapatnam",
    "baroda": "vadodara",
    "poona": "pune",
    "gauhati": "guwahati",
    "banaras": "varanasi",
    "benares": "varanasi",
    "allahabad": "prayagraj",
    "faizabad": "ayodhya",
    "chhatrapati sambhaji nagar": "chhatrapati sambhajinagar",
    "sri vijayapuram": "sri vijaya puram",
}

DISPLAY = {
    "bangalore": "Bengaluru",
    "mysore": "Mysuru",
    "gurgaon": "Gurugram",
    "allahabad": "Prayagraj",
    "faizabad": "Ayodhya",
    "aurangabad": "Chhatrapati Sambhajinagar",
    "port blair": "Sri Vijaya Puram",
    "sambhajinagar": "Chhatrapati Sambhajinagar",
    "ahmednagar": "Ahilyanagar",
}

MERGED_UT = "Dadra and Nagar Haveli and Daman and Diu"
MERGED_UT_WORDS = re.compile(r"\b(dadra|nagar haveli|daman|diu|silvassa)\b")

AMBIGUOUS_DISTRICTS = {"hamirpur", "pratapgarh", "balrampur", "basti"}
UP_WORDS = re.compile(r"\b(uttar pradesh|up|u p)\b")


def _norm(text: str) -> str:
    lowered = (text or "").lower().replace("&", " and ")
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    lowered = f" {lowered.strip()} "
    for alias, real in ALIASES.items():
        lowered = lowered.replace(f" {alias} ", f" {real} ")
    return lowered


def _has(norm: str, phrase: str) -> bool:
    return f" {_norm(phrase).strip()} " in norm


def find_offices(query: str) -> dict:
    norm = _norm(query)
    norm_core = norm.replace(" navi mumbai ", " ")
    centers: list = []
    up_centers: list = []
    district_centers: list = []
    matched: list = []
    notes: list = []

    def add_center(name: str):
        if name not in centers:
            centers.append(name)

    def add_match(label: str):
        if label not in matched:
            matched.append(label)

    for state in STATES:
        if _has(norm, state["name"]):
            add_match(state["name"])
            for center in state["centers"]:
                if state["name"] == "Uttar Pradesh":
                    up_centers.append(center)
                else:
                    add_center(center)
            if state.get("note") and state["note"] not in notes:
                notes.append(state["note"])

    for office in OFFICES:
        for covered in office["statesCovered"]:
            if _has(norm_core, covered):
                add_match(covered)
                add_center(office["center"])
        if _has(norm_core, office["center"]):
            add_match(office["center"])
            add_center(office["center"])
        for district in office.get("districts") or []:
            key = _norm(district).strip()
            if key in AMBIGUOUS_DISTRICTS and not UP_WORDS.search(norm):
                continue
            if _has(norm, district):
                add_match(f"{district}, Uttar Pradesh")
                if office["center"] not in district_centers:
                    district_centers.append(office["center"])

    if MERGED_UT_WORDS.search(norm):
        add_match(MERGED_UT)
        add_center("Ahmedabad")

    if isinstance(CITIES, dict):
        for city, center in CITIES.items():
            if _has(norm if city == "navi mumbai" else norm_core, city):
                add_match(DISPLAY.get(city, city.title()))
                add_center(center)

    for center in (district_centers or up_centers):
        add_center(center)
    if district_centers:
        matched = [m for m in matched if m != "Uttar Pradesh"]
        notes = [n for n in notes if not n.startswith("Uttar Pradesh is divided")]

    by_center = {o["center"]: o for o in OFFICES}
    return {
        "offices": [by_center[c] for c in centers if c in by_center],
        "matched": matched,
        "notes": notes,
    }
