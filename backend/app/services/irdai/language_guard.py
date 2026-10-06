"""
Output language guard - RedoClaim.

Global rules for anything that reaches the user:

  1. A missed turnaround time (TAT) is reported as POTENTIAL TAT NON-COMPLIANCE
     and never as proof that the underlying decision is invalid.
  2. Waiting-period language never says a claim "is likely validly rejected".
  3. Consumer-law / grievance / Ombudsman time limits are never presented as
     fixed generic deadlines produced by the model.

The prompts ask the model to follow these rules; this guard is a deterministic
safety net applied to model output before it is returned or stored.
"""
import re
from typing import Any

TAT_CAVEAT = (
    "This does not by itself establish that the underlying claim or cashless "
    "decision is invalid."
)

# (pattern, replacement) - applied case-insensitively to every string value.
_REWRITES = [
    (r"procedurally (invalid|void|illegal|defective)", "potentially non-compliant with the applicable TAT"),
    (r"(denial|rejection|decision) (is|was|being) (legally |procedurally )?(invalid|void|illegal)",
     r"\1 may warrant review; the timing issue alone does not establish invalidity"),
    (r"(is|was) (hereby )?(legally )?invalid\b", "may warrant review"),
    (r"likely (to be )?validly rejected", "may be affected by the waiting period unless an exception applies"),
    (r"is likely to be validly rejected", "may be affected by the waiting period unless an exception applies"),
    (r"\bTAT (was )?violated\b", "potential TAT non-compliance"),
    (r"\bviolat(ed|es|ion of) (the )?(cashless )?(TAT|timeline)", "potential non-compliance with the applicable TAT"),
]
_COMPILED = [(re.compile(p, re.IGNORECASE), r) for p, r in _REWRITES]

_TAT_KEYS = {"tat_violation_detail"}


def soften_text(text: str) -> str:
    for rx, repl in _COMPILED:
        text = rx.sub(repl, text)
    return text


def soften_legal_language(obj: Any) -> Any:
    """Recursively rewrite string values in dicts/lists. Returns a new object."""
    if isinstance(obj, str):
        return soften_text(obj)
    if isinstance(obj, list):
        return [soften_legal_language(i) for i in obj]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            nv = soften_legal_language(v)
            if k in _TAT_KEYS and obj.get("tat_violated") and isinstance(nv, str) and nv and TAT_CAVEAT not in nv:
                nv = f"{nv.rstrip('. ')}. {TAT_CAVEAT}"
            out[k] = nv
        return out
    return obj
