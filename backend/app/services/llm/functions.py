"""
Function-calling tools for RedoClaim's GPT-5 Nano agent.

Each tool here is real: it queries your own Postgres/Qdrant data rather
than asking GPT to guess. GPT decides which tool(s) it needs; `run_agent`
below executes them against your backend and feeds the results back in,
so GPT stays the reasoning layer while your database stays the source
of truth (as recommended in the RedoClaim architecture notes).

Wire a new use case by:
  1. adding a schema to TOOL_SCHEMAS
  2. adding a matching branch in `_dispatch`
  3. calling `run_agent(prompt, system, db=db)` from your route/task
"""
import json
import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func as sa_func
from app.services.llm.gemini_service import gemini
from app.services.rag.rag_pipeline import search_irdai_regulations
from app.models.models import Claim, Document, Appeal, AppealType

logger = logging.getLogger(__name__)

DEADLINE_RULES = {
    "gro":            15,        # days to escalate to GRO after rejection
    "ombudsman":      45,        # days to file with Insurance Ombudsman
    "edaakhil":       15,        # days after unresolved grievance to trigger e-Daakhil eligibility
    "consumer_court": 365 * 2,   # limitation period, Consumer Protection Act 2019
}

OMBUDSMAN_CLAIM_LIMIT_INR = 50_00_000  # Rs. 50 Lakhs


# ── Tool schemas (OpenAI function-calling format) ──────────────────────────
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_regulations",
            "description": (
                "Search RedoClaim's own IRDAI regulation knowledge base (Qdrant) "
                "for passages relevant to a claim issue. Prefer this over general "
                "knowledge for anything regulatory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural-language description of the issue"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_policy_clause",
            "description": (
                "Fetch the extracted policy clauses already stored for a document "
                "(from prior OCR + extraction), optionally filtered to one clause type."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "UUID of the uploaded policy document"},
                    "clause_type": {
                        "type": "string",
                        "description": "Optional: one key from the extracted clauses, e.g. 'exclusions', 'waiting_periods', 'co_payment'",
                    },
                },
                "required": ["document_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_deadline",
            "description": "Calculate an IRDAI/CPA-mandated redressal deadline from a given date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Start date in YYYY-MM-DD, e.g. the rejection date"},
                    "rule": {
                        "type": "string",
                        "enum": list(DEADLINE_RULES.keys()),
                        "description": "Which deadline to compute",
                    },
                },
                "required": ["date", "rule"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_claim_status",
            "description": "Look up a claim's current status, dates, and stored audit report by its ID.",
            "parameters": {
                "type": "object",
                "properties": {"claim_id": {"type": "string", "description": "UUID of the claim"}},
                "required": ["claim_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_insurer_details",
            "description": (
                "Get aggregate stats RedoClaim has recorded for an insurer "
                "(claims logged, rejection/violation rate) plus the standard "
                "IRDAI grievance-escalation contacts. There is no separate "
                "insurer master table, so this is derived from claims on file."
            ),
            "parameters": {
                "type": "object",
                "properties": {"insurer_name": {"type": "string"}},
                "required": ["insurer_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_redressal_route",
            "description": (
                "Determine the recommended escalation route (GRO / Ombudsman / "
                "Consumer Court) given the claim amount and whether a GRO "
                "complaint has already been filed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "claim_amount": {"type": "number", "description": "Claim amount in INR"},
                    "gro_already_filed": {"type": "boolean"},
                },
                "required": ["claim_amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_appeal_draft",
            "description": "Persist a drafted appeal letter against a claim so the user can review/edit/submit it later.",
            "parameters": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string"},
                    "appeal_type": {"type": "string", "enum": [t.value for t in AppealType]},
                    "letter_content": {"type": "string"},
                    "legal_references": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of regulation citations used in the letter",
                    },
                },
                "required": ["claim_id", "appeal_type", "letter_content"],
            },
        },
    },
]


# ── Tool implementations ────────────────────────────────────────────────────
async def _get_policy_clause(args: dict, db) -> dict:
    doc_id = args["document_id"]
    result = await db.execute(select(Document).where(Document.id == UUID(doc_id)))
    doc = result.scalar_one_or_none()
    if not doc:
        return {"error": f"No document found with id {doc_id}"}
    clauses = doc.extracted_clauses or {}
    clause_type = args.get("clause_type")
    if clause_type:
        return {clause_type: clauses.get(clause_type, f"No '{clause_type}' key in extracted clauses")}
    return clauses


def _calculate_deadline(args: dict) -> dict:
    rule = args["rule"]
    days = DEADLINE_RULES.get(rule)
    if days is None:
        return {"error": f"Unknown rule '{rule}'. Valid rules: {list(DEADLINE_RULES.keys())}"}
    try:
        start = datetime.strptime(args["date"], "%Y-%m-%d")
    except ValueError:
        return {"error": "date must be in YYYY-MM-DD format"}
    deadline = start + timedelta(days=days)
    return {
        "rule": rule,
        "start_date": start.date().isoformat(),
        "days_allowed": days,
        "deadline": deadline.date().isoformat(),
        "days_remaining_from_today": (deadline - datetime.utcnow()).days,
    }


async def _get_claim_status(args: dict, db) -> dict:
    claim_id = args["claim_id"]
    result = await db.execute(select(Claim).where(Claim.id == UUID(claim_id)))
    claim = result.scalar_one_or_none()
    if not claim:
        return {"error": f"No claim found with id {claim_id}"}
    return {
        "claim_id": str(claim.id),
        "insurer_name": claim.insurer_name,
        "claim_amount": claim.claim_amount,
        "insurance_type": claim.insurance_type.value if claim.insurance_type else None,
        "status": claim.status.value if claim.status else None,
        "irdai_violation": claim.irdai_violation,
        "rejection_date": claim.rejection_date.isoformat() if claim.rejection_date else None,
        "gro_deadline": claim.gro_deadline.isoformat() if claim.gro_deadline else None,
        "irdai_deadline": claim.irdai_deadline.isoformat() if claim.irdai_deadline else None,
        "audit_report": claim.audit_report,
    }


async def _get_insurer_details(args: dict, db) -> dict:
    insurer_name = args["insurer_name"]
    result = await db.execute(
        select(sa_func.count(Claim.id)).where(Claim.insurer_name.ilike(f"%{insurer_name}%"))
    )
    total = result.scalar() or 0

    violations_result = await db.execute(
        select(sa_func.count(Claim.id)).where(
            Claim.insurer_name.ilike(f"%{insurer_name}%"),
            Claim.irdai_violation.is_(True),
        )
    )
    violations = violations_result.scalar() or 0

    return {
        "insurer_name": insurer_name,
        "claims_on_file_with_redoclaim": total,
        "claims_with_flagged_irdai_violation": violations,
        "note": "RedoClaim has no separate insurer master table — these are stats derived from claims logged in this system, not an official IRDAI insurer registry.",
        "standard_escalation_contacts": {
            "gro": "Insurer's Grievance Redressal Officer — contact listed on policy document / insurer website",
            "irdai_igms": "https://igms.irda.gov.in",
            "ombudsman": "https://www.cioins.co.in",
            "consumer_edaakhil": "https://edaakhil.nic.in",
        },
    }


def _find_redressal_route(args: dict) -> dict:
    amount = args["claim_amount"]
    gro_filed = args.get("gro_already_filed", False)

    if not gro_filed:
        return {
            "recommended_action": "gro_appeal",
            "reasoning": "No GRO complaint filed yet — IRDAI process requires exhausting the insurer's internal GRO channel first, unless it has already been unresolved for 30+ days.",
        }
    if amount <= OMBUDSMAN_CLAIM_LIMIT_INR:
        return {
            "recommended_action": "ombudsman",
            "reasoning": f"Claim amount (₹{amount:,.0f}) is within the Insurance Ombudsman's ₹50,00,000 jurisdiction limit, and GRO has already been approached. Ombudsman is free and faster than Consumer Court.",
            "ombudsman_eligible": True,
        }
    return {
        "recommended_action": "consumer_court",
        "reasoning": f"Claim amount (₹{amount:,.0f}) exceeds the Ombudsman's ₹50,00,000 limit, so this must go to the Consumer Court (District/State/National Commission by value) via e-Daakhil.",
        "ombudsman_eligible": False,
    }


async def _save_appeal_draft(args: dict, db) -> dict:
    claim_id = args["claim_id"]
    result = await db.execute(select(Claim).where(Claim.id == UUID(claim_id)))
    claim = result.scalar_one_or_none()
    if not claim:
        return {"error": f"No claim found with id {claim_id}"}

    appeal = Appeal(
        owner_id=claim.owner_id,
        claim_id=claim.id,
        appeal_type=AppealType(args["appeal_type"]),
        letter_content=args["letter_content"],
        legal_references=args.get("legal_references", []),
        model_used="gpt-5-nano",
    )
    db.add(appeal)
    await db.commit()
    await db.refresh(appeal)
    return {"appeal_id": str(appeal.id), "status": "saved"}


async def _dispatch(name: str, args: dict, db) -> dict:
    if name == "search_regulations":
        return {"context": await search_irdai_regulations(args["query"])}
    if name == "get_policy_clause":
        return await _get_policy_clause(args, db)
    if name == "calculate_deadline":
        return _calculate_deadline(args)
    if name == "get_claim_status":
        return await _get_claim_status(args, db)
    if name == "get_insurer_details":
        return await _get_insurer_details(args, db)
    if name == "find_redressal_route":
        return _find_redressal_route(args)
    if name == "save_appeal_draft":
        return await _save_appeal_draft(args, db)
    return {"error": f"Unknown tool '{name}'"}


# ── Agent loop ───────────────────────────────────────────────────────────
async def run_agent(
    prompt: str,
    system: str = "",
    model: str = "gemini-2.5-flash",
    db=None,
    max_steps: int = 4,
) -> str:
    """
    Multi-turn function-calling loop: GPT-5 Nano picks tools from
    TOOL_SCHEMAS, we execute them against real Postgres/Qdrant data via
    `_dispatch`, and feed the results back until GPT returns a final answer.

    `db` is an AsyncSession — required for any tool that touches Postgres
    (get_policy_clause, get_claim_status, get_insurer_details,
    save_appeal_draft). search_regulations and calculate_deadline work
    without it.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    for _ in range(max_steps):
        message = await gemini.chat_raw(
            model=model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )

        if not getattr(message, "tool_calls", None):
            return message.content or ""

        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in message.tool_calls
            ],
        })

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments or "{}")
            try:
                result = await _dispatch(tool_call.function.name, args, db)
            except Exception as e:
                logger.error(f"Tool {tool_call.function.name} failed: {e}")
                result = {"error": str(e)}

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, default=str),
            })

    logger.warning("run_agent hit max_steps without a final answer")
    return "The assistant reached the tool-call limit without producing a final answer."
