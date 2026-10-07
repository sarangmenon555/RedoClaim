"""
Citation traceability - RedoClaim.

Why: the model used to see only a truncated JSON summary of the policy, with no
clause numbers, so it sometimes produced plausible but wrong references
("Clause 5.4" when the policy says 3.4). For an institution-facing tool every
policy reference must trace back to the supplied document.

Three parts:
  1. build_clause_index(policy_text)  - deterministic index of the clause numbers
     and headings that REALLY appear in the policy text (no model involved).
  2. format_reference_block(index)    - what the prompts show the model: the exact
     numbers, headings and short excerpts it may cite.
  3. verify_citations(obj, ...)       - after the model answers, every
     "Clause N" it wrote is checked against the index; unknown numbers are
     rewritten as "not found in the supplied policy text", and every
     policy_evidence excerpt is checked against the policy text.
"""
import re
from typing import Any, Optional

# A numbered heading at the start of a line: "3.4 Day-care treatment",
# "Clause 3.4 - Day Care", "3.4) OPD ...". Multi-level numbers are the norm in
# policy wordings; single-level numbers are accepted too (more permissive).
_HEADING_RE = re.compile(
    r"^[ \t]*(?:(?:clause|section|article|para(?:graph)?)[ \t]+)?"
    r"(\d{1,2}(?:\.\d{1,2}){0,3})[ \t]*[\).:\-\u2013\u2014]?[ \t]+(\S.{2,200})$",
    re.IGNORECASE | re.MULTILINE,
)
_CLAUSE_CITE_RE = re.compile(
    r"\b(?:Policy[ \t]+)?Clause[ \t]+(?:No\.?[ \t]*)?(\d{1,2}(?:\.\d{1,2}){0,3})(?![\d.]*\d)",
    re.IGNORECASE,
)
NOT_FOUND = "[clause number not found in the supplied policy text - verify]"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def build_clause_index(policy_text: Optional[str]) -> dict[str, dict]:
    """ref -> {"heading": str, "excerpt": str}, in document order."""
    index: dict[str, dict] = {}
    text = policy_text or ""
    matches = list(_HEADING_RE.finditer(text))
    for i, m in enumerate(matches):
        ref, heading = m.group(1), m.group(2).strip()
        if ref in index:
            continue
        end = matches[i + 1].start() if i + 1 < len(matches) else min(len(text), m.end() + 400)
        body = text[m.start():end]
        excerpt = re.sub(r"\s+", " ", body).strip()[:260]
        index[ref] = {"heading": heading[:120], "excerpt": excerpt}
    return index


def format_reference_block(index: dict[str, dict], limit: int = 70) -> str:
    if not index:
        return (
            "POLICY CLAUSE REFERENCE: no numbered clauses could be identified in the supplied policy text. "
            "Do NOT cite any clause number; quote the wording instead and say the clause number is not shown."
        )
    lines = ["POLICY CLAUSE REFERENCE (cite ONLY these clause numbers, with a short verbatim excerpt):"]
    for ref, v in list(index.items())[:limit]:
        lines.append(f"- Clause {ref} | {v['heading']} | \"{v['excerpt'][:200]}\"")
    return "\n".join(lines)


def _word_ngrams(text: str, n: int = 4) -> set:
    w = re.findall(r"[a-z0-9\u20b9%.,]+", _norm(text))
    return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def excerpt_in_text(excerpt: str, policy_text: str) -> bool:
    """True if the excerpt is (near-)verbatim present in the policy text."""
    ex = _norm(excerpt).strip(" .\"'")
    if not ex or not policy_text:
        return False
    if ex in _norm(policy_text):
        return True
    ex_grams = _word_ngrams(ex)
    if not ex_grams:
        return False
    hit = len(ex_grams & _word_ngrams(policy_text))
    return hit / len(ex_grams) >= 0.8


def verify_citations(obj: Any, policy_text: Optional[str], index: Optional[dict] = None, extra_text: Optional[str] = None) -> tuple[Any, dict]:
    """
    Returns (cleaned_obj, report). report = {"verified": [...], "unverified": [...],
    "excerpts_unverified": int, "policy_text_available": bool}.
    """
    index = index if index is not None else build_clause_index(policy_text)
    valid = set(index.keys())
    have_text = bool((policy_text or "").strip())
    report = {"verified": [], "unverified": [], "insurer_cited": [], "excerpts_unverified": 0, "policy_text_available": have_text}
    # Clause numbers that appear in the insurer's own letter: the model may legitimately
    # say "the insurer cites Clause 4.2". They are kept but are NOT verified against the policy.
    insurer_refs = {m.group(1) for m in _CLAUSE_CITE_RE.finditer(extra_text or "")}

    def fix_string(s: str) -> str:
        def sub(m):
            ref = m.group(1)
            if have_text and ref in valid:
                if ref not in report["verified"]:
                    report["verified"].append(ref)
                return m.group(0)
            if ref in insurer_refs:
                if ref not in report["insurer_cited"]:
                    report["insurer_cited"].append(ref)
                return m.group(0)
            if ref not in report["unverified"]:
                report["unverified"].append(ref)
            return f"clause {ref} {NOT_FOUND}"
        return _CLAUSE_CITE_RE.sub(sub, s)

    def walk(o):
        if isinstance(o, str):
            return fix_string(o)
        if isinstance(o, list):
            return [walk(i) for i in o]
        if isinstance(o, dict):
            out = {}
            for k, v in o.items():
                if k == "clause_ref" and isinstance(v, str) and v.strip():
                    ref = v.strip().lower().replace("clause", "").strip(" .")
                    if have_text and ref in valid:
                        report["verified"].append(ref) if ref not in report["verified"] else None
                        out[k] = ref
                    else:
                        report["unverified"].append(ref) if ref not in report["unverified"] else None
                        out[k] = None
                        out["clause_ref_note"] = "Clause number not found in the supplied policy text - verify."
                    continue
                out[k] = walk(v)
            ex = out.get("excerpt")
            if isinstance(ex, str) and ex.strip() and ("clause_ref" in out or "clause_ref_note" in out):
                ok = excerpt_in_text(ex, policy_text or "")
                out["excerpt_verified"] = ok
                if not ok:
                    report["excerpts_unverified"] += 1
            return out
        return o

    return walk(obj), report
