import asyncio
import logging
import re
from typing import Optional

from app.models.models import AppealType, Claim, InsuranceType
from app.api.routes import analysis as analysis_routes
from app.api.routes import appeals as appeals_routes
from app.services.irdai.rules_engine import irdai_engine
from app.services.llm.functions import run_agent
from app.services.rag.rag_pipeline import search_irdai_regulations
from app.services.llm.gemini_service import generate_portability_guide
from app.services.assistant.context import (
    Ctx, doc_field, failed, guarded, need, ok, unavailable, value_field,
)
from app.services.assistant.doc_classifier import (
    KIND_LABELS, extract_basic_facts, extract_bill_total, guess_insurance_type,
)
from app.services.irdai.consumer_fees import describe as describe_consumer_fee
from app.services.assistant.guard import check_answer
from app.services.assistant.ombudsman_lookup import find_offices
from app.services.assistant.verified_facts import APP_PAGES, facts_text, retrieve_facts
from app.services.assistant.params import as_lines, inr, to_float, to_text

logger = logging.getLogger(__name__)

INTENT_LABELS = {
    "audit_rejection": "Rejection audit",
    "analyze_policy": "Policy analysis",
    "scan_cis": "Customer Information Sheet review",
    "audit_settlement": "Settlement second opinion",
    "preauth_check": "Cashless denial check",
    "estimate_payout": "Payout estimate",
    "waiting_period": "Waiting period check",
    "compare_policies": "Policy comparison",
    "renewal_check": "Renewal check",
    "copay_breakdown": "Co-pay and room rent breakdown",
    "portability": "Portability guide",
    "explain_term": "Plain-language explanation",
    "ncb_check": "No-claim bonus check",
    "sum_insured_check": "Sum insured adequacy check",
    "draft_appeal": "Appeal letter",
    "cost_benefit": "Worth-pursuing check",
    "followup_letter": "Follow-up letter",
    "precedents": "Similar past cases",
    "ejagriti_guide": "Consumer commission guide",
    "ombudsman_contact": "Insurance Ombudsman office",
    "verify_response": "How to check the insurer's response",
    "general_question": "Answer",
}


def clauses_ok(doc) -> bool:
    clauses = doc.extracted_clauses
    return isinstance(clauses, dict) and bool(clauses) and not clauses.get("parse_error")


def _clauses(doc) -> dict:
    return doc.extracted_clauses if clauses_ok(doc) else {}


def _policy(ctx: Ctx, label: str, purpose: str):
    candidates = ctx.docs_of("policy")
    readable = [d for d in candidates if clauses_ok(d)]
    if readable:
        return readable[0], None
    if candidates:
        return None, unavailable(
            label,
            "I could not read your policy clearly enough to " + purpose + ". A clearer copy (a PDF is best) should help.",
        )
    return None, need(label, f"Please attach your policy document so I can {purpose}.", [doc_field("policy", "Your insurance policy document")])


def _facts(*docs) -> dict:
    merged: dict = {}
    for doc in docs:
        if doc is None:
            continue
        stored = doc.extracted_clauses if isinstance(doc.extracted_clauses, dict) else {}
        for key in ("insurer_name", "policy_number"):
            value = to_text(stored.get(key))
            if value:
                merged.setdefault(key, value)
        for key, value in extract_basic_facts(doc.ocr_text or "").items():
            merged.setdefault(key, value)
    return merged


def _insurance_type(ctx: Ctx, *docs) -> InsuranceType:
    stated = ctx.text("insurance_type")
    if stated:
        try:
            return InsuranceType(stated)
        except ValueError:
            pass
    for doc in docs:
        if doc is not None and doc.insurance_type:
            try:
                return InsuranceType(doc.insurance_type.value if hasattr(doc.insurance_type, "value") else doc.insurance_type)
            except ValueError:
                continue
    for doc in docs:
        if doc is not None and doc.ocr_text:
            return guess_insurance_type(doc.ocr_text, ctx.kinds.get(str(doc.id), "other"))
    return InsuranceType.HEALTH


def _parse_money(value) -> Optional[float]:
    return to_float(value)


def _first_present(*values):
    for value in values:
        if value is not None:
            return value
    return None


async def run_audit_rejection(ctx: Ctx) -> dict:
    label = INTENT_LABELS["audit_rejection"]
    rejection = ctx.first("rejection_letter")
    if rejection is None:
        return need(label, "Please attach the claim rejection letter you received so I can check it against your policy and the IRDAI rules.",
                    [doc_field("rejection_letter", "The rejection or repudiation letter from your insurer")])

    policy = ctx.first("policy")
    cis = ctx.first("cis")
    facts = _facts(policy, rejection)
    insurer = ctx.text("insurer_name") or facts.get("insurer_name") or "Not stated"
    policy_number = ctx.text("policy_number") or facts.get("policy_number") or "Not stated"
    claim_amount = _first_present(ctx.num("claim_amount"), facts.get("claim_amount"))

    request = analysis_routes.AuditRequest(
        rejection_document_id=str(rejection.id),
        policy_document_id=str(policy.id) if policy else None,
        cis_document_id=str(cis.id) if cis else None,
        insurer_name=insurer,
        policy_number=policy_number,
        claim_amount=claim_amount,
        insurance_type=_insurance_type(ctx, rejection, policy),
        claim_date=ctx.when("claim_date"),
        rejection_date=ctx.when("rejection_date"),
        gro_filed=bool(ctx.flag("gro_filed")),
        gro_filed_date=ctx.when("gro_filed_date"),
        policy_inception_date=ctx.when("policy_inception_date"),
        documents_complete_date=ctx.when("documents_complete_date"),
        output_language="en",
        patient_name=ctx.text("patient_name"),
        patient_relationship=ctx.text("patient_relationship"),
    )

    result, error = await guarded(ctx, label, lambda: analysis_routes.audit_claim_rejection(req=request, db=ctx.db, current_user=ctx.user))
    if error:
        return error

    result = analysis_routes._make_json_serializable(result)
    claim_id = result.get("claim_id")
    if claim_id:
        ctx.claim_id = claim_id

    summary = result.get("summary") or {}
    report = result.get("report") or {}
    hoe = report.get("hierarchy_of_evidence") or {}
    step1 = hoe.get("step1_sla") or {}
    audit = (hoe.get("step2_regulations") or {}).get("audit") or {}
    step3 = hoe.get("step3_redressal") or {}

    lines = []
    if summary.get("evidence_status") == "insufficient":
        lines.append("The documents do not yet give enough evidence for a firm view on this rejection.")
    elif summary.get("is_valid_rejection") is False:
        lines.append("On the documents provided, the rejection may not be consistent with the policy terms or IRDAI rules.")
    elif summary.get("is_valid_rejection") is True:
        lines.append("On the documents provided, the rejection appears to be consistent with the policy terms.")

    total = summary.get("total_violations_found") or 0
    if total:
        lines.append(
            f"{total} potential issue(s) flagged for your review "
            f"({summary.get('sla_violations', 0)} timeline, {summary.get('irdai_violations', 0)} regulatory)."
        )
    if summary.get("strength_of_case"):
        lines.append(f"Informational strength rating of the case: {summary['strength_of_case']}.")
    for gap in as_lines(summary.get("evidence_gaps"), 3):
        lines.append(f"Evidence gap: {gap}")
    for action in as_lines(summary.get("recommended_action"), 1):
        lines.append(f"Suggested route: {action}")
    if summary.get("moratorium_shield"):
        lines.append("A moratorium-period protection may apply to this claim.")
    if summary.get("ejagriti_applicable"):
        lines.append("A consumer commission complaint through e-Jagriti may be an option, after the earlier escalation steps.")

    deadlines = step1.get("deadlines") or {}
    days_left = deadlines.get("days_left_for_ombudsman_window")
    if days_left is not None:
        lines.append(f"Indicative Ombudsman filing window: about {days_left} day(s) left. Please verify the exact date with the Ombudsman procedure.")
    if insurer == "Not stated" or policy_number == "Not stated":
        lines.append("I could not find the insurer name or policy number in your documents. You can correct them on the claim page.")

    issues = []
    for item in (audit.get("step2_regulatory_violations") or [])[:5]:
        if isinstance(item, dict):
            issues.append({
                "title": item.get("violation"),
                "reference": item.get("regulation"),
                "severity": item.get("severity"),
                "argument": item.get("argument"),
            })
    for item in (step1.get("sla_violations") or [])[:4]:
        if isinstance(item, dict):
            issues.append({
                "title": item.get("detail"),
                "reference": item.get("regulation"),
                "severity": "timeline",
                "argument": item.get("basis"),
            })

    escalation = []
    for item in (step3.get("escalation_path") or [])[:4]:
        if isinstance(item, dict):
            escalation.append({
                "step": item.get("step"),
                "route": item.get("route"),
                "how": item.get("how"),
                "cost": item.get("cost"),
                "deadline": item.get("deadline"),
            })

    links = [{"label": "Open full report", "href": f"/dashboard/claims/{claim_id}"}] if claim_id else []
    return ok(label, lines, {
        "claim_id": claim_id,
        "summary": summary,
        "issues": issues,
        "escalation": escalation,
        "insurer_name": insurer,
        "policy_number": policy_number,
        "recommended_appeal_type": _appeal_from_action(summary.get("recommended_action")),
    }, links)


def _appeal_from_action(action) -> str:
    text = " ".join(as_lines(action, 2)).lower()
    if "ombudsman" in text:
        return "ombudsman"
    if "consumer" in text or "jagriti" in text:
        return "consumer_court"
    return "gro"


async def run_analyze_policy(ctx: Ctx) -> dict:
    label = INTENT_LABELS["analyze_policy"]
    policy, error = _policy(ctx, label, "explain what it covers")
    if error:
        return error
    clauses = _clauses(policy)

    lines = []
    if clauses.get("plain_english_summary"):
        lines.append(str(clauses["plain_english_summary"]))
    if clauses.get("sum_insured"):
        lines.append(f"Sum insured: {clauses['sum_insured']}")
    copay = clauses.get("co_payment")
    if isinstance(copay, dict) and copay.get("percentage"):
        applies = f" ({copay['applies_to']})" if copay.get("applies_to") else ""
        lines.append(f"Co-payment: {copay['percentage']}{applies}")
    room = clauses.get("room_rent_cap")
    if isinstance(room, dict) and room.get("limit"):
        lines.append(f"Room rent limit: {room['limit']}")

    waiting = [w for w in (clauses.get("waiting_periods") or []) if isinstance(w, dict)]
    exclusions = [e for e in (clauses.get("exclusions") or []) if isinstance(e, dict)]
    inclusions = [i for i in (clauses.get("inclusions") or []) if isinstance(i, dict)]
    if waiting:
        lines.append(f"{len(waiting)} waiting period(s) listed in the policy.")
    if exclusions:
        lines.append(f"{len(exclusions)} exclusion(s) listed in the policy.")

    risky = [r for r in (clauses.get("risky_clauses") or []) if isinstance(r, dict)]
    for item in risky[:3]:
        text = " - ".join(x for x in [to_text(item.get("clause"), 140), to_text(item.get("explanation"), 220)] if x)
        if text:
            lines.append(f"Worth checking: {text}")

    return ok(label, lines, {
        "document_id": str(policy.id),
        "file_name": policy.file_name,
        "insurer_name": clauses.get("insurer_name"),
        "policy_number": clauses.get("policy_number"),
        "sum_insured": clauses.get("sum_insured"),
        "inception_date": clauses.get("inception_date"),
        "waiting_periods": [{"condition": w.get("condition"), "duration": w.get("duration"), "risk_level": w.get("risk_level")} for w in waiting[:10]],
        "exclusions": [{"title": e.get("clause"), "description": e.get("description"), "risk_level": e.get("risk_level")} for e in exclusions[:10]],
        "inclusions": [{"title": i.get("benefit"), "limit": i.get("limit")} for i in inclusions[:10]],
        "risky_clauses": [{"title": r.get("clause"), "explanation": r.get("explanation"), "category": r.get("category")} for r in risky[:6]],
    })


async def run_scan_cis(ctx: Ctx) -> dict:
    label = INTENT_LABELS["scan_cis"]
    cis = ctx.first("cis")
    if cis is None:
        return need(label, "Please attach the Customer Information Sheet (CIS) from your insurer.", [doc_field("cis", "Customer Information Sheet")])
    result, error = await guarded(ctx, label, lambda: analysis_routes.scan_cis(document_id=str(cis.id), db=ctx.db, current_user=ctx.user))
    if error:
        return error
    analysis = result.get("cis_analysis") or {}
    lines = []
    if analysis.get("plain_english_inclusions"):
        lines.append(f"Covered: {analysis['plain_english_inclusions']}")
    if analysis.get("plain_english_exclusions"):
        lines.append(f"Not covered: {analysis['plain_english_exclusions']}")
    for item in [r for r in (analysis.get("risky_exclusions") or []) if isinstance(r, dict)][:3]:
        text = " - ".join(x for x in [to_text(item.get("exclusion"), 140), to_text(item.get("risk"), 200)] if x)
        if text:
            lines.append(f"Worth checking: {text}")
    return ok(label, lines, {
        "inclusions": analysis.get("inclusions"),
        "exclusions": analysis.get("exclusions"),
        "risky_exclusions": analysis.get("risky_exclusions"),
    })


async def run_audit_settlement(ctx: Ctx) -> dict:
    label = INTENT_LABELS["audit_settlement"]
    letter = ctx.first("settlement_letter")
    if letter is None:
        return need(label, "Please attach the settlement letter in which your insurer explains what it paid and what it deducted.",
                    [doc_field("settlement_letter", "The insurer's settlement letter")])
    claim_amount = _first_present(ctx.num("claim_amount"), _facts(letter).get("claim_amount"))
    settled = ctx.num("settled_amount")
    missing = []
    if claim_amount is None:
        missing.append(value_field("claim_amount", "Amount you originally claimed", "for example 150000"))
    if settled is None:
        missing.append(value_field("settled_amount", "Amount the insurer actually paid", "for example 90000"))
    if missing:
        return need(label, "To check the deductions I need two amounts: what you claimed and what the insurer paid.", missing)

    policy = ctx.first("policy")
    request = analysis_routes.SettlementAuditRequest(
        settlement_document_id=str(letter.id),
        policy_document_id=str(policy.id) if policy else None,
        claim_amount=claim_amount,
        settled_amount=settled,
    )
    result, error = await guarded(ctx, label, lambda: analysis_routes.audit_settlement_route(body=request, db=ctx.db, current_user=ctx.user))
    if error:
        return error
    result = analysis_routes._make_json_serializable(result)

    lines = [f"Claimed {inr(claim_amount)}, paid {inr(settled)}, shortfall {inr(claim_amount - settled)}."]
    likely = result.get("is_settlement_likely_correct")
    if likely is True:
        lines.append("The deductions look consistent with the policy terms on record.")
    elif likely is False:
        lines.append("Some deductions may not be supported by the policy terms on record.")
    questionable = to_float(result.get("total_questionable_deduction"))
    if questionable:
        lines.append(f"Deductions that may be questionable add up to about {inr(questionable)}.")
    if result.get("reasoning"):
        lines.append(str(result["reasoning"]))
    if policy is None:
        lines.append("Attaching your policy document would let me check each deduction against the actual wording.")

    reviewed = [d for d in (result.get("deductions_reviewed") or []) if isinstance(d, dict)]
    return ok(label, lines, {
        "claim_amount": claim_amount,
        "settled_amount": settled,
        "deductions_reviewed": [
            {"reason": d.get("stated_reason"), "amount": d.get("amount_deducted"), "justified": d.get("justified_by_policy"), "explanation": d.get("explanation")}
            for d in reviewed[:8]
        ],
        "key_arguments": as_lines(result.get("key_arguments"), 5),
        "recommended_action": result.get("recommended_action"),
    })


async def run_preauth_check(ctx: Ctx) -> dict:
    label = INTENT_LABELS["preauth_check"]
    denial = ctx.first("preauth_denial")
    if denial is None:
        return need(label, "Please attach the letter or message in which the hospital or insurer denied your cashless request.",
                    [doc_field("preauth_denial", "The cashless pre-authorisation denial")])
    policy = ctx.first("policy")
    request = analysis_routes.PreAuthCheckRequest(
        denial_document_id=str(denial.id),
        policy_document_id=str(policy.id) if policy else None,
        treatment_amount=ctx.num("treatment_amount"),
    )
    result, error = await guarded(ctx, label, lambda: analysis_routes.preauth_check_route(body=request, db=ctx.db, current_user=ctx.user))
    if error:
        return error
    result = analysis_routes._make_json_serializable(result)

    lines = []
    if result.get("denial_reason_summary"):
        lines.append(str(result["denial_reason_summary"]))
    if result.get("is_valid_denial") is True:
        lines.append("The stated reason appears consistent with the policy on the documents provided.")
    elif result.get("is_valid_denial") is False:
        lines.append("The stated reason may be open to challenge on the documents provided.")
    if result.get("tat_violation_detail"):
        lines.append(str(result["tat_violation_detail"]))
    if result.get("reimbursement_path_note"):
        lines.append(str(result["reimbursement_path_note"]))
    if result.get("reasoning"):
        lines.append(str(result["reasoning"]))
    return ok(label, lines, {
        "reason_category": result.get("denial_reason_category"),
        "recommendation": result.get("immediate_recommendation"),
        "key_arguments": as_lines(result.get("key_arguments"), 5),
    })


async def run_estimate_payout(ctx: Ctx) -> dict:
    label = INTENT_LABELS["estimate_payout"]
    policy, error = _policy(ctx, label, "estimate what it may pay")
    if error:
        return error
    amount = ctx.num("claim_amount")
    assumed_from_bill = False
    if amount is None:
        bill = ctx.first("hospital_bill")
        total = extract_bill_total(bill.ocr_text) if bill is not None else None
        if total:
            amount, assumed_from_bill = total, True
    if amount is None or amount <= 0:
        return need(label, "What is the total amount of the bill or claim? You can also attach the hospital bill.",
                    [value_field("claim_amount", "Total bill or claim amount", "for example 250000")])

    request = analysis_routes.PayoutEstimateRequest(
        claim_amount=amount, document_id=str(policy.id), claim_id=ctx.claim_id, patient_age=ctx.whole("patient_age"),
    )
    result, error = await guarded(ctx, label, lambda: analysis_routes.estimate_payout_route(body=request, db=ctx.db, current_user=ctx.user))
    if error:
        return error

    lines = []
    if assumed_from_bill:
        lines.append(f"I used the total on your hospital bill ({inr(amount)}) as the claim amount.")
    if result.get("can_estimate") and result.get("estimated_payout") is not None:
        band = result.get("estimated_payout_range") or []
        extra = f", roughly {inr(band[0])} to {inr(band[1])}" if len(band) == 2 else ""
        lines.append(f"Estimated eligible amount: {inr(result['estimated_payout'])}{extra}. Deductions: {inr(result.get('total_deductions', 0))}.")
        for deduction in [d for d in (result.get("deductions") or []) if isinstance(d, dict)][:4]:
            lines.append(f"{deduction.get('reason')}: {inr(deduction.get('amount', 0))}")
    else:
        lines.append("There is not enough information in the policy to give a reliable estimate.")
        for item in as_lines(result.get("missing_inputs"), 3):
            lines.append(f"Missing: {item}")
    for item in as_lines(result.get("assumptions"), 2):
        lines.append(f"Assumption: {item}")

    return ok(label, lines, {
        "claim_amount": amount,
        "estimated_payout": result.get("estimated_payout"),
        "range": result.get("estimated_payout_range"),
        "deductions": result.get("deductions"),
        "confidence": result.get("confidence"),
    })


async def run_waiting_period(ctx: Ctx) -> dict:
    label = INTENT_LABELS["waiting_period"]
    policy, error = _policy(ctx, label, "check your waiting periods")
    if error:
        return error
    request = analysis_routes.WaitingPeriodRequest(
        document_id=str(policy.id),
        as_of_date=ctx.text("as_of_date"),
        accident_related=ctx.flag("accident_related"),
        accident_date=ctx.text("accident_date"),
    )
    result, error = await guarded(ctx, label, lambda: analysis_routes.waiting_period_check(body=request, db=ctx.db, current_user=ctx.user))
    if error:
        return error
    result = analysis_routes._make_json_serializable(result)

    periods = [p for p in (result.get("waiting_periods") or []) if isinstance(p, dict)]
    lines = [f"Checked as of {result.get('checked_as_of')} against a policy start date of {result.get('inception_date')}."]
    for period in periods[:6]:
        lapse = f" (ends {period['lapses_on']})" if period.get("lapses_on") else ""
        lines.append(f"{period.get('condition')}: {period.get('duration_as_stated')} - {str(period.get('status', '')).replace('_', ' ')}{lapse}")
    for exception in as_lines(result.get("exceptions_identified"), 2):
        lines.append(f"Possible exception: {exception}")
    return ok(label, lines, {
        "checked_as_of": result.get("checked_as_of"),
        "inception_date": result.get("inception_date"),
        "waiting_periods": [
            {"condition": p.get("condition"), "duration": p.get("duration_as_stated"), "status": p.get("status"), "ends": p.get("lapses_on"), "note": p.get("note")}
            for p in periods[:12]
        ],
    })


async def run_compare_policies(ctx: Ctx) -> dict:
    label = INTENT_LABELS["compare_policies"]
    policies = [d for d in ctx.docs_of("policy") if clauses_ok(d)][:3]
    if len(policies) < 2:
        return need(label, "To compare policies I need at least two policy documents. Please attach the other one.",
                    [doc_field("policy", "A second policy document")])
    request = analysis_routes.PolicyCompareRequest(document_ids=[str(d.id) for d in policies])
    result, error = await guarded(ctx, label, lambda: analysis_routes.compare_policies_route(body=request, db=ctx.db, current_user=ctx.user))
    if error:
        return error
    rows = [r for r in (result.get("comparison_rows") or []) if isinstance(r, dict)]
    names = [d.file_name for d in policies]
    lines = []
    for row in rows[:8]:
        values = [str(v.get("display")) for v in (row.get("values") or []) if isinstance(v, dict)]
        lines.append(f"{row.get('attribute')}: " + " | ".join(values))
    return ok(label, lines, {"policies": names, "rows": [{"attribute": r.get("attribute"), "values": [v.get("display") for v in (r.get("values") or []) if isinstance(v, dict)]} for r in rows]})


async def run_renewal_check(ctx: Ctx) -> dict:
    label = INTENT_LABELS["renewal_check"]
    policies = [d for d in ctx.docs_of("policy") if clauses_ok(d)]
    if len(policies) < 2:
        return need(label, "To check a renewal I need both last year's policy and the new renewal document.",
                    [doc_field("policy", "Last year's policy and this year's renewal")])
    ordered = sorted(policies[:2], key=lambda d: str((d.extracted_clauses or {}).get("inception_date") or "9999"))
    request = analysis_routes.RenewalCheckRequest(old_policy_document_id=str(ordered[0].id), new_policy_document_id=str(ordered[1].id))
    result, error = await guarded(ctx, label, lambda: analysis_routes.renewal_check_route(body=request, db=ctx.db, current_user=ctx.user))
    if error:
        return error
    lines = []
    if result.get("overall_verdict"):
        lines.append(str(result["overall_verdict"]))
    flags = [f for f in (result.get("red_flags") or []) if isinstance(f, dict)]
    for flag in flags[:5]:
        lines.append(f"{str(flag.get('severity', '')).title()} - {flag.get('field')}: {flag.get('old_value')} to {flag.get('new_value')}. {flag.get('explanation', '')}".strip())
    return ok(label, lines, {
        "red_flags": [{"field": f.get("field"), "old": f.get("old_value"), "new": f.get("new_value"), "severity": f.get("severity"), "explanation": f.get("explanation")} for f in flags],
        "neutral_changes": as_lines(result.get("neutral_changes"), 6),
    })


async def run_copay_breakdown(ctx: Ctx) -> dict:
    label = INTENT_LABELS["copay_breakdown"]
    policy, error = _policy(ctx, label, "work out the room rent and co-pay deductions")
    if error:
        return error
    total = ctx.num("total_bill_amount")
    from_bill = False
    if total is None:
        bill = ctx.first("hospital_bill")
        found = extract_bill_total(bill.ocr_text) if bill is not None else None
        if found:
            total, from_bill = found, True
    missing = []
    if total is None:
        missing.append(value_field("total_bill_amount", "Total hospital bill", "for example 250000"))
    if ctx.num("room_rent_per_day") is None:
        missing.append(value_field("room_rent_per_day", "Room rent you were charged per day", "for example 8000"))
    if missing:
        return need(label, "To work out the deductions I need a couple of figures from your hospital bill.", missing)

    request = analysis_routes.CopayBreakdownRequest(
        document_id=str(policy.id),
        total_bill_amount=total,
        actual_room_rent_per_day=ctx.num("room_rent_per_day"),
        days_admitted=ctx.whole("days_admitted") or 1,
        patient_age=ctx.whole("patient_age"),
    )
    result, error = await guarded(ctx, label, lambda: analysis_routes.copay_breakdown_route(body=request, db=ctx.db, current_user=ctx.user))
    if error:
        return error
    lines = []
    if from_bill:
        lines.append(f"I used the total on your hospital bill ({inr(total)}).")
    lines.append(f"Estimated insurer payout: {inr(result.get('estimated_insurer_payout', 0))}. Your out-of-pocket share: {inr(result.get('your_out_of_pocket', 0))}.")
    for deduction in [d for d in (result.get("deductions") or []) if isinstance(d, dict)][:4]:
        lines.append(f"{deduction.get('reason') or deduction.get('type')}: {inr(deduction.get('amount', 0))}")
    return ok(label, lines, {
        "total_bill_amount": total,
        "estimated_insurer_payout": result.get("estimated_insurer_payout"),
        "your_out_of_pocket": result.get("your_out_of_pocket"),
        "deductions": result.get("deductions"),
        "notes": as_lines(result.get("notes"), 4),
    })


async def run_portability(ctx: Ctx) -> dict:
    label = INTENT_LABELS["portability"]
    years = ctx.num("years_covered")
    if years is None:
        return need(label, "For how many years have you held your current health policy without a break?",
                    [value_field("years_covered", "Years of continuous cover", "for example 3")])
    policy = ctx.first("policy")
    clauses = _clauses(policy) if policy is not None else {}
    reason = ctx.text("reason_for_porting") or "Better cover or service"

    async def build():
        guide = await generate_portability_guide(current_policy=clauses, years_covered=years, reason_for_porting=reason)
        advice = irdai_engine.portability_advisor(policy_clauses=clauses, years_covered=years)
        return guide, advice

    built, error = await guarded(ctx, label, build)
    if error:
        return error
    guide, advice = built
    lines = []
    if isinstance(guide, str) and guide.strip():
        lines.append(guide.strip()[:900])
    lines.extend(as_lines(advice.get("key_rights"), 4))
    return ok(label, lines, {
        "key_rights": as_lines(advice.get("key_rights"), 8),
        "how_to_port": as_lines(advice.get("how_to_port"), 8),
        "regulation": advice.get("regulation"),
    })


async def run_explain_term(ctx: Ctx) -> dict:
    label = INTENT_LABELS["explain_term"]
    term = ctx.text("term") or ctx.message[:500]
    request = analysis_routes.ExplainTermRequest(term_or_clause=term, output_language="en")
    result, error = await guarded(ctx, label, lambda: analysis_routes.explain_term_route(body=request, current_user=ctx.user))
    if error:
        return error
    lines = [str(result[k]) for k in ("plain_explanation", "example", "why_it_matters") if result.get(k)]
    allowed = facts_text(retrieve_facts(f"{term} {ctx.message}", "", limit=6))
    checked = check_answer("\n".join(lines), allowed, "", f"{term} {ctx.message}")
    lines = [line for line in checked["answer"].split("\n") if line.strip()]
    return ok(label, lines, {"term": result.get("term") or term})


async def run_ncb_check(ctx: Ctx) -> dict:
    label = INTENT_LABELS["ncb_check"]
    missing = []
    if ctx.whole("claim_free_years") is None:
        missing.append(value_field("claim_free_years", "Claim-free years so far", "for example 3"))
    if ctx.num("od_premium_before_ncb") is None:
        missing.append(value_field("od_premium_before_ncb", "Own-damage premium before any discount", "for example 12000"))
    if ctx.num("ncb_applied_by_insurer") is None:
        missing.append(value_field("ncb_applied_by_insurer", "No-claim bonus percentage your insurer applied", "for example 25"))
    if missing:
        return need(label, "To check your no-claim bonus I need these figures from your renewal quote.", missing)
    request = analysis_routes.NCBCheckRequest(
        claim_free_years=ctx.whole("claim_free_years"),
        od_premium_before_ncb=ctx.num("od_premium_before_ncb"),
        ncb_applied_by_insurer=ctx.num("ncb_applied_by_insurer"),
        had_claim_this_year=bool(ctx.flag("had_claim_this_year")),
    )
    result, error = await guarded(ctx, label, lambda: analysis_routes.ncb_check_route(body=request, current_user=ctx.user))
    if error:
        return error
    lines = [str(result.get("note"))] if result.get("note") else []
    if result.get("is_shortchanged"):
        lines.append(f"You may be owed about {inr(result.get('shortfall_amount', 0))} in discount.")
    return ok(label, lines, {
        "expected_ncb_percent": result.get("expected_ncb_percent"),
        "applied_ncb_percent": result.get("ncb_applied_by_insurer"),
        "shortfall_amount": result.get("shortfall_amount"),
    })


async def run_sum_insured_check(ctx: Ctx) -> dict:
    label = INTENT_LABELS["sum_insured_check"]
    policy = ctx.first("policy")
    sum_insured = ctx.num("sum_insured")
    if sum_insured is None and policy is not None:
        sum_insured = _parse_money(_clauses(policy).get("sum_insured"))
    missing = []
    if sum_insured is None:
        missing.append(value_field("sum_insured", "Your sum insured", "for example 500000"))
    if not ctx.text("city_tier"):
        missing.append(value_field("city_tier", "Type of city you live in", "metro, tier 1 or tier 2"))
    if not ctx.ages():
        missing.append(value_field("family_ages", "Ages of everyone to be covered", "for example 35, 32, 6"))
    if missing:
        return need(label, "To judge whether your cover is enough I need a few details.", missing)
    request = analysis_routes.SumInsuredCheckRequest(
        sum_insured=sum_insured,
        city_tier=ctx.text("city_tier"),
        family_members=[analysis_routes.FamilyMember(age=a) for a in ctx.ages()],
    )
    result, error = await guarded(ctx, label, lambda: analysis_routes.sum_insured_check_route(body=request, current_user=ctx.user))
    if error:
        return error
    lines = [str(result.get("headline"))] if result.get("headline") else []
    if result.get("recommended_minimum"):
        lines.append(f"A rough minimum for your profile: {inr(result['recommended_minimum'])}.")
    return ok(label, lines, {
        "sum_insured": sum_insured,
        "recommended_minimum": result.get("recommended_minimum"),
        "verdict": result.get("verdict"),
    })


def _appeal_type(ctx: Ctx) -> str:
    stated = ctx.text("appeal_type")
    if stated:
        return stated
    lowered = ctx.message.lower()
    if "ombudsman" in lowered:
        return "ombudsman"
    if any(word in lowered for word in ("consumer", "jagriti", "commission", "court")):
        return "consumer_court"
    if "bima bharosa" in lowered:
        return "bima_bharosa"
    if "escalat" in lowered:
        return "insurer_escalation"
    audited = ctx.results.get("audit_rejection") or {}
    return (audited.get("data") or {}).get("recommended_appeal_type") or "gro"


APPEAL_LABELS = {
    "gro": "grievance officer",
    "insurer_escalation": "insurer escalation",
    "ombudsman": "Insurance Ombudsman",
    "bima_bharosa": "Bima Bharosa",
    "consumer_court": "consumer commission",
}


async def run_draft_appeal(ctx: Ctx) -> dict:
    label = INTENT_LABELS["draft_appeal"]
    if not ctx.claim_id:
        return need(label, "To draft a letter I first need to review your rejection. Please attach the rejection letter.",
                    [doc_field("rejection_letter", "The rejection or repudiation letter from your insurer")])
    appeal_type = _appeal_type(ctx)
    request = appeals_routes.AppealGenerateRequest(
        claim_id=ctx.claim_id,
        appeal_type=AppealType(appeal_type),
        additional_context=ctx.message[:1200] or None,
    )
    result, error = await guarded(ctx, label, lambda: appeals_routes.generate_appeal(req=request, db=ctx.db, current_user=ctx.user))
    if error:
        return error
    kind = APPEAL_LABELS.get(appeal_type, appeal_type)
    lines = [f"I drafted a letter addressed to the {kind}. Read every line, fill in any blanks, and verify the citations before you send it."]
    return ok(label, lines, {
        "appeal_id": result.get("appeal_id"),
        "appeal_type": appeal_type,
        "letter": result.get("letter"),
    }, [{"label": "Open in Appeals", "href": f"/dashboard/appeals?claim_id={ctx.claim_id}"}])


async def run_cost_benefit(ctx: Ctx) -> dict:
    label = INTENT_LABELS["cost_benefit"]
    if not ctx.claim_id:
        return need(label, "I need to review your rejection first. Please attach the rejection letter.",
                    [doc_field("rejection_letter", "The rejection or repudiation letter from your insurer")])
    amount = ctx.num("claim_amount")
    if amount:
        claim = await ctx.db.get(Claim, ctx.claim_id)
        if claim is not None and not claim.claim_amount:
            claim.claim_amount = amount
            await ctx.db.flush()
    request = analysis_routes.CostBenefitRequest(claim_id=ctx.claim_id)
    result, error = await guarded(ctx, label, lambda: analysis_routes.cost_benefit_route(body=request, db=ctx.db, current_user=ctx.user))
    if error:
        if error.get("status") == "unavailable" and "claim amount" in error.get("message", "").lower():
            return need(label, "What was the amount of the claim?", [value_field("claim_amount", "Claim amount", "for example 185000")])
        return error
    lines = [str(result.get("headline"))] if result.get("headline") else []
    if result.get("reasoning"):
        lines.append(str(result["reasoning"]))
    return ok(label, lines, {
        "verdict": result.get("verdict"),
        "factors": result.get("factors"),
        "recommended_route": result.get("recommended_route_label"),
    })


async def run_followup_letter(ctx: Ctx) -> dict:
    label = INTENT_LABELS["followup_letter"]
    if not ctx.claim_id:
        return need(label, "I need a reviewed claim to base the reminder on. Please attach the rejection letter.",
                    [doc_field("rejection_letter", "The rejection or repudiation letter from your insurer")])
    request = analysis_routes.FollowUpRequest(claim_id=ctx.claim_id, deadline_type="gro")
    result, error = await guarded(ctx, label, lambda: analysis_routes.generate_followup_route(body=request, db=ctx.db, current_user=ctx.user))
    if error:
        return error
    result = analysis_routes._make_json_serializable(result)
    letter = result.get("letter") or result.get("body") or result.get("letter_content")
    return ok(label, ["I prepared a reminder letter for your insurer's overdue grievance response."], {"letter": letter, "raw": None if letter else result})


async def run_precedents(ctx: Ctx) -> dict:
    label = INTENT_LABELS["precedents"]
    category = ctx.text("insurance_type") or "health"
    if ctx.claim_id is None:
        rejection = ctx.first("rejection_letter", "settlement_letter", "preauth_denial")
        if rejection is not None:
            category = _insurance_type(ctx, rejection).value
    request = analysis_routes.PrecedentMatchRequest(
        claim_id=ctx.claim_id,
        rejection_category=None if ctx.claim_id else category,
        fact_pattern=ctx.text("fact_pattern") or (ctx.message[:600] if ctx.message else None),
    )
    result, error = await guarded(ctx, label, lambda: analysis_routes.match_precedents_route(body=request, db=ctx.db, current_user=ctx.user))
    if error:
        return error
    matches = [m for m in (result.get("precedents") or []) if isinstance(m, dict)]
    if not matches:
        return ok(label, ["I did not find a close match in the curated precedent library."], {"precedents": []})
    lines = [f"{len(matches)} similar precedent pattern(s) found."]
    for match in matches[:3]:
        lines.append(f"{match.get('case_name')} ({match.get('court')}): {match.get('summary')}")
    lines.append("These are illustrative summaries. Verify each citation against the primary source before relying on it.")
    return ok(label, lines, {
        "precedents": [{"case_name": m.get("case_name"), "court": m.get("court"), "summary": m.get("summary"), "how_to_use": m.get("how_to_use")} for m in matches[:5]],
    })


async def run_ejagriti_guide(ctx: Ctx) -> dict:
    label = INTENT_LABELS["ejagriti_guide"]
    result, error = await guarded(ctx, label, lambda: analysis_routes.ejagriti_guide())
    if error:
        return error
    steps = [s for s in (result.get("steps") or []) if isinstance(s, dict)]
    lines = [str(result["when_to_use"])] if result.get("when_to_use") else []
    if result.get("legal_basis"):
        lines.append(f"Legal basis: {result['legal_basis']}")
    premium = ctx.num("premium_paid")
    if premium is not None:
        info = describe_consumer_fee(premium)
        fee_text = inr(info["fee"]) if info["fee"] else "nil"
        lines.append(f"With a premium of {inr(premium)}, the complaint belongs before the {info['forum']} and the court fee is {fee_text}.")
    else:
        lines.append(
            "The forum and the court fee depend on the value paid as consideration, which for an insurance policy is generally the premium paid, "
            "not the claim amount. For a premium up to Rs. 5 lakh the District Commission hears the complaint and there is no court fee. "
            "Tell me the premium you paid and I can work out the exact fee."
        )
    return ok(label, lines, {
        "portal": result.get("portal"),
        "fee_slabs": result.get("fee_slabs"),
        "steps": [{"step": s.get("step"), "action": s.get("action"), "detail": s.get("detail")} for s in steps[:10]],
    })


async def run_ombudsman_contact(ctx: Ctx) -> dict:
    label = INTENT_LABELS["ombudsman_contact"]
    query = " ".join(x for x in [ctx.text("state"), ctx.message] if x)
    found = find_offices(query)
    offices = found["offices"]
    if not offices:
        return need(label, "Which state, union territory or city are you in? The Ombudsman office depends on where you live.",
                    [value_field("state", "Your state, union territory or city", "for example Gujarat")])

    place = found["matched"][0] if found["matched"] else "your area"
    lines = [f"Here are the Insurance Ombudsman details for {place}:"]
    cards = []
    for office in offices:
        if len(offices) > 1:
            lines.append(f"**{office['center']} office**")
        lines.append(f"- Office: Insurance Ombudsman, {office['center']}")
        lines.append(f"- Address: {office['address']}")
        if office.get("phone"):
            lines.append(f"- Phone: {office['phone']}")
        lines.append(f"- Email: {office['email']}")
        lines.append(f"- Covers: {', '.join(office['statesCovered'])}")
        cards.append(office)
    for note in found["notes"][:2]:
        lines.append(note)
    lines.append(
        "Please confirm these details on cioins.co.in before you file, because offices and jurisdictions are occasionally revised. "
        "You can also use the [Ombudsman finder](/dashboard/ombudsman-finder) in this app."
    )
    lines.append("If you would like, I can draft your complaint letter to this office.")

    return ok(label, [], {"answer": "\n".join(lines), "offices": cards}, [{"label": "Open Ombudsman finder", "href": "/dashboard/ombudsman-finder"}])


GROUNDED_SYSTEM = (
    "You are RedoClaim's assistant for Indian insurance policyholders. Answer ONLY from the SOURCES provided. "
    "Do not use outside knowledge for facts. Never state a number (days, hours, weeks, months, years, percentages, rupee amounts), "
    "a fee, a regulation, section, rule, clause or paragraph number, a web address, a portal name, or a feature or page of this app "
    "unless it appears in the SOURCES. If the question needs something the SOURCES do not contain, say plainly that you do not have a "
    "verified answer for that part and point to the official sources: irdai.gov.in, bimabharosa.irdai.gov.in, cioins.co.in, or a licensed advocate. "
    "You may explain general ideas in plain words without numbers. This is not legal advice. "
    "Format: plain text, short paragraphs, '- ' for list items, no tables, no emojis, under about 200 words. "
    "The user may write in any language; answer in English."
)


async def _claim_context(ctx: Ctx) -> str:
    if not ctx.claim_id:
        return ""
    try:
        claim = await ctx.db.get(Claim, ctx.claim_id)
    except Exception:
        return ""
    if claim is None:
        return ""
    parts = []
    for label, attr in (
        ("Insurer", "insurer_name"), ("Policy number", "policy_number"), ("Claim amount", "claim_amount"),
        ("Status", "status"), ("Claim date", "claim_date"), ("Rejection date", "rejection_date"),
        ("Insurer response deadline", "gro_deadline"),
    ):
        value = getattr(claim, attr, None)
        if value not in (None, ""):
            parts.append(f"{label}: {getattr(value, 'value', value)}")
    return "; ".join(parts)


def _facts_fallback(facts: list, question: str = "") -> str:
    wants_pages = bool(re.search(r"\bpages?\b|\bfeatures?\b|redoclaim have|which tools|what tools", question or "", re.I))
    chosen = [f for f in facts if wants_pages or f["id"] != "app_pages"]
    if wants_pages:
        chosen.sort(key=lambda f: f["id"] != "app_pages")
    chosen = chosen[:2]
    return "\n\n".join(f"- {f['title']}: {f['text']}" for f in chosen)


async def run_general_question(ctx: Ctx) -> dict:
    label = INTENT_LABELS["general_question"]
    history = [m for m in ctx.history[-6:] if isinstance(m, dict)]
    history_all = " ".join(str(m.get("content", "")) for m in history)
    history_user = " ".join(str(m.get("content", "")) for m in history if m.get("role") == "user")
    facts = retrieve_facts(ctx.message, history_all)
    facts_block = facts_text(facts)
    rag_block = ""
    try:
        rag_block = (await asyncio.wait_for(search_irdai_regulations(ctx.message), timeout=10)) or ""
    except Exception as exc:
        logger.info(f"Knowledge-base search skipped: {exc}")
    rag_block = rag_block[:3500]
    claim_block = await _claim_context(ctx)
    recent = "\n".join(f"{m.get('role')}: {str(m.get('content', ''))[:300]}" for m in history[-4:])
    prompt = (
        f"SOURCES\nVERIFIED FACTS:\n{facts_block}\n\nKNOWLEDGE BASE EXTRACTS:\n{rag_block or 'none'}\n\n"
        f"CLAIM DETAILS: {claim_block or 'none'}\n\nRECENT CONVERSATION:\n{recent or 'none'}\n\nQUESTION: {ctx.message}"
    )
    fallback = _facts_fallback(facts, ctx.message)
    try:
        from app.services.llm.gemini_service import gemini
        raw = await gemini.generate(model="gpt-5-nano", prompt=prompt, system=GROUNDED_SYSTEM, temperature=0.1, max_tokens=700)
    except Exception as exc:
        logger.warning(f"General answer model call failed: {exc}")
        if fallback:
            text = "I could not reach the AI service just now, but here is verified information that may help.\n\n" + fallback
        else:
            text = (
                "I could not reach the AI service just now, and I do not have a verified answer ready for that question. "
                "Please try again in a moment, or check irdai.gov.in."
            )
        return ok(label, [], {"answer": text})
    allowed = "\n".join([facts_block, rag_block, claim_block, ctx.message, history_user])
    checked = check_answer(raw or "", allowed, fallback, ctx.message + " " + history_user)
    return ok(label, [], {"answer": checked["answer"], "guard": {"dropped": checked["dropped"], "fallback": checked["fallback"]}})


async def run_verify_response(ctx: Ctx) -> dict:
    label = INTENT_LABELS["verify_response"]
    lines = [
        "Here is how to check whether your insurer has missed its grievance deadline:",
        "- Find the date your grievance was registered. The insurer's acknowledgement (an email, SMS, portal ticket number or letter) should show it; the insurer must acknowledge a grievance immediately.",
        "- Count 14 days from that date. Within that time the insurer must resolve the grievance and send a final letter of resolution. It may ask you for further details only once, within the first week.",
        "- Look for that final letter. If it does not accept your complaint it must give reasons with reference to the specific policy terms, and it must include the contact details of the Insurance Ombudsman.",
        "- Check the status on Bima Bharosa (bimabharosa.irdai.gov.in). Insurers must keep their grievance systems synchronised with it and record grievances received by phone, email, post or in person.",
        "- In RedoClaim, the [Timeline](/dashboard/timeline) page shows the insurer's response deadline for your claims.",
    ]
    claim_line = ""
    if ctx.claim_id:
        try:
            claim = await ctx.db.get(Claim, ctx.claim_id)
            deadline = getattr(claim, "gro_deadline", None) if claim is not None else None
            if deadline:
                claim_line = f"For your claim, the recorded insurer response deadline is {str(deadline)[:10]}."
        except Exception:
            claim_line = ""
    if claim_line:
        lines.append(claim_line)
    lines.append(
        "If 14 days have passed with no final resolution letter, you can escalate: the Insurance Ombudsman (for claims up to Rs. 50 lakh; see the "
        "[Ombudsman finder](/dashboard/ombudsman-finder)) or a consumer commission complaint (see the [e-Jagriti guide](/dashboard/e-jagriti))."
    )
    return ok(label, [], {"answer": "\n".join(lines)}, [{"label": "Open Timeline", "href": "/dashboard/timeline"}])


EXECUTORS = {
    "audit_rejection": run_audit_rejection,
    "analyze_policy": run_analyze_policy,
    "scan_cis": run_scan_cis,
    "audit_settlement": run_audit_settlement,
    "preauth_check": run_preauth_check,
    "estimate_payout": run_estimate_payout,
    "waiting_period": run_waiting_period,
    "compare_policies": run_compare_policies,
    "renewal_check": run_renewal_check,
    "copay_breakdown": run_copay_breakdown,
    "portability": run_portability,
    "explain_term": run_explain_term,
    "ncb_check": run_ncb_check,
    "sum_insured_check": run_sum_insured_check,
    "draft_appeal": run_draft_appeal,
    "cost_benefit": run_cost_benefit,
    "followup_letter": run_followup_letter,
    "precedents": run_precedents,
    "ejagriti_guide": run_ejagriti_guide,
    "ombudsman_contact": run_ombudsman_contact,
    "verify_response": run_verify_response,
    "general_question": run_general_question,
}
