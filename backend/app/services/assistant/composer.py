import json
import logging

from app.services.assistant.context import Ctx

logger = logging.getLogger(__name__)


def _digest(results: dict, order: list) -> list:
    items = []
    for name in order:
        result = results.get(name)
        if not result:
            continue
        entry = {"tool": result["label"], "status": result["status"]}
        if result["status"] == "ok":
            entry["key_points"] = [str(h)[:500] for h in result["highlights"][:8]]
            answer = (result.get("data") or {}).get("answer")
            if answer:
                entry["answer"] = str(answer)[:2500]
        elif result["status"] == "needs_input":
            entry["needs"] = result.get("question")
            entry["details_needed"] = [f.get("label") for f in result.get("fields", [])]
        else:
            entry["note"] = result.get("message")
        items.append(entry)
    return items


def _fallback(results: dict, order: list) -> str:
    parts = []
    for name in order:
        result = results.get(name)
        if not result:
            continue
        if result["status"] == "ok":
            body = (result.get("data") or {}).get("answer") or "\n".join(f"- {h}" for h in result["highlights"][:6])
            parts.append(f"{result['label']}\n{body}".strip())
        elif result["status"] == "needs_input":
            parts.append(result.get("question", ""))
        else:
            parts.append(result.get("message", ""))
    return "\n\n".join(p for p in parts if p) or "I could not complete this request. Please try again."


async def compose_answer(ctx: Ctx, results: dict, order: list) -> str:
    only = [results[n] for n in order if n in results]
    if len(only) == 1 and only[0]["status"] == "ok":
        answer = (only[0].get("data") or {}).get("answer")
        if answer:
            return str(answer)

    try:
        from app.services.llm.gemini_service import gemini

        system = (
            "You are RedoClaim's assistant for Indian insurance policyholders. Write a clear reply in simple, "
            "plain English that a non-expert can follow. You are not a lawyer; this is not legal advice. "
            "Use only the findings provided: never invent facts, clause numbers, dates, amounts or outcomes. "
            "Use cautious wording such as 'may' and 'appears'; never state that an insurer broke the law. "
            "If a tool needs more information, ask for it plainly and say exactly what is needed. "
            "Format: short paragraphs, '- ' for list items, no other markdown, no headings, no emojis. "
            "Start with the most important point and end with the single most useful next step."
        )
        prompt = (
            f"The user wrote:\n{ctx.message[:1500]}\n\n"
            f"Findings from the tools that ran (JSON):\n{json.dumps(_digest(results, order), ensure_ascii=False)[:7000]}\n\n"
            "Write the reply."
        )
        text = await gemini.generate(model="gpt-5-nano", prompt=prompt, system=system, temperature=0.2, max_tokens=900)
        text = (text or "").strip()
        if text:
            return text
    except Exception as exc:
        logger.warning(f"Answer composition failed, using template: {exc}")
    return _fallback(results, order)
