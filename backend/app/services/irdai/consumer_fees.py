from typing import Optional

LAKH = 100_000
CRORE = 10_000_000

FEE_SLABS = [
    (5 * LAKH, 0),
    (10 * LAKH, 200),
    (20 * LAKH, 400),
    (50 * LAKH, 1000),
    (1 * CRORE, 2000),
    (2 * CRORE, 2500),
    (4 * CRORE, 3000),
    (6 * CRORE, 4000),
    (8 * CRORE, 5000),
    (10 * CRORE, 6000),
]
TOP_FEE = 7500

DISTRICT_LIMIT = 50 * LAKH
STATE_LIMIT = 2 * CRORE

FORUM_NAMES = {
    "district": "District Consumer Disputes Redressal Commission",
    "state": "State Consumer Disputes Redressal Commission",
    "national": "National Consumer Disputes Redressal Commission",
}

FORUM_BASIS_NOTE = (
    "The forum and the court fee depend on the value of the goods or services paid as consideration, not on the "
    "claim amount. For an insurance policy this is generally the premium paid, so most insurance complaints are "
    "filed before the District Commission. Confirm the position with the commission or an advocate if your premium is large."
)


def _amount(value: int) -> str:
    if value % CRORE == 0:
        return f"Rs. {value // CRORE} crore"
    return f"Rs. {value // LAKH} lakh"


def fee_table() -> list:
    rows = []
    previous = 0
    for upper, fee in FEE_SLABS:
        label = f"Up to {_amount(upper)}" if previous == 0 else f"Above {_amount(previous)} up to {_amount(upper)}"
        rows.append({"range": label, "fee": fee})
        previous = upper
    rows.append({"range": f"Above {_amount(previous)}", "fee": TOP_FEE})
    return rows


def fee_for(consideration: float) -> int:
    for upper, fee in FEE_SLABS:
        if consideration <= upper:
            return fee
    return TOP_FEE


def forum_for(consideration: float) -> str:
    if consideration <= DISTRICT_LIMIT:
        return "district"
    if consideration <= STATE_LIMIT:
        return "state"
    return "national"


def describe(consideration: Optional[float]) -> dict:
    if consideration is None or consideration < 0:
        return {}
    key = forum_for(consideration)
    return {"forum_key": key, "forum": FORUM_NAMES[key], "fee": fee_for(consideration)}


def forums() -> list:
    return [
        {"forum": FORUM_NAMES["district"], "range": "Up to Rs. 50 lakh"},
        {"forum": FORUM_NAMES["state"], "range": "Above Rs. 50 lakh up to Rs. 2 crore"},
        {"forum": FORUM_NAMES["national"], "range": "Above Rs. 2 crore"},
    ]
