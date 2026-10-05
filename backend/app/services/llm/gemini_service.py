"""
LLM service — despite the filename (kept for backward compatibility with
existing imports across the codebase; renaming it is a larger refactor than
this pass covers), this module is a provider-agnostic wrapper: Groq → Gemini → OpenAI fallback for chat. It used to
route between Gemini/Groq/Llama depending on task; that routing is gone —
everything now resolves to a single OpenAI model via _LEGACY_MODEL_ALIASES
below, kept only so old caller code that still passes a "gemini-..." or
"llama-..." string as `model` keeps working unchanged.

TODO(cleanup): rename this file to app/services/llm/openai_service.py (or
similar) and update the ~handful of `from app.services.llm.gemini_service
import ...` call sites accordingly, once there's a moment to do the
search-and-replace + test pass safely.
"""
import json
import time
import logging
from datetime import datetime
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

# Old task-specific model names from the pre-OpenAI-migration codebase.
# All of them now resolve to the same underlying model; this map exists
# purely so callers passing a legacy name don't need to change.
_LEGACY_MODEL_ALIASES = {
    "gemini-2.0-flash-lite":         "gpt-5-nano",
    "gemini-2.5-flash-lite":         "gpt-5-nano",
    "gemini-2.5-flash":              "gpt-5-nano",
    "gemini-2.0-flash":              "gpt-5-nano",
    "llama-3.3-70b-versatile":       "gpt-5-nano",
    "llama-3.1-8b-instant":          "gpt-5-nano",
    "llama4-scout-17b-16e-instruct": "gpt-5-nano",
    "gpt-5-nano":                    "gpt-5-nano",
}
# Backward-compatible alias for the old name, in case anything imports it directly.
_MODEL_MAP = _LEGACY_MODEL_ALIASES

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 768  # truncated via OpenAI's `dimensions` param — matches existing Qdrant collections


_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def _resolve_model(model: str) -> str:
    """Model for the OpenAI fallback provider (legacy names map to gpt-5-nano)."""
    return _MODEL_MAP.get(model, "gpt-5-nano")


class _Provider:
    def __init__(self, name: str, client: AsyncOpenAI, model: str | None):
        self.name = name
        self.client = client
        self.model = model  # None → resolve from the caller's legacy model name (OpenAI)


class OpenAIClientWrapper:
    """
    Provider-agnostic chat wrapper (class name kept for compatibility). Chat calls try Groq,
    then Gemini, then OpenAI — whichever are configured — and fall back to the next on any error.
    Embeddings use a single provider (Gemini preferred, else OpenAI) so vectors are never mixed.
    """

    def __init__(self):
        self.providers: list[_Provider] = []
        if getattr(settings, "GROQ_API_KEY", ""):
            self.providers.append(_Provider(
                "groq", AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url=_GROQ_BASE_URL), settings.GROQ_MODEL))
        if getattr(settings, "GEMINI_API_KEY", ""):
            self.providers.append(_Provider(
                "gemini", AsyncOpenAI(api_key=settings.GEMINI_API_KEY, base_url=_GEMINI_BASE_URL),
                settings.GEMINI_CHAT_MODEL))
        if getattr(settings, "OPENAI_API_KEY", ""):
            self.providers.append(_Provider("openai", AsyncOpenAI(api_key=settings.OPENAI_API_KEY), None))
        if not self.providers:
            logger.error("No LLM API key configured (GROQ_API_KEY / GEMINI_API_KEY / OPENAI_API_KEY)")

        # Embedding client: Gemini preferred, else OpenAI, else none.
        if getattr(settings, "GEMINI_API_KEY", ""):
            self.embed_provider = "gemini"
            self.embed_client = AsyncOpenAI(api_key=settings.GEMINI_API_KEY, base_url=_GEMINI_BASE_URL)
        elif getattr(settings, "OPENAI_API_KEY", ""):
            self.embed_provider = "openai"
            self.embed_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.embed_provider = None
            self.embed_client = None

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.05,
        max_tokens: int = 8192,
        tools: list | None = None,
        tool_choice: str | dict | None = None,
    ):
        """
        Chat completion. Returns plain text by default. If `tools` is passed, returns the raw
        message object instead (so the caller can inspect `.tool_calls`) — used for
        function-calling flows such as search_regulations() below.
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        message = await self.chat_raw(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice=tool_choice,
        )
        if tools:
            return message
        return message.content or ""

    async def chat_raw(
        self,
        model: str,
        messages: list,
        temperature: float = 0.05,
        max_tokens: int = 8192,
        tools: list | None = None,
        tool_choice: str | dict | None = None,
    ):
        """
        Lower-level chat call taking a full message list (needed for multi-step function-calling
        loops). Returns the raw message object. Tries each configured provider in order.
        """
        if not self.providers:
            raise RuntimeError("LLM API error: no API key configured (set GROQ_API_KEY or GEMINI_API_KEY)")

        errors = []
        for prov in self.providers:
            kwargs = {
                "model": prov.model or _resolve_model(model),
                "messages": messages,
            }
            # Reasoning models burn part of the limit on hidden thinking — add headroom for
            # Groq/Gemini so the visible answer (often long JSON) isn't truncated.
            headroom = getattr(settings, "LLM_REASONING_HEADROOM", 6000) if prov.name in ("groq", "gemini") else 0
            effective_max = max_tokens + headroom
            # Gemini's OpenAI-compat layer takes max_tokens; Groq/OpenAI take max_completion_tokens.
            limit_key = "max_tokens" if prov.name == "gemini" else "max_completion_tokens"
            kwargs[limit_key] = effective_max
            if tools:
                kwargs["tools"] = tools
                if tool_choice:
                    kwargs["tool_choice"] = tool_choice
            if prov.name == "groq" and "gpt-oss" in (prov.model or ""):
                kwargs["extra_body"] = {"reasoning_effort": getattr(settings, "GROQ_REASONING_EFFORT", "medium")}

            async def _call(**extra):
                try:
                    return await prov.client.chat.completions.create(temperature=temperature, **{**kwargs, **extra})
                except Exception as temp_err:
                    # Some reasoning models only accept the default temperature — retry without it.
                    if "temperature" in str(temp_err).lower():
                        return await prov.client.chat.completions.create(**{**kwargs, **extra})
                    raise

            try:
                completion = await _call()
                choice = completion.choices[0]
                # Output hit the limit (thinking + answer too long) → retry once with double the limit.
                if getattr(choice, "finish_reason", None) == "length" and not getattr(choice.message, "tool_calls", None):
                    logger.warning(f"LLM provider '{prov.name}' output truncated at {effective_max} tokens; retrying with {effective_max * 2}")
                    completion = await _call(**{limit_key: effective_max * 2})
                    choice = completion.choices[0]
                return choice.message
            except Exception as e:
                logger.warning(f"LLM provider '{prov.name}' failed: {e}")
                errors.append(f"{prov.name}: {e}")

        logger.error(f"All LLM providers failed: {errors}")
        raise RuntimeError(f"LLM API error: all providers failed — {'; '.join(errors)}")

    async def embed(self, text: str) -> list[float]:
        """
        Embeddings, 768 dims (matches the Qdrant collections). Gemini (gemini-embedding-001) if
        GEMINI_API_KEY is set, else OpenAI text-embedding-3-small. One provider only — no
        fallback between them, because vectors from different models can't be compared.
        Returns [] if unavailable, so RAG is skipped and the hardcoded IRDAI context is used.
        """
        if self.embed_client is None:
            logger.warning("No GEMINI_API_KEY/OPENAI_API_KEY set — embeddings unavailable, skipping RAG")
            return []
        try:
            if self.embed_provider == "gemini":
                resp = await self.embed_client.embeddings.create(
                    model=settings.GEMINI_EMBEDDING_MODEL, input=text, dimensions=EMBEDDING_DIMENSIONS)
                vec = list(resp.data[0].embedding)
                # Truncated Gemini embeddings aren't unit-length; normalise for consistent similarity.
                norm = sum(x * x for x in vec) ** 0.5
                return [x / norm for x in vec] if norm else vec
            resp = await self.embed_client.embeddings.create(
                model=EMBEDDING_MODEL, input=text, dimensions=EMBEDDING_DIMENSIONS)
            return resp.data[0].embedding
        except Exception as e:
            logger.warning(f"Embedding failed ({self.embed_provider}): {e} — RAG context will be skipped")
            return []


# Singleton — kept as the name `gemini` so every other module (which does
# `from app.services.llm.gemini_service import ...`) needs no changes.
gemini = OpenAIClientWrapper()


# ── Function calling ────────────────────────────────────────────────
# Give GPT-5 Nano a tool that lets it pull from RedoClaim's own Qdrant
# knowledge base instead of relying on built-in web search (disabled for
# this org). This is the pattern recommended for RedoClaim: your backend
# stays the source of truth, GPT is the reasoning/orchestration layer.
REGULATION_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_regulations",
        "description": (
            "Search RedoClaim's own IRDAI regulation and policy-clause knowledge "
            "base (Qdrant) for passages relevant to a claim issue. Always prefer "
            "this over general knowledge for anything regulatory."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language description of the issue, e.g. 'claim rejected for pre-existing disease exclusion'",
                }
            },
            "required": ["query"],
        },
    },
}


async def call_with_regulation_search(prompt: str, system: str = "", model: str = "gemini-2.5-flash") -> dict:
    """
    Example function-calling loop: GPT-5 Nano decides whether it needs
    regulatory context, calls search_regulations(query), we run the real
    Qdrant search via rag_pipeline, then GPT produces its final structured
    answer using those retrieved passages as grounding.
    """
    from app.services.rag.rag_pipeline import search_irdai_regulations as search_irdai_context

    message = await gemini.generate(
        model=model,
        prompt=prompt,
        system=system,
        tools=[REGULATION_SEARCH_TOOL],
        tool_choice="auto",
    )

    if not getattr(message, "tool_calls", None):
        return _parse_json(message.content or "", "call_with_regulation_search")

    tool_call = message.tool_calls[0]
    args = json.loads(tool_call.function.arguments or "{}")
    query = args.get("query", "")
    context = await search_irdai_context(query)

    follow_up_prompt = (
        f"{prompt}\n\nRELEVANT REGULATIONS RETRIEVED FROM YOUR KNOWLEDGE BASE:\n{context}"
    )
    raw = await gemini.generate(model=model, prompt=follow_up_prompt, system=system)
    return _parse_json(raw, "call_with_regulation_search")


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
        "You are an AI research assistant helping Indian health insurance policyholders "
        "review a claim rejection against IRDAI regulations. You are NOT a lawyer. "
        "Your output is NOT legal advice and is NOT an official determination. "
        "You reference the IRDAI Master Circular on Health Insurance, 2024, IRDAI Health Regs 2024, "
        "Insurance Ombudsman Rules 2017, Consumer Protection Act, 2019. "
        "You perform a structured evidence-based analysis in three stages: "
        "Step 1: timeline and TAT analysis. Step 2: potential regulatory inconsistencies. Step 3: redressal route. "
        "Never state that an insurer has violated a law, regulation or policy term. "
        "Describe each finding as a potential inconsistency or an apparent inconsistency for the user to review. "
        "For each finding identify the source, the specific provision, and the supporting text from the uploaded documents. "
        "Do not assume one universal deadline. State the applicable timeline together with its basis, "
        "and if the basis cannot be identified from the material provided, say so. "
        "CRITICAL: Return ONLY a valid JSON object. "
        "Output MUST start with { and end with }. "
        "No markdown fences, no preamble, no text before { or after }."
    )

    prompt = f"""CLAIM REJECTION ANALYSIS — structured evidence-based analysis.
Use cautious wording such as "potential inconsistency" or "appears inconsistent". Do not use the words "violated" or "violation" in any value you write.

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
      {{"type": "...", "regulation": "Source and provision e.g. IRDAI Master Circular on Health Insurance, 2024, Para X.Y", "detail": "...", "applicable_timeline": "e.g. 15 days", "basis": "specific provision or source for this timeline, or not identified"}}
    ],
    "interest_applicable": false
  }},

  "step2_regulatory_violations": [
    {{
      "violation": "Description of the potential inconsistency, in cautious wording",
      "regulation": "Exact citation e.g. IRDAI Master Circular on Health Insurance, 2024, Para 8.3",
      "source": "Name of the source document e.g. IRDAI Master Circular on Health Insurance, 2024",
      "provision": "Specific section or paragraph",
      "evidence_from_document": "Short extract or paraphrase from the uploaded rejection letter or policy that supports this finding",
      "verification_note": "Review against the current primary source before relying on this finding.",
      "severity": "high|medium|low",
      "argument": "How the user may raise this in an appeal"
    }}
  ],

  "deficiency_in_service": false,
  "deficiency_grounds": ["..."],
  "deficiency_statement": "Neutral statement of the grounds on which a Deficiency in Service allegation under CPA 2019 Section 2(11) could be considered. Do not present it as established.",

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
    "ejagriti_applicable": true,
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
            "For OD claims: cite apparent surveyor TAT delays, IDV disputes, depreciation schedule. "
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
        f"based on IRDAI regulations. You are NOT a lawyer. These are AI-generated, editable DRAFTS "
        f"for the user to review, verify and correct before sending. "
        f"Where relevant, use the legal term 'Deficiency in Service' (CPA 2019 Section 2(11)) as an allegation, not as an established fact. "
        f"Phrase concerns as apparent or potential inconsistencies and do not assert that a violation has been established. "
        f"Cite specific IRDAI regulations with paragraph numbers where they are supplied in the analysis. "
        f"Follow correct Indian legal letter format. "
        f"Insurance type: {insurance_type.upper()}. {type_context}"
    )

    appeal_descriptions = {
        "gro": {
            "to": "The Grievance Redressal Officer (GRO)",
            "org": f"{insurer_name}",
            "context": (
                "First formal escalation. Refer to the applicable timelines and their stated basis. "
                "Request resolution within the insurer's applicable grievance timeline. Mention possible Ombudsman escalation. "
                "If the documented dates indicate the applicable timeline may have been exceeded, request interest where applicable, citing its basis."
            ),
        },
        "insurer_escalation": {
            "to": "The Chief Executive Officer / Chairman & Managing Director",
            "org": f"{insurer_name}",
            "context": (
                "Direct CEO escalation. Use firm but measured language about apparent regulatory inconsistencies. "
                "Mention potential IRDAI complaint and Ombudsman filing. "
                "Reference Deficiency in Service under Consumer Protection Act, 2019."
            ),
        },
        "ombudsman": {
            "to": "The Insurance Ombudsman",
            "org": "Office of the Insurance Ombudsman",
            "context": (
                "Formal Ombudsman complaint under Insurance Ombudsman Rules 2017. "
                "State GRO was filed and unresolved. Cite all potential inconsistencies identified in the analysis. "
                "Claim full amount + interest + costs up to Rs.5,000. "
                "Reference Deficiency in Service under CPA 2019 S.2(11)."
            ),
        },
        "bima_bharosa": {
            "to": "The Grievance Cell",
            "org": "IRDAI — Bima Bharosa Portal (igms.irda.gov.in)",
            "context": (
                "IRDAI portal complaint. Concise, factual, regulatory-focused. "
                "List each IRDAI provision the rejection appears inconsistent with, with paragraph numbers. "
                "Request IRDAI intervention and insurer show-cause notice."
            ),
        },
        "consumer_court": {
            "to": "The Hon'ble President",
            "org": "District Consumer Disputes Redressal Commission",
            "context": (
                "Formal Consumer Court complaint. Lead with Deficiency in Service under "
                "CPA 2019 Section 2(11). Reference e-Jagriti filing. "
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

POTENTIAL REGULATORY INCONSISTENCIES IDENTIFIED:
{json.dumps(violations, indent=2)[:1500] if violations else "See timeline analysis below"}

TIMELINE AND TAT ANALYSIS:
{json.dumps(sla, indent=2)[:800] if sla else "No timeline concerns detected"}

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
5. Para 2-4: Arguments with the relevant IRDAI citations, each phrased as an apparent inconsistency
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
        "review a claim rejection. You are NOT a lawyer. Output is NOT legal advice and is NOT an official determination. "
        "You reference IRDAI Motor Insurance Guidelines 2017, Motor Vehicles Act 1988, "
        "IRDAI Master Circular 2024, Insurance Ombudsman Rules 2017, CPA 2019. "
        "Describe findings as potential inconsistencies and never state that a violation has been established. "
        "CRITICAL: Return ONLY a valid JSON object. "
        "Output MUST start with { and end with }. No markdown, no text outside the JSON."
    )

    prompt = f"""MOTOR INSURANCE CLAIM REJECTION ANALYSIS.

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
    "ejagriti_applicable": true,
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
        "You are an AI research assistant helping Indian life insurance claimants "
        "review a claim rejection against IRDAI regulations and Insurance Act 1938. "
        "You are NOT a lawyer. Output is NOT legal advice and is NOT an official determination. "
        "Describe findings as potential inconsistencies and never state that a violation has been established. "
        "You reference IRDAI Life Regs 2023, Insurance Act 1938 S.45, "
        "IRDAI Master Circular 2024, Ombudsman Rules 2017, CPA 2019. "
        "CRITICAL: Return ONLY a valid JSON object. "
        "Output MUST start with { and end with }. No markdown, no text outside the JSON."
    )

    prompt = f"""LIFE INSURANCE CLAIM REJECTION ANALYSIS.

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
    "ejagriti_applicable": true,
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

# ── Health Insurance Literacy Explainer ─────────────────────────────
async def explain_insurance_term(term_or_clause: str, target_language: str = "en") -> dict:
    """
    Plain-language explanation of any insurance term/clause the user pastes
    in. Reuses the same OpenAI call you already pay for elsewhere — this
    isn't a new external cost, just a new prompt/endpoint over it.
    Regional-language output is handled by the caller via Sarvam (existing
    /language endpoints), same as the rest of the app — this always
    generates in English first for consistent quality, then the route
    layer can translate.
    """
    system = (
        "You are an insurance-literacy explainer for Indian consumers. Explain insurance "
        "terms and policy clauses in plain, simple language a non-expert can understand. "
        "Use a short real-world example where helpful. Never give legal advice — just explain "
        "what the term/clause commonly means in Indian health/motor/life insurance."
    )
    prompt = f"""Explain this insurance term or clause in plain English, for someone with no insurance background:

"{term_or_clause}"

Respond as JSON:
{{
  "term": "...",
  "plain_explanation": "2-4 simple sentences",
  "example": "one short real-world example",
  "why_it_matters": "one sentence on why a policyholder should care about this"
}}
Return ONLY the JSON object."""

    raw = await gemini.generate(
        model=settings.MODEL_DRAFTING if hasattr(settings, "MODEL_DRAFTING") else "gpt-5-nano",
        prompt=prompt,
        system=system,
        temperature=0.3,
        max_tokens=500,
    )
    return _parse_json(raw, context="explain_insurance_term")


# ── Renewal Red-Flag Checker ─────────────────────────────────────────
async def check_renewal_red_flags(old_clauses: dict, new_clauses: dict) -> dict:
    """
    Diffs last year's extracted policy clauses against this year's renewal
    clauses and flags changes that quietly disadvantage the policyholder —
    reduced sum insured, new exclusions, a shrunk room-rent cap, a
    disproportionate premium hike relative to sum-insured changes.
    Unlike the Policy Comparison Tool (pure local diff, no LLM), this needs
    judgment about which changes are actually adverse vs neutral, so it's
    one LLM call over already-extracted clauses — not raw documents.
    """
    system = (
        "You audit Indian health/motor/life insurance policy renewals for changes that quietly "
        "disadvantage the policyholder. Compare last year's clauses to this year's. Flag only "
        "genuinely adverse changes — a clarified wording or a truly neutral change is not a red flag."
    )
    prompt = f"""Last year's policy clauses (JSON):
{json.dumps(old_clauses, indent=2)}

This year's renewal clauses (JSON):
{json.dumps(new_clauses, indent=2)}

Compare them and respond as JSON:
{{
  "red_flags": [
    {{"field": "sum_insured|room_rent_cap|co_payment|exclusions|sub_limits|premium|other",
      "old_value": "...", "new_value": "...",
      "severity": "high|medium|low",
      "explanation": "why this specifically disadvantages the policyholder"}}
  ],
  "neutral_changes": ["short description of any changes that are NOT adverse"],
  "overall_verdict": "one paragraph plain-English summary of whether this renewal is worth accepting as-is, negotiating, or porting away from"
}}
If there genuinely are no adverse changes, return an empty red_flags array — do not invent flags.
Return ONLY the JSON object."""

    raw = await gemini.generate(
        model=settings.MODEL_DRAFTING,
        prompt=prompt,
        system=system,
        temperature=0.2,
        max_tokens=1200,
    )
    return _parse_json(raw, context="check_renewal_red_flags")


# ── Second Opinion on Settlement Amount ──────────────────────────────
async def audit_settlement(
    settlement_text: str,
    policy_clauses: dict,
    claim_amount: float,
    settled_amount: float,
    irdai_context: str = "",
) -> dict:
    """
    For PARTIAL settlements (not outright rejections) — audits whether the
    amount an insurer actually paid matches what the policy terms justify,
    the same "hierarchy of evidence" way audit_rejection checks a denial.
    Reuses the same regulatory grounding, applied to under-payment instead
    of non-payment.
    """
    system = (
        "You are an AI legal research assistant helping Indian insurance policyholders "
        "review whether a PARTIAL settlement amount appears consistent with the terms of their policy. "
        "You are NOT a lawyer. Your output is NOT legal advice and is NOT an official determination. "
        "Reference IRDAI Master Circular 2024, IRDAI Health Regs 2024, Insurance Ombudsman Rules 2017. "
        "CRITICAL: Return ONLY a valid JSON object. Output MUST start with { and end with }. "
        "No markdown fences, no preamble, no text before { or after }."
    )

    shortfall = claim_amount - settled_amount

    prompt = f"""SETTLEMENT AMOUNT ANALYSIS

CLAIM AMOUNT: ₹{claim_amount:,.0f}
AMOUNT ACTUALLY SETTLED: ₹{settled_amount:,.0f}
SHORTFALL: ₹{shortfall:,.0f}

INSURER'S SETTLEMENT LETTER / DEDUCTION EXPLANATION:
{settlement_text[:3500]}

POLICY CLAUSES ON RECORD:
{json.dumps(policy_clauses, indent=2)[:2000] if policy_clauses else "Not provided"}

IRDAI REGULATIONS (from RAG knowledge base):
{irdai_context[:2000] if irdai_context else "Not available"}

Check whether each deduction the insurer made is actually justified by the policy clauses on
record. Return ONLY this JSON object:
{{
  "deductions_reviewed": [
    {{"stated_reason": "...", "amount_deducted": 0, "justified_by_policy": true,
      "explanation": "why this deduction does or doesn't match the policy clauses",
      "regulation_reference": "citation if a regulation is relevant, else null"}}
  ],
  "total_questionable_deduction": 0,
  "is_settlement_likely_correct": true,
  "confidence": "high|medium|low",
  "key_arguments": ["argument to use if disputing the shortfall"],
  "recommended_action": "accept|gro_appeal|ombudsman|consumer_court",
  "reasoning": "one paragraph summary"
}}
Return ONLY the JSON object."""

    raw = await gemini.generate(
        model=settings.MODEL_LEGAL,
        prompt=prompt,
        system=system,
        temperature=0.05,
        max_tokens=2500,
    )
    return _parse_json(raw, context="audit_settlement")


# ── Pre-Authorization Denial Checker ─────────────────────────────────
async def audit_preauth_denial(
    denial_text: str,
    policy_clauses: dict,
    irdai_context: str,
    treatment_amount: float | None = None,
) -> dict:
    """
    Separate from a post-discharge claim rejection: a cashless PRE-AUTH
    denial at hospital admission has its own IRDAI timeline (cashless
    request TAT — 1 hour for initial authorization, 3 hours for discharge
    authorization, per the IRDAI Master Circular 2024) and a different
    practical remedy (pay and claim reimbursement, not GRO/Ombudsman as
    the first step) — so this gets its own prompt rather than reusing
    audit_rejection's claim-TAT framing.
    """
    system = (
        "You are an AI legal research assistant helping Indian insurance policyholders "
        "understand a CASHLESS PRE-AUTHORIZATION denial at hospital admission — this is "
        "distinct from a post-discharge claim rejection. You are NOT a lawyer. Your output "
        "is NOT legal advice. Reference IRDAI Master Circular on cashless facility TAT "
        "(1 hour for initial pre-auth, 3 hours for final discharge authorization), IRDAI "
        "Health Insurance Regulations 2024. "
        "CRITICAL: Return ONLY a valid JSON object. Output MUST start with { and end with }. "
        "No markdown fences, no preamble, no text before { or after }."
    )

    prompt = f"""CASHLESS PRE-AUTHORIZATION DENIAL ANALYSIS

INSURER'S PRE-AUTH DENIAL / QUERY LETTER:
{denial_text[:3500]}

POLICY CLAUSES ON RECORD:
{json.dumps(policy_clauses, indent=2)[:2000] if policy_clauses else "Not provided"}

IRDAI REGULATIONS (from RAG knowledge base):
{irdai_context[:2500] if irdai_context else "Not available"}

ESTIMATED TREATMENT COST: {f"₹{treatment_amount:,.0f}" if treatment_amount else "Not provided"}

A pre-auth denial is NOT a final claim rejection — the patient can still pay out of pocket and
file for reimbursement under the same policy. Analyze whether the denial reason itself is valid,
and whether the insurer met the cashless TAT (1 hour initial response, 3 hours for discharge
authorization once complete documents were submitted).

Return ONLY this JSON object:
{{
  "denial_reason_category": "insufficient_info|policy_exclusion|network_hospital_dispute|sub_limit|waiting_period|treatment_not_covered|other",
  "denial_reason_summary": "1-2 sentence summary of what the insurer says",
  "is_valid_denial": false,
  "confidence": "high|medium|low",
  "tat_violated": false,
  "tat_violation_detail": "documented timing that appears inconsistent with the applicable cashless timeline and its basis, if any, else null",
  "immediate_recommendation": "pay_and_reimburse|escalate_to_gro_first|challenge_before_admission",
  "reimbursement_path_note": "brief note on the fact that paying out-of-pocket and claiming reimbursement afterward is still available regardless of this denial",
  "key_arguments": ["argument 1", "argument 2"],
  "reasoning": "one paragraph summary"
}}
Return ONLY the JSON object."""

    raw = await gemini.generate(
        model=settings.MODEL_LEGAL,
        prompt=prompt,
        system=system,
        temperature=0.05,
        max_tokens=2000,
    )
    return _parse_json(raw, context="audit_preauth_denial")
