import json
import time
import logging
import httpx
from datetime import datetime
from groq import AsyncGroq
from app.core.config import settings

logger = logging.getLogger(__name__)

_MODEL_MAP = {
    "gemini-2.0-flash-lite":         "llama-3.1-8b-instant",
    "gemini-2.5-flash-lite":         "llama-3.1-8b-instant",
    "gemini-2.5-flash":              "llama-3.3-70b-versatile",
    "gemini-2.0-flash":              "llama-3.3-70b-versatile",
    "llama-3.3-70b-versatile":       "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant":          "llama-3.1-8b-instant",
    "llama4-scout-17b-16e-instruct": "llama4-scout-17b-16e-instruct",
}

def _resolve_model(model: str) -> str:
    return _MODEL_MAP.get(model, "llama-3.3-70b-versatile")


class GroqClient:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.05,
        max_tokens: int = 4096,
    ) -> str:
        groq_model = _resolve_model(model)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            completion = await self.client.chat.completions.create(
                model=groq_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise RuntimeError(f"Groq API error: {e}")

    async def embed(self, text: str) -> list[float]:
        """
        Embeddings via Jina AI (free tier, 1M tokens free, works in India).
        Falls back gracefully if key unavailable — RAG skipped, hardcoded context used.
        Model: jina-embeddings-v2-base-en (768-dim, matches Qdrant collection config).
        Sign up free at jina.ai — set JINA_API_KEY in Render env vars.
        """
        jina_key = getattr(settings, "JINA_API_KEY", "")
        if not jina_key:
            logger.warning("No JINA_API_KEY set — embeddings unavailable, skipping RAG")
            return []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.jina.ai/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {jina_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "jina-embeddings-v2-base-en",
                        "input": [text],
                    },
                )
                resp.raise_for_status()
                return resp.json()["data"][0]["embedding"]
        except Exception as e:
            logger.warning(f"Embedding failed: {e} — RAG context will be skipped")
            return []


# Singleton
gemini = GroqClient()


# ── 1. Policy Clause Extractor ────────────────────────────────────
async def extract_policy_clauses(policy_text: str) -> dict:
    system = (
        "You are an AI research assistant that extracts Indian insurance policy clauses. "
        "You are NOT a legal expert. Extractions may be incomplete for scanned documents. "
        "Return ONLY a valid JSON object. "
        "CRITICAL: Output MUST start with { and end with }. "
        "No markdown fences, no preamble, no explanation, no text after the closing brace."
    )

    prompt = f"""Analyze this Indian insurance policy document and extract ALL clauses.

DOCUMENT TEXT:
{policy_text[:7000]}

IMPORTANT FOR CO-PAYMENT: Extract BOTH the percentage AND the exact age/condition it applies to.
Example: if policy says "20% for age 60 and above, NIL for below 60", extract both parts.

Return ONLY this JSON structure. Start your response with {{ and end with }}. Nothing else:
{{
  "document_type": "policy|cis|rejection_letter|other",
  "policy_type": "health|motor|life|other",
  "insurer_name": "...",
  "policy_number": "...",
  "sum_insured": "...",
  "inception_date": "YYYY-MM-DD or null",
  "renewal_date": "YYYY-MM-DD or null",
  "is_cis": false,
  "waiting_periods": [
    {{"condition": "...", "duration": "...", "risk_level": "high|medium|low"}}
  ],
  "exclusions": [
    {{"clause": "...", "description": "...", "risk_level": "high|medium|low"}}
  ],
  "inclusions": [
    {{"benefit": "...", "limit": "...", "note": "..."}}
  ],
  "sub_limits": [
    {{"item": "...", "limit": "...", "note": "..."}}
  ],
  "room_rent_cap": {{"limit": "...", "type": "per_day|percentage|none", "note": "..."}},
  "co_payment": {{
    "percentage": "exact percentage e.g. 20% or NIL",
    "applies_to": "exact age/condition e.g. applicable only if insured age >= 60 years, NIL for age below 60",
    "conditions": "full condition text copied from policy",
    "note": "any additional note e.g. does not apply to accidents"
  }},
  "pre_existing_disease_waiting": "...",
  "moratorium_period": "5 years per IRDAI Health Regulations 2024",
  "claim_restrictions": ["..."],
  "network_hospitals": "cashless|reimbursement|both",
  "portability_allowed": true,
  "cis_inclusions_summary": null,
  "cis_exclusions_summary": null,
  "risky_clauses": [
    {{
      "clause": "...",
      "why_risky": "...",
      "irdai_reference": "IRDAI Master Circular 2024, Para X or Regulation Y"
    }}
  ],
  "plain_english_summary": "3-4 sentence summary a non-expert can understand"
}}"""

    start = time.time()
    raw = await gemini.generate(
        model=settings.MODEL_EXTRACTION,
        prompt=prompt,
        system=system,
        temperature=0.05,
        max_tokens=3500,
    )
    ms = int((time.time() - start) * 1000)
    logger.info(f"Policy extraction: {ms}ms")
    return _parse_json(raw, "policy_extraction")


# ── 2. CIS Analyzer ───────────────────────────────────────────────
async def analyze_cis(cis_text: str) -> dict:
    system = (
        "You are an AI assistant that extracts information from Indian insurance Customer "
        "Information Sheets (CIS). Output is AI-generated and may contain errors. "
        "Return ONLY a valid JSON object. "
        "CRITICAL: Output MUST start with { and end with }. No markdown, no extra text."
    )

    prompt = f"""This is a Customer Information Sheet (CIS) from an Indian insurer.
Extract all inclusions and exclusions clearly.

CIS TEXT:
{cis_text[:6000]}

Return ONLY this JSON. Start with {{ end with }}:
{{
  "insurer_name": "...",
  "policy_name": "...",
  "sum_insured": "...",
  "inclusions": [
    {{"benefit": "...", "coverage_limit": "...", "conditions": "..."}}
  ],
  "exclusions": [
    {{"exclusion": "...", "scope": "...", "irdai_permissible": true}}
  ],
  "waiting_periods": [
    {{"type": "...", "duration": "...", "applies_to": "..."}}
  ],
  "sub_limits": [
    {{"item": "...", "limit": "...", "note": "..."}}
  ],
  "co_payment": "...",
  "room_rent_limit": "...",
  "key_conditions": ["..."],
  "plain_english_inclusions": "What IS covered, in simple terms",
  "plain_english_exclusions": "What is NOT covered, in simple terms",
  "risky_exclusions": [
    {{
      "exclusion": "...",
      "risk": "...",
      "irdai_note": "Is this exclusion permissible under IRDAI regulations?"
    }}
  ]
}}"""

    raw = await gemini.generate(
        model=settings.MODEL_EXTRACTION,
        prompt=prompt,
        system=system,
        temperature=0.05,
        max_tokens=3000,
    )
    return _parse_json(raw, "cis_analysis")


# ── 3. Rejection Auditor — Hierarchy of Evidence ─────────────────
async def audit_rejection(
    rejection_text: str,
    policy_clauses: dict,
    irdai_context: str,
    rejection_patterns: str = "",
) -> dict:
    system = (
        "You are an AI legal research assistant helping Indian insurance policyholders "
        "understand their rights under IRDAI regulations. You are NOT a lawyer. "
        "Your output is NOT legal advice. "
        "You reference IRDAI Master Circular 2024, IRDAI Health Regs 2024, "
        "Insurance Ombudsman Rules 2017, Consumer Protection Act 2019. "
        "You STRICTLY follow the Hierarchy of Evidence: "
        "Step 1: SLA violations. Step 2: IRDAI regulatory violations. Step 3: Redressal route. "
        "CRITICAL: Return ONLY a valid JSON object. "
        "Output MUST start with { and end with }. "
        "No markdown fences, no preamble, no text before { or after }."
    )

    prompt = f"""CLAIM REJECTION AUDIT — Follow the Hierarchy of Evidence strictly.

REJECTION LETTER TEXT:
{rejection_text[:3500]}

POLICY CLAUSES ON RECORD:
{json.dumps(policy_clauses, indent=2)[:2000] if policy_clauses else "Not provided"}

IRDAI REGULATIONS (from RAG knowledge base):
{irdai_context[:2500]}

KNOWN REJECTION PATTERNS:
{rejection_patterns[:800] if rejection_patterns else "Not available"}

Return ONLY this JSON object. Start with {{ and end with }}. Nothing before or after:
{{
  "rejection_reason_category": "pre_existing_disease|waiting_period|exclusion|documentation|cashless_denial|fraud|procedure_not_covered|sub_limit|other",
  "rejection_reason_summary": "1-2 sentence summary of what insurer claims",
  "is_valid_rejection": false,
  "confidence": "high|medium|low",

  "step1_sla_analysis": {{
    "tat_violated": false,
    "violations": [
      {{"type": "...", "regulation": "IRDAI Master Circular 2024, Para X.Y", "detail": "..."}}
    ],
    "interest_applicable": false
  }},

  "step2_regulatory_violations": [
    {{
      "violation": "Specific description of what was violated",
      "regulation": "Exact citation e.g. IRDAI Master Circular 2024, Para 8.3",
      "severity": "high|medium|low",
      "argument": "How to use this in an appeal"
    }}
  ],

  "deficiency_in_service": false,
  "deficiency_grounds": ["..."],
  "deficiency_statement": "Formal legal statement using CPA 2019 Section 2(11) language",

  "product_liability_applicable": false,
  "product_liability_note": "...",

  "moratorium_applies": false,
  "moratorium_note": "...",

  "cis_violation": false,
  "cis_violation_note": "...",

  "document_demand_violation": false,
  "document_demand_note": "...",

  "step3_redressal": {{
    "recommended_action": "gro_appeal|ombudsman|consumer_court|accept",
    "ombudsman_eligible": true,
    "edaakhil_applicable": true,
    "reasoning": "Why this route is recommended"
  }},

  "strength_of_case": "strong|moderate|weak",
  "strength_reasoning": "...",
  "key_arguments": ["Argument 1", "Argument 2"],
  "evidence_needed": ["Document 1", "Document 2"],
  "interest_demand": null
}}"""

    start = time.time()
    raw = await gemini.generate(
        model=settings.MODEL_LEGAL,
        prompt=prompt,
        system=system,
        temperature=0.05,
        max_tokens=3500,
    )
    ms = int((time.time() - start) * 1000)
    logger.info(f"Rejection audit: {ms}ms")
    return _parse_json(raw, "rejection_audit")


# ── 4. Appeal Letter Generator ────────────────────────────────────
async def generate_appeal_letter(
    appeal_type: str,
    claim_data: dict,
    audit_report: dict,
    policy_clauses: dict,
    user_name: str,
    policy_number: str,
    insurer_name: str,
) -> str:
    insurance_type = claim_data.get("insurance_type", "health")
    if hasattr(insurance_type, "value"):
        insurance_type = insurance_type.value

    # Today's date for the letter header
    today = datetime.now().strftime("%d %B %Y")

    type_context = {
        "health": (
            "References: IRDAI (Health Insurance) Regulations 2024, IRDAI Master Circular 2024. "
            "Cite moratorium under Regulation 8(6) if applicable. "
            "Reference CIS disclosures, cashless rights, and PED waiting period rules."
        ),
        "motor": (
            "References: IRDAI Motor Insurance Guidelines 2017, "
            "IRDAI (Surveyors and Loss Assessors) Regulations 2015, Motor Vehicles Act 1988. "
            "For OD claims: cite surveyor TAT violations, IDV disputes, depreciation schedule. "
            "For driving licence grounds: cite Swaran Singh (2004) SC principle. "
            "Demand the full Survey Report and Surveyor's certificate under Reg 19."
        ),
        "life": (
            "References: IRDAI (Life Insurance) Regulations 2023, Insurance Act 1938 Section 45, "
            "IRDAI Master Circular 2024. "
            "Cite incontestability (Reg 27) if policy is 3+ years old. "
            "For non-disclosure: demand insurer prove fraudulent intent, not mere omission. "
            "For suicide clause: cite IRDAI mandated minimum payout after 1 year. "
            "Nominee has right to full claim documentation under IRDAI Regulations."
        ),
    }.get(insurance_type, "")

    system = (
        f"You are an AI writing assistant that drafts Indian insurance appeal letters "
        f"based on IRDAI regulations. You are NOT a lawyer. These are AI-generated DRAFTS "
        f"the user must verify before sending. "
        f"Use the EXACT legal term 'Deficiency in Service' (CPA 2019 Section 2(11)). "
        f"Cite specific IRDAI regulations with paragraph numbers. "
        f"Follow correct Indian legal letter format. "
        f"Insurance type: {insurance_type.upper()}. {type_context}"
    )

    appeal_descriptions = {
        "gro": {
            "to": "The Grievance Redressal Officer (GRO)",
            "org": f"{insurer_name}",
            "context": (
                "First formal escalation. Cite IRDAI Master Circular 2024 TATs. "
                "Demand resolution within 15 days. Warn of Ombudsman escalation. "
                "If TAT violated, demand interest under Para 7.4."
            ),
        },
        "insurer_escalation": {
            "to": "The Chief Executive Officer / Chairman & Managing Director",
            "org": f"{insurer_name}",
            "context": (
                "Direct CEO escalation. Use strong language about regulatory violations. "
                "Mention potential IRDAI complaint and Ombudsman filing. "
                "Reference Deficiency in Service under Consumer Protection Act 2019."
            ),
        },
        "ombudsman": {
            "to": "The Insurance Ombudsman",
            "org": "Office of the Insurance Ombudsman",
            "context": (
                "Formal Ombudsman complaint under Insurance Ombudsman Rules 2017. "
                "State GRO was filed and unresolved. Cite all IRDAI violations. "
                "Claim full amount + interest + costs up to Rs.5,000. "
                "Reference Deficiency in Service under CPA 2019 S.2(11)."
            ),
        },
        "bima_bharosa": {
            "to": "The Grievance Cell",
            "org": "IRDAI — Bima Bharosa Portal (igms.irda.gov.in)",
            "context": (
                "IRDAI portal complaint. Concise, factual, regulatory-focused. "
                "List every IRDAI regulation violated with paragraph numbers. "
                "Request IRDAI intervention and insurer show-cause notice."
            ),
        },
        "consumer_court": {
            "to": "The Hon'ble President",
            "org": "District Consumer Disputes Redressal Commission",
            "context": (
                "Formal Consumer Court complaint. Lead with Deficiency in Service under "
                "CPA 2019 Section 2(11). Reference E-Daakhil filing. "
                "Claim full amount + interest (9-12% p.a.) + mental agony compensation "
                "+ litigation costs + punitive damages if warranted. "
                "Mention Product Liability (CPA 2019 S.2(34)) if policy was mis-sold."
            ),
        },
    }

    desc = appeal_descriptions.get(appeal_type, appeal_descriptions["gro"])
    violations = audit_report.get("step2_regulatory_violations", [])
    sla = audit_report.get("step1_sla_analysis", {})
    deficiency = audit_report.get("deficiency_statement", "")
    key_args = audit_report.get("key_arguments", [])
    interest_demand = audit_report.get("interest_demand", "")

    # Format rejection date nicely if available
    rejection_date_raw = claim_data.get("rejection_date", "")
    if rejection_date_raw and rejection_date_raw != "[DATE]":
        try:
            rd = datetime.fromisoformat(str(rejection_date_raw).replace("Z", ""))
            rejection_date_display = rd.strftime("%d %B %Y")
        except Exception:
            rejection_date_display = str(rejection_date_raw)
    else:
        rejection_date_display = "as per rejection letter"

    prompt = f"""Draft a {appeal_type.upper().replace("_", " ")} letter.

TO: {desc["to"]}
ORGANISATION: {desc["org"]}
LETTER CONTEXT: {desc["context"]}

CLAIMANT DETAILS:
Name: {user_name}
Policy Number: {policy_number}
Insurer: {insurer_name}
Claim Amount: Rs.{claim_data.get("claim_amount", "as per claim")}
Insurance Type: {claim_data.get("insurance_type", "Health")}
Rejection Date: {rejection_date_display}
Today's Date: {today}

IRDAI VIOLATIONS FOUND:
{json.dumps(violations, indent=2)[:1500] if violations else "See SLA violations below"}

SLA VIOLATIONS:
{json.dumps(sla, indent=2)[:800] if sla else "None detected"}

DEFICIENCY IN SERVICE STATEMENT:
{deficiency[:500] if deficiency else "Insurer has failed in its service obligations"}

KEY LEGAL ARGUMENTS:
{chr(10).join(f"- {a}" for a in key_args[:5])}

INTEREST DEMAND:
{interest_demand if interest_demand else "N/A"}

ADDITIONAL CONTEXT:
{claim_data.get("additional_context", "")}

Write the complete letter. Include:
1. Date line: {today}
2. Full address block to: {desc["to"]}, {desc["org"]}
3. Subject line referencing policy number and claim
4. Para 1: Facts of the case (policy, claim, rejection)
5. Para 2-4: Legal arguments with specific IRDAI citations
6. Para 5: Relief sought (specific amounts + interest if applicable)
7. Para 6: Consequence of non-compliance (next escalation step)
8. Closing: Yours faithfully, {user_name}

IMPORTANT: Use {today} as the date. Use {user_name} as the name.
Do NOT use placeholders like [DATE], [NAME], or [CONTACT DETAILS] anywhere in the letter.
Replace contact placeholders with: [Your Phone Number] and [Your Email Address] as reminders."""

    start = time.time()
    letter = await gemini.generate(
        model=settings.MODEL_DRAFTING,
        prompt=prompt,
        system=system,
        temperature=0.25,
        max_tokens=4000,
    )
    ms = int((time.time() - start) * 1000)
    logger.info(f"Appeal letter ({appeal_type}): {ms}ms")
    return letter


# ── 5. Portability Advisor ────────────────────────────────────────
async def generate_portability_guide(
    current_policy: dict,
    years_covered: float,
    reason_for_porting: str,
) -> str:
    system = (
        "You are an AI research assistant that helps users understand Indian health insurance "
        "portability rules under IRDAI Regulations 2024. Output is AI-generated research, "
        "NOT legal advice. Always recommend verifying with the insurer and consulting a "
        "licensed advisor for important decisions."
    )

    prompt = f"""Generate a detailed portability guide for this policyholder.

CURRENT POLICY:
{json.dumps(current_policy, indent=2)[:1500]}

Years of continuous coverage: {years_covered:.1f} years
Reason for wanting to port: {reason_for_porting}

Provide:
1. Whether portability is advisable given the situation
2. Waiting period credits they will carry forward
3. Moratorium status at new insurer
4. Step-by-step porting process (IRDAI Regulation 17)
5. Documents needed
6. How to choose a better insurer
7. What to watch out for at the new insurer
8. Timeline (apply 45 days before renewal)

Be specific, practical, and reference IRDAI (Health Insurance) Regulations 2024, Regulation 17."""

    return await gemini.generate(
        model=settings.MODEL_EXTRACTION,
        prompt=prompt,
        system=system,
        temperature=0.2,
        max_tokens=2000,
    )


# ── 6. Motor Insurance Audit ──────────────────────────────────────
async def audit_motor_rejection(
    rejection_text: str,
    policy_clauses: dict,
    irdai_context: str,
    motor_rules_analysis: dict,
) -> dict:
    system = (
        "You are an AI legal research assistant helping Indian motor insurance policyholders "
        "understand their rights. You are NOT a lawyer. Output is NOT legal advice. "
        "You reference IRDAI Motor Insurance Guidelines 2017, Motor Vehicles Act 1988, "
        "IRDAI Master Circular 2024, Insurance Ombudsman Rules 2017, CPA 2019. "
        "CRITICAL: Return ONLY a valid JSON object. "
        "Output MUST start with { and end with }. No markdown, no text outside the JSON."
    )

    prompt = f"""MOTOR INSURANCE CLAIM REJECTION AUDIT.

REJECTION LETTER TEXT:
{rejection_text[:3500]}

POLICY CLAUSES ON RECORD:
{json.dumps(policy_clauses, indent=2)[:2000] if policy_clauses else "Not provided"}

MOTOR-SPECIFIC RULES ANALYSIS:
{json.dumps(motor_rules_analysis, indent=2)[:1500]}

IRDAI REGULATIONS (from knowledge base):
{irdai_context[:2000]}

Return ONLY this JSON. Start with {{ end with }}:
{{
  "rejection_reason_category": "driving_licence|drunk_driving|policy_lapse|consequential_damage|depreciation_dispute|vehicle_use_violation|fraud|theft_conditions|other",
  "rejection_reason_summary": "1-2 sentence summary",
  "is_valid_rejection": false,
  "confidence": "high|medium|low",
  "step1_sla_analysis": {{
    "tat_violated": false,
    "violations": [{{"type": "...", "regulation": "...", "detail": "..."}}],
    "interest_applicable": false
  }},
  "step2_regulatory_violations": [
    {{
      "violation": "Specific description",
      "regulation": "Exact citation",
      "severity": "high|medium|low",
      "argument": "How to use this in an appeal",
      "case_law": "Relevant SC/NCDRC case if applicable"
    }}
  ],
  "surveyor_report_issues": {{
    "report_provided": false,
    "issues": ["..."],
    "demand_note": "What to demand from insurer regarding survey"
  }},
  "depreciation_applicable": false,
  "zero_dep_rider_check": "Does policy have zero depreciation rider? Check policy schedule.",
  "own_damage_vs_tp": "own_damage|third_party|both",
  "deficiency_in_service": false,
  "deficiency_grounds": ["..."],
  "deficiency_statement": "Formal legal statement using CPA 2019 Section 2(11) language",
  "step3_redressal": {{
    "recommended_action": "gro_appeal|ombudsman|consumer_court|accept",
    "ombudsman_eligible": true,
    "edaakhil_applicable": true,
    "reasoning": "Why this route is recommended"
  }},
  "strength_of_case": "strong|moderate|weak",
  "strength_reasoning": "...",
  "key_arguments": ["Argument 1", "Argument 2"],
  "evidence_needed": ["Document 1", "Document 2"],
  "interest_demand": null
}}"""

    start = time.time()
    raw = await gemini.generate(
        model=settings.MODEL_LEGAL,
        prompt=prompt,
        system=system,
        temperature=0.05,
        max_tokens=3500,
    )
    ms = int((time.time() - start) * 1000)
    logger.info(f"Motor rejection audit: {ms}ms")
    return _parse_json(raw, "motor_rejection_audit")


# ── 7. Life Insurance Audit ───────────────────────────────────────
async def audit_life_rejection(
    rejection_text: str,
    policy_clauses: dict,
    irdai_context: str,
    life_rules_analysis: dict,
    incontestability_check: dict,
) -> dict:
    system = (
        "You are an AI legal research assistant helping Indian life insurance claimants "
        "understand their rights under IRDAI regulations and Insurance Act 1938. "
        "You are NOT a lawyer. Output is NOT legal advice. "
        "You reference IRDAI Life Regs 2023, Insurance Act 1938 S.45, "
        "IRDAI Master Circular 2024, Ombudsman Rules 2017, CPA 2019. "
        "CRITICAL: Return ONLY a valid JSON object. "
        "Output MUST start with { and end with }. No markdown, no text outside the JSON."
    )

    prompt = f"""LIFE INSURANCE CLAIM REJECTION AUDIT.

REJECTION LETTER TEXT:
{rejection_text[:3500]}

POLICY CLAUSES ON RECORD:
{json.dumps(policy_clauses, indent=2)[:2000] if policy_clauses else "Not provided"}

INCONTESTABILITY CHECK:
{json.dumps(incontestability_check, indent=2)[:800]}

LIFE-SPECIFIC RULES ANALYSIS:
{json.dumps(life_rules_analysis, indent=2)[:1500]}

IRDAI REGULATIONS (from knowledge base):
{irdai_context[:2000]}

Return ONLY this JSON. Start with {{ end with }}:
{{
  "rejection_reason_category": "non_disclosure|suicide|policy_lapse|early_claim|nominee_dispute|accidental_death|fraud|other",
  "rejection_reason_summary": "1-2 sentence summary",
  "is_valid_rejection": false,
  "confidence": "high|medium|low",
  "step1_sla_analysis": {{
    "tat_violated": false,
    "violations": [{{"type": "...", "regulation": "...", "detail": "..."}}],
    "interest_applicable": false
  }},
  "incontestability": {{
    "applies": false,
    "years_active": 0,
    "argument": "...",
    "strength": "very_strong|strong|moderate|weak"
  }},
  "step2_regulatory_violations": [
    {{
      "violation": "Specific description",
      "regulation": "Exact citation e.g. IRDAI Life Regs 2023, Reg 27",
      "severity": "high|medium|low",
      "argument": "How to use in appeal"
    }}
  ],
  "section_45_insurance_act": {{
    "applicable": false,
    "argument": "Section 45 Insurance Act 1938 argument if applicable"
  }},
  "cause_of_death_relevance": {{
    "undisclosed_condition_related_to_death": false,
    "note": "If undisclosed condition is unrelated to cause of death, repudiation is weaker"
  }},
  "deficiency_in_service": false,
  "deficiency_grounds": ["..."],
  "deficiency_statement": "Formal legal statement using CPA 2019 Section 2(11) language",
  "step3_redressal": {{
    "recommended_action": "gro_appeal|ombudsman|consumer_court|accept",
    "ombudsman_eligible": true,
    "edaakhil_applicable": true,
    "reasoning": "Why this route is recommended"
  }},
  "strength_of_case": "strong|moderate|weak",
  "strength_reasoning": "...",
  "key_arguments": ["Argument 1", "Argument 2"],
  "evidence_needed": ["Document 1", "Document 2"],
  "interest_demand": null
}}"""

    start = time.time()
    raw = await gemini.generate(
        model=settings.MODEL_LEGAL,
        prompt=prompt,
        system=system,
        temperature=0.05,
        max_tokens=3500,
    )
    ms = int((time.time() - start) * 1000)
    logger.info(f"Life rejection audit: {ms}ms")
    return _parse_json(raw, "life_rejection_audit")


# ── 8. Motor/Life Policy Clause Extractor ────────────────────────
async def extract_motor_life_policy_clauses(policy_text: str, insurance_type: str) -> dict:
    system = (
        "You are an AI research assistant that extracts Indian insurance policy clauses. "
        "You are NOT a legal expert. "
        "Return ONLY a valid JSON object. "
        "CRITICAL: Output MUST start with { and end with }. No markdown, no extra text."
    )

    if insurance_type == "motor":
        schema = """{
  "document_type": "policy|rejection_letter|survey_report|other",
  "policy_type": "comprehensive|third_party|own_damage|two_wheeler",
  "insurer_name": "...",
  "policy_number": "...",
  "vehicle_registration": "...",
  "idv": "Insured Declared Value in INR",
  "inception_date": "YYYY-MM-DD or null",
  "expiry_date": "YYYY-MM-DD or null",
  "premium_paid": "...",
  "add_ons": [{"name": "Zero Depreciation|Engine Protect|NCB Protect", "active": true}],
  "exclusions": [{"clause": "...", "description": "...", "risk_level": "high|medium|low"}],
  "deductibles": {"compulsory": "...", "voluntary": "...", "note": "..."},
  "ncb_percentage": "No Claim Bonus percentage if applicable",
  "cashless_garages": "number or description",
  "risky_clauses": [{"clause": "...", "why_risky": "...", "irdai_reference": "..."}],
  "plain_english_summary": "3-4 sentence summary"
}"""
    else:
        schema = """{
  "document_type": "policy|rejection_letter|death_certificate|other",
  "policy_type": "term|endowment|ulip|whole_life|money_back",
  "insurer_name": "...",
  "policy_number": "...",
  "sum_assured": "...",
  "premium": "...",
  "policy_term": "...",
  "inception_date": "YYYY-MM-DD or null",
  "maturity_date": "YYYY-MM-DD or null",
  "nominee_name": "...",
  "nominee_relationship": "...",
  "is_active": true,
  "exclusions": [{"clause": "...", "description": "...", "risk_level": "high|medium|low"}],
  "riders": [{"name": "Accidental Death|Critical Illness|Waiver of Premium", "sum_assured": "..."}],
  "suicide_clause": "...",
  "revival_clause": "...",
  "incontestability_period": "3 years per IRDAI Life Regulations 2023",
  "risky_clauses": [{"clause": "...", "why_risky": "...", "irdai_reference": "..."}],
  "plain_english_summary": "3-4 sentence summary"
}"""

    prompt = f"""Analyze this Indian {insurance_type} insurance policy and extract ALL clauses.

DOCUMENT TEXT:
{policy_text[:7000]}

Return ONLY this JSON. Start with {{ end with }}:
{schema}"""

    start = time.time()
    raw = await gemini.generate(
        model=settings.MODEL_EXTRACTION,
        prompt=prompt,
        system=system,
        temperature=0.05,
        max_tokens=3500,
    )
    ms = int((time.time() - start) * 1000)
    logger.info(f"{insurance_type.capitalize()} policy extraction: {ms}ms")
    return _parse_json(raw, f"{insurance_type}_policy_extraction")


# ── 9. Embeddings ─────────────────────────────────────────────────
async def generate_embeddings(text: str) -> list[float]:
    """Embeddings via Jina AI (free tier, 768-dim, works in India)."""
    return await gemini.embed(text=text)


# ── Helpers ───────────────────────────────────────────────────────
def _parse_json(raw: str, context: str) -> dict:
    """
    Safely parse LLM JSON output.
    Handles markdown fences, leading/trailing text, and truncated responses.
    """
    try:
        clean = raw.strip()

        # Strip markdown fences
        for fence in ["```json", "```"]:
            if clean.startswith(fence):
                clean = clean[len(fence):]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()

        # If there's text before the JSON, find the first {
        brace_start = clean.find("{")
        if brace_start > 0:
            clean = clean[brace_start:]

        # If there's text after the JSON, find the last }
        brace_end = clean.rfind("}")
        if brace_end != -1 and brace_end < len(clean) - 1:
            clean = clean[:brace_end + 1]

        return json.loads(clean)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed in {context}: {e}")
        return {"raw_analysis": raw, "parse_error": True, "context": context}