"""
LLM Service — RedoClaim (Gemini API)
All inference via Google Gemini 2.0 Flash (free tier).

Model routing:
  gemini-2.0-flash-lite  → policy clause extraction, CIS analysis, classification (fast + cheap)
  gemini-2.0-flash       → legal reasoning, IRDAI audit (Hierarchy of Evidence)
  gemini-2.0-flash       → appeal letter drafting (GRO, Ombudsman, Consumer Court)
  text-embedding-004     → RAG embeddings (free, 768-dim)
"""
import json
import time
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.timeout = 120  # Gemini is fast; 2 min is plenty

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.05,
        max_tokens: int = 4096,
    ) -> str:
        contents = []
        if system:
            # Gemini uses "system_instruction" at the top level
            pass  # handled below via system_instruction field

        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system:
            payload["system_instruction"] = {"parts": [{"text": system}]}

        url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except httpx.HTTPStatusError as e:
                body = e.response.text
                logger.error(f"Gemini API error {e.response.status_code}: {body}")
                raise RuntimeError(f"Gemini API error: {e.response.status_code} — {body}")
            except httpx.ConnectError:
                raise RuntimeError(
                    "Cannot connect to Gemini API. Check your internet connection "
                    "and that GEMINI_API_KEY is set correctly."
                )

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings using text-embedding-004 (768-dim, free tier)."""
        url = (
            f"{GEMINI_API_BASE}/models/text-embedding-004:embedContent"
            f"?key={self.api_key}"
        )
        payload = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()["embedding"]["values"]


gemini = GeminiClient()


# ── 1. Policy Clause Extractor ────────────────────────────────────
async def extract_policy_clauses(policy_text: str) -> dict:
    """
    Extract ALL important clauses from a policy document.
    Also detects if the document is a CIS (Customer Information Sheet).
    Model: gemini-2.0-flash-lite — fast structured extraction.
    """
    system = """You are an AI research assistant that helps extract insurance policy clauses
from documents. You are NOT a legal expert. Your extractions may be incomplete or
contain errors, especially for scanned or poorly formatted documents. Extract key
clauses and return ONLY valid JSON with no markdown, no preamble."""

    prompt = f"""Analyze this Indian insurance policy document and extract ALL clauses.

DOCUMENT TEXT:
{policy_text[:7000]}

Return ONLY this JSON structure (no markdown, no explanation):
{{
  "document_type": "policy|cis|rejection_letter|other",
  "policy_type": "health|motor|life|other",
  "insurer_name": "...",
  "policy_number": "...",
  "sum_insured": "...",
  "inception_date": "YYYY-MM-DD or null",
  "renewal_date": "YYYY-MM-DD or null",
  "is_cis": true|false,
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
  "co_payment": {{"percentage": "...", "conditions": "...", "note": "..."}},
  "pre_existing_disease_waiting": "...",
  "moratorium_period": "5 years per IRDAI Health Regulations 2024",
  "claim_restrictions": ["..."],
  "network_hospitals": "cashless|reimbursement|both",
  "portability_allowed": true,
  "cis_inclusions_summary": "... (only if is_cis=true, else null)",
  "cis_exclusions_summary": "... (only if is_cis=true, else null)",
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
    """
    Dedicated Customer Information Sheet (CIS) analyzer.
    IRDAI Master Circular 2024, Para 4.2: Insurer must provide CIS with
    clear inclusions and exclusions.
    """
    system = """You are an AI assistant that extracts information from insurance Customer
Information Sheets (CIS). Your output is AI-generated and may contain errors.
Users should verify all extracted information against the original CIS document.
Extract CIS contents clearly and return ONLY valid JSON."""

    prompt = f"""This is a Customer Information Sheet (CIS) from an Indian insurer.
Extract all inclusions and exclusions clearly.

CIS TEXT:
{cis_text[:6000]}

Return ONLY this JSON:
{{
  "insurer_name": "...",
  "policy_name": "...",
  "sum_insured": "...",
  "inclusions": [
    {{"benefit": "...", "coverage_limit": "...", "conditions": "..."}}
  ],
  "exclusions": [
    {{"exclusion": "...", "scope": "...", "irdai_permissible": true|false}}
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
    """
    Full legal audit of a claim rejection.
    Strictly follows the Hierarchy of Evidence:
      Step 1: SLA violations
      Step 2: IRDAI Master Circular violations
      Step 3: Redressal route
    Model: gemini-2.0-flash — strong legal reasoning.
    """
    system = """You are an AI legal research assistant helping Indian insurance policyholders
understand their rights under IRDAI regulations. You are NOT a lawyer and your output
is NOT legal advice. You help users identify potential regulatory issues as a starting
point for their own research and for consulting a licensed advocate.

You reference:
- IRDAI Master Circular on Protection of Policyholders Interests (2024)
- IRDAI (Health Insurance) Regulations 2024
- Insurance Ombudsman Rules 2017
- Consumer Protection Act 2019

You STRICTLY follow the Hierarchy of Evidence:
Step 1: SLA violations (TAT breaches)
Step 2: IRDAI Master Circular regulatory violations
Step 3: Redressal route recommendation

Return ONLY valid JSON. Note: your output may contain errors — always verify citations.
Remind the user this is AI-generated research, not legal advice."""

    prompt = f"""CLAIM REJECTION AUDIT — Follow the Hierarchy of Evidence strictly.

REJECTION LETTER TEXT:
{rejection_text[:3500]}

POLICY CLAUSES ON RECORD:
{json.dumps(policy_clauses, indent=2)[:2000] if policy_clauses else "Not provided"}

IRDAI REGULATIONS (from RAG knowledge base):
{irdai_context[:2500]}

KNOWN REJECTION PATTERNS:
{rejection_patterns[:800] if rejection_patterns else "Not available"}

Perform a complete audit. Return ONLY valid JSON:
{{
  "rejection_reason_category": "pre_existing_disease|waiting_period|exclusion|documentation|cashless_denial|fraud|procedure_not_covered|sub_limit|other",
  "rejection_reason_summary": "1-2 sentence summary of what insurer claims",
  "is_valid_rejection": true|false,
  "confidence": "high|medium|low",

  "step1_sla_analysis": {{
    "tat_violated": true|false,
    "violations": [
      {{"type": "...", "regulation": "IRDAI Master Circular 2024, Para X.Y", "detail": "..."}}
    ],
    "interest_applicable": true|false
  }},

  "step2_regulatory_violations": [
    {{
      "violation": "Specific description of what was violated",
      "regulation": "Exact citation e.g. IRDAI Master Circular 2024, Para 8.3",
      "severity": "high|medium|low",
      "argument": "How to use this in an appeal"
    }}
  ],

  "deficiency_in_service": true|false,
  "deficiency_grounds": ["..."],
  "deficiency_statement": "Formal legal statement using CPA 2019 Section 2(11) language",

  "product_liability_applicable": true|false,
  "product_liability_note": "...",

  "moratorium_applies": true|false,
  "moratorium_note": "...",

  "cis_violation": true|false,
  "cis_violation_note": "...",

  "document_demand_violation": true|false,
  "document_demand_note": "...",

  "step3_redressal": {{
    "recommended_action": "gro_appeal|ombudsman|consumer_court|accept",
    "ombudsman_eligible": true|false,
    "edaakhil_applicable": true|false,
    "reasoning": "Why this route is recommended"
  }},

  "strength_of_case": "strong|moderate|weak",
  "strength_reasoning": "...",
  "key_arguments": ["Argument 1", "Argument 2", "..."],
  "evidence_needed": ["Document 1", "Document 2", "..."],
  "interest_demand": "Specify exact interest demand if TAT violated, else null"
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
    """
    Generate a professional legal appeal letter.
    Mandatorily uses:
    - "Deficiency in Service" (CPA 2019, S.2(11)) in relevant letters
    - Exact IRDAI regulation citations with paragraph numbers
    - E-Daakhil reference where appropriate
    - Interest demand where TAT is violated
    Model: gemini-2.0-flash — excellent formal legal drafting.
    """
    system = """You are an AI writing assistant that helps draft insurance appeal letters
based on IRDAI regulations. You are NOT a lawyer. These are AI-generated DRAFTS that
must be reviewed and corrected by the user before sending. The user is responsible for
verifying all facts, regulation citations, and legal arguments. Draft letters that:
- Use the EXACT legal term "Deficiency in Service" (Consumer Protection Act 2019, Section 2(11))
- Cite specific IRDAI regulations with paragraph numbers
- Reference Insurance Ombudsman Rules 2017 where applicable
- Include E-Daakhil portal reference when appropriate
- Demand interest on delayed claims citing IRDAI Master Circular 2024, Para 7.4
- Follow correct Indian legal letter format with proper salutation and closing"""

    appeal_descriptions = {
        "gro": {
            "to": "The Grievance Redressal Officer (GRO)",
            "org": f"{insurer_name}",
            "context": (
                "This is the first formal escalation. Cite IRDAI Master Circular 2024 TATs. "
                "Demand resolution within 15 days. Warn of Ombudsman escalation. "
                "If TAT was violated, demand interest under Para 7.4."
            ),
        },
        "insurer_escalation": {
            "to": "The Chief Executive Officer / Chairman & Managing Director",
            "org": f"{insurer_name}",
            "context": (
                "This is a direct CEO escalation. Use strong language about regulatory violations. "
                "Mention potential IRDAI complaint and Ombudsman filing. "
                "Reference Deficiency in Service under Consumer Protection Act 2019."
            ),
        },
        "ombudsman": {
            "to": "The Insurance Ombudsman",
            "org": "Office of the Insurance Ombudsman",
            "context": (
                "Formal Ombudsman complaint under Insurance Ombudsman Rules 2017. "
                "State GRO was filed and unresolved. Cite all IRDAI violations found. "
                "Claim full amount + interest + costs up to ₹5,000. "
                "Reference 'Deficiency in Service' under CPA 2019 S.2(11)."
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
                "Formal Consumer Court complaint. Lead with 'Deficiency in Service' under "
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

    prompt = f"""Draft a {appeal_type.upper().replace("_", " ")} letter.

TO: {desc["to"]}
ORGANISATION: {desc["org"]}
LETTER CONTEXT: {desc["context"]}

CLAIMANT DETAILS:
Name: {user_name}
Policy Number: {policy_number}
Insurer: {insurer_name}
Claim Amount: ₹{claim_data.get("claim_amount", "As per claim")}
Insurance Type: {claim_data.get("insurance_type", "Health")}
Rejection Date: {claim_data.get("rejection_date", "[DATE]")}

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
1. Date line: [DATE]
2. Full address block to: {desc["to"]}, {desc["org"]}
3. Subject line referencing policy number and claim
4. Para 1: Facts of the case (policy, claim, rejection)
5. Para 2-4: Legal arguments with specific IRDAI citations
6. Para 5: Relief sought (specific amounts + interest if applicable)
7. Para 6: Consequence of non-compliance (next escalation step)
8. Closing: Yours faithfully, [NAME], with date and contact placeholders

Use formal legal English. Be assertive but professional."""

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
    """
    Generate a step-by-step portability guide for the user.
    IRDAI Health Insurance Regulations 2024, Regulation 17.
    """
    system = """You are an AI research assistant that helps users understand Indian health
insurance portability rules based on IRDAI Regulations 2024. Your output is AI-generated
research guidance, NOT legal advice. Always recommend verifying with the insurer and
consulting a licensed advisor for important decisions."""

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


# ── 6. Embeddings ─────────────────────────────────────────────────
async def generate_embeddings(text: str) -> list[float]:
    """Embeddings via Gemini text-embedding-004 (768-dim, free tier)."""
    return await gemini.embed(text=text)


# ── Helpers ───────────────────────────────────────────────────────
def _parse_json(raw: str, context: str) -> dict:
    """Safely parse LLM JSON output."""
    try:
        clean = raw.strip()
        for prefix in ["```json", "```"]:
            if clean.startswith(prefix):
                clean = clean[len(prefix):]
        if clean.endswith("```"):
            clean = clean[:-3]
        return json.loads(clean.strip())
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed in {context}: {e}")
        return {"raw_analysis": raw, "parse_error": True, "context": context}
