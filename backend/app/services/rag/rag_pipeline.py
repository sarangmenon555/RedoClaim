"""
RAG Pipeline — RedoClaim
Qdrant vector DB for IRDAI regulations, policy chunks, CIS documents.
Embeddings via OpenAI text-embedding-3-small (truncated to 768-dim).
If embeddings are unavailable (e.g. invalid API key), RAG is gracefully skipped
and the hardcoded IRDAI context is used as fallback.

Collections:
  - redoclaim_policy_chunks     : user policy document chunks
  - redoclaim_irdai_regulations : IRDAI Master Circular 2024 + Health Regs 2024
  - redoclaim_rejection_patterns: known unfair rejection tactics
  - redoclaim_cis_chunks        : Customer Information Sheet chunks
"""
import asyncio
import logging
import uuid
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    VectorParams, Distance, PointStruct,
    Filter, FieldCondition, MatchValue, FilterSelector
)
from app.core.config import settings
from app.services.llm.gemini_service import generate_embeddings

logger = logging.getLogger(__name__)
EMBEDDING_DIM = 768  # Gemini gemini-embedding-001 / OpenAI text-embedding-3-small, truncated to 768

class _AsyncQdrant:
    """
    The Qdrant client is synchronous. Calling it directly inside async code blocks
    the whole event loop (every other request, including login, waits). This proxy
    runs each call in a worker thread; usage is `await client.search(...)`.
    """
    def __init__(self, sync_client):
        self._c = sync_client

    def __getattr__(self, name):
        fn = getattr(self._c, name)

        async def run(*args, **kwargs):
            return await asyncio.to_thread(fn, *args, **kwargs)
        return run


client = _AsyncQdrant(QdrantClient(
    url=settings.QDRANT_URL,
    api_key=getattr(settings, "QDRANT_API_KEY", None),
    timeout=30,
))
_collections_ready = False

COLLECTIONS = {
    "policy":     settings.QDRANT_POLICY_COLLECTION,
    "irdai":      settings.QDRANT_IRDAI_COLLECTION,
    "rejections": settings.QDRANT_REJECTION_COLLECTION,
    "cis":        "redoclaim_cis_chunks",
}


def _is_valid_vector(vector: list) -> bool:
    """Return True only if vector is a non-empty list of floats."""
    return bool(vector) and isinstance(vector, list) and len(vector) > 0


async def ensure_collections():
    global _collections_ready
    if _collections_ready:
        return
    existing = {c.name for c in (await client.get_collections()).collections}
    for name in COLLECTIONS.values():
        if name not in existing:
            await client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {name}")
    _collections_ready = True


async def upsert_document_chunks(
    document_id: str,
    user_id: str,
    chunks: list[dict],
    collection: str = None,
) -> int:
    if collection is None:
        collection = COLLECTIONS["policy"]

    await ensure_collections()

    points = []
    skipped = 0

    sem = asyncio.Semaphore(5)  # embed a few chunks at a time instead of one-by-one

    async def _embed(chunk):
        async with sem:
            try:
                return chunk, await generate_embeddings(chunk["text"]), None
            except Exception as e:  # noqa: BLE001
                return chunk, None, e

    for chunk, vector, err in await asyncio.gather(*[_embed(c) for c in chunks]):
        if err is not None:
            skipped += 1
            logger.warning(f"Embed chunk {chunk['chunk_index']} failed: {err}")
            continue
        # Skip chunks with empty vectors - happens when the embedding API is unavailable
        if not _is_valid_vector(vector):
            skipped += 1
            logger.debug(f"Skipping chunk {chunk['chunk_index']} - empty embedding")
            continue
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "document_id": document_id,
                "user_id": user_id,
                "text": chunk["text"],
                "chunk_index": chunk["chunk_index"],
            },
        ))

    if skipped > 0:
        logger.warning(
            f"Skipped {skipped}/{len(chunks)} chunks due to missing embeddings. "
            "RAG search for this document will use hardcoded fallback context. "
            "To enable full RAG, set a valid GEMINI_API_KEY (or OPENAI_API_KEY) in Render env vars."
        )

    if points:
        await client.upsert(collection_name=collection, points=points)
        logger.info(f"Stored {len(points)} chunks → {collection}")
    else:
        logger.warning(
            f"No vectors stored for document {document_id} — "
            "embeddings unavailable. Document processing will continue "
            "using hardcoded IRDAI context for audits."
        )

    # Return 0 but do NOT raise — document processing should continue
    return len(points)


async def search_irdai_regulations(query: str, top_k: int = 6) -> str:
    """
    RAG retrieval of IRDAI regulations relevant to the query.
    Falls back to hardcoded context if embeddings unavailable or Qdrant is empty.
    """
    await ensure_collections()
    try:
        vector = await generate_embeddings(query)

        if not _is_valid_vector(vector):
            logger.info("Embeddings unavailable — using hardcoded IRDAI context")
            return _get_hardcoded_irdai_context()

        results = await client.search(
            collection_name=COLLECTIONS["irdai"],
            query_vector=vector,
            limit=top_k,
        )
        if results and len(results) >= 2:
            texts = [r.payload.get("text", "") for r in results]
            logger.info(f"RAG: retrieved {len(texts)} IRDAI chunks for query: {query[:60]}")
            return "\n\n---\n\n".join(texts)
        else:
            logger.info("Qdrant returned <2 results — using hardcoded IRDAI context")
            return _get_hardcoded_irdai_context()
    except Exception as e:
        logger.warning(f"Qdrant search failed: {e} — using hardcoded context")
        return _get_hardcoded_irdai_context()


async def search_rejection_patterns(rejection_text: str, top_k: int = 4) -> str:
    """RAG retrieval of known unfair rejection patterns."""
    await ensure_collections()
    try:
        vector = await generate_embeddings(rejection_text[:500])

        if not _is_valid_vector(vector):
            return ""

        results = await client.search(
            collection_name=COLLECTIONS["rejections"],
            query_vector=vector,
            limit=top_k,
        )
        if results:
            return "\n\n---\n\n".join(r.payload.get("text", "") for r in results)
    except Exception as e:
        logger.warning(f"Rejection pattern search failed: {e}")
    return ""


async def search_policy_chunks(query: str, document_id: str, top_k: int = 5) -> list[str]:
    """Search within a specific uploaded policy document."""
    await ensure_collections()
    try:
        vector = await generate_embeddings(query)

        if not _is_valid_vector(vector):
            return []

        results = await client.search(
            collection_name=COLLECTIONS["policy"],
            query_vector=vector,
            query_filter=Filter(must=[
                FieldCondition(key="document_id", match=MatchValue(value=document_id))
            ]),
            limit=top_k,
        )
        return [r.payload.get("text", "") for r in results]
    except Exception as e:
        logger.warning(f"Policy chunk search failed: {e}")
        return []


async def search_cis_chunks(query: str, document_id: str, top_k: int = 4) -> list[str]:
    """Search within a Customer Information Sheet document."""
    await ensure_collections()
    try:
        vector = await generate_embeddings(query)

        if not _is_valid_vector(vector):
            return []

        results = await client.search(
            collection_name=COLLECTIONS["cis"],
            query_vector=vector,
            query_filter=Filter(must=[
                FieldCondition(key="document_id", match=MatchValue(value=document_id))
            ]),
            limit=top_k,
        )
        return [r.payload.get("text", "") for r in results]
    except Exception as e:
        logger.warning(f"CIS search failed: {e}")
        return []


async def delete_document_chunks(document_id: str, collection_key: str = "policy"):
    """Delete all vectors for a document (GDPR right-to-erasure)."""
    col = COLLECTIONS.get(collection_key, COLLECTIONS["policy"])
    await client.delete(
        collection_name=col,
        points_selector=FilterSelector(
            filter=Filter(must=[
                FieldCondition(key="document_id", match=MatchValue(value=document_id))
            ])
        ),
    )


def _get_hardcoded_irdai_context() -> str:
    """
    Authoritative IRDAI regulation text used when Qdrant is empty.
    Run scripts/seed_irdai.py to populate Qdrant for full RAG retrieval.
    """
    return """
════════════════════════════════════════════════════════
IRDAI MASTER CIRCULAR REFERENCES (2024) — KEY PROVISIONS
FOR AI-ASSISTED ANALYSIS. VERIFY AGAINST PRIMARY SOURCES.
════════════════════════════════════════════════════════

[SECTION A — TURNAROUND TIMES (TATs)]
The following timelines are references used for analysis. The applicable timeline depends on the
type of claim or event, and must be stated together with its basis. If the basis cannot be
identified from the material, say so and do not present a single universal deadline.
Documented dates that appear inconsistent with a timeline are potential inconsistencies for the
user to review, not official determinations.

Health Insurance:
• Cashless pre-authorisation: WITHIN 1 HOUR of receiving complete documents
• Cashless final discharge authorisation: Within 3 hours of discharge request
• Reimbursement claim settlement: Within 30 DAYS of last document received
• Claim repudiation (rejection): Must cite specific policy clause + specific IRDAI regulation
• Acknowledgement of claim intimation: Within 15 MINUTES (digital/email)

Non-life (Motor, Property):
• Survey for claims >₹50,000: Within 3 WORKING DAYS of intimation
• Survey report to insurer: Within 15 days of survey completion
• Settlement after survey approval: Within 30 DAYS

Internal Grievance (GRO):
• Acknowledgement: Within 3 WORKING DAYS
• Resolution by GRO: approximately 15 DAYS from complaint receipt (some IRDAI health-insurance FAQ text states 14 days for the decision; verify). This is the INSURER's turnaround - there is no established deadline for the policyholder to file a grievance
• If unresolved in 15 days → insurer must auto-escalate to senior officer

Interest on Delayed Claims (Para 7.4):
If the insurer's delay in settlement beyond the applicable timeline is attributable to the insurer:
→ Interest at Bank Rate + 2% per annum on the pending amount may apply (verify the provision)
→ The policyholder may request this interest in an appeal or court filing

[SECTION B — CASHLESS TREATMENT RIGHTS]
• Insurer CANNOT refuse cashless and ask for reimbursement if network hospital exists
• Pre-authorisation CANNOT be denied without citing a specific policy exclusion
• Hospital cannot demand upfront cash if cashless pre-auth is active
• Insurer/TPA CANNOT demand documents that the hospital/treating doctor must provide
• Rejection cannot cite "insufficient documents" without specifying EXACTLY which documents
  are missing and WHY they are required
• All cashless decisions must be communicated in writing
• Verbal denials of cashless appear inconsistent with the Master Circular's requirement of written communication

[SECTION C — CUSTOMER INFORMATION SHEET (CIS)]
• Every insurer MUST provide a CIS at policy issuance (Para 4.2)
• CIS must clearly state in simple language:
  - All INCLUSIONS (what is covered)
  - All EXCLUSIONS (what is NOT covered)
  - Waiting periods (type, duration)
  - Sub-limits and co-payments
  - Key conditions for claim settlement
• If the insurer did not provide a CIS → this may be a potential regulatory inconsistency
• AI should scan uploaded CIS to extract inclusions/exclusions automatically
• Insurer CANNOT enforce exclusions that are NOT mentioned in the CIS

[SECTION D — DOCUMENT DEMANDS]
• Insurer cannot repeatedly ask for documents already submitted
• Each document request must specify the document, reason needed, and deadline
• If insurer cites a document-related rejection after documents were already submitted:
  → This may be a potential inconsistency with Para 8.3 of the Master Circular (verify)
• Insurer bears the burden of specifying which documents are missing

════════════════════════════════════════════════════════
IRDAI (HEALTH INSURANCE) REGULATIONS 2024
════════════════════════════════════════════════════════

[MORATORIUM PERIOD — Regulation 8(6)]
After 60 CONTINUOUS MONTHS (5 years) of health insurance coverage:
• Insurer CANNOT reject claim on grounds of non-disclosure of Pre-Existing Disease (PED)
• EXCEPTION: Only if the insurer can PROVE intentional fraudulent misrepresentation
• Burden of proof is on the INSURER — not on the policyholder
• Applies to ported policies: years with previous insurer COUNT toward moratorium
• Reduced from 8 years to 5 years in the 2024 reform
• Critical: "forgetting" to disclose a condition is NOT fraud
• Insurer must have evidence of deliberate concealment to overcome the moratorium

[PORTABILITY RIGHTS — Regulation 17]
• Policyholder can port health policy to ANY other IRDAI-registered insurer
• New insurer MUST accept the application (cannot arbitrarily refuse)
• Waiting periods already served CARRY FORWARD to new insurer
• No fresh initial waiting period at the new insurer
• Portability request: submit 45 days before policy renewal date
• Insurer cannot increase premium solely because of portability
• Benefits of continuity (moratorium credits) transfer with the policy
• AI should guide users through portability when current insurer is acting in bad faith

[WAITING PERIOD REFORMS — 2024]
• Initial waiting period: Maximum 30 days (accidents always covered from Day 1)
• Pre-existing disease (PED) waiting: Maximum 3 years (down from 4 years)
• Specific named disease waiting: Maximum 2 years
• Exception: specific-treatment and PED waiting periods generally do not apply where the treatment is required due to an accident - always check the policy's exception wording before concluding a waiting period applies
• Maternity waiting period: As per policy (typically 9-12 months)

════════════════════════════════════════════════════════
INSURANCE OMBUDSMAN RULES 2017
════════════════════════════════════════════════════════

[JURISDICTION & ELIGIBILITY]
• Claim value: Up to ₹50,00,000 (Fifty Lakhs)
• Applies to: Life, Health, Motor, Property insurance
• Who can file: Policyholder, nominee, legal heir, assignee, authorised representative
• Filing window: eligibility and time limits depend on the Ombudsman rules - generally within 1 YEAR of the relevant rejection/decision or expiry of the applicable insurer-response period, subject to eligibility requirements (do NOT state a short fixed deadline such as 45 days)
• Cost: COMPLETELY FREE for policyholders

[WHEN TO APPROACH OMBUDSMAN]
Policyholder can approach Ombudsman if:
1. Insurer rejects the grievance OR
2. GRO does not resolve within 30 days OR
3. Policyholder is unsatisfied with GRO resolution

[HOW TO FILE]
• Online: www.igms.irda.gov.in (IRDAI Integrated Grievance Management System)
• Find ombudsman: search by state at www.ecoi.co.in
• Physical offices in all major Indian cities

[OMBUDSMAN POWERS]
• Can award FULL claim amount
• Can award up to ₹5,000 as legal/procedural costs
• Award is binding on the insurer if the policyholder accepts
• Insurer must comply within 30 days of award
• Policyholder can reject the award and still approach civil courts

════════════════════════════════════════════════════════
CONSUMER PROTECTION ACT, 2019 — INSURANCE CLAIMS
════════════════════════════════════════════════════════

[DEFICIENCY IN SERVICE — Section 2(11)]
Insurance claim rejection constitutes "Deficiency in Service" when:
• Claim is rejected unreasonably or arbitrarily without valid policy ground
• Settlement is delayed beyond the applicable timeline
• Insurer provides false or misleading information to reject claim
• Insurer fails to process documents within TAT
• Policy was mis-sold (features misrepresented at time of sale)
• Where the evidence supports it, appeal letters may allege "Deficiency in Service" as an allegation, not as an established fact; where evidence is insufficient, do not allege it

[PRODUCT LIABILITY — Section 2(34)]
If the insurance product itself was:
• Misleadingly marketed or mis-sold
• Designed with unfair terms not disclosed at sale
• Presented with false promises about coverage
→ This gives rise to a PRODUCT LIABILITY claim (separate from Deficiency in Service)

[e-Jagriti — ONLINE CONSUMER COURT FILING]
Portal: e-jagriti.gov.in
Procedure:
1. Register on e-Jagriti portal
2. Fill online complaint form with policy + rejection details
3. Upload all documents digitally (rejection letter, policy, hospital records)
4. Pay nominal court fee online (₹200 for claims up to ₹5 Lakhs, varies by amount)
5. Receive case number and hearing schedule via email/SMS

Trigger for e-Jagriti: If insurer does NOT respond to complaint within 15 DAYS

Consumer Forums by claim amount:
• District Consumer Disputes Redressal Commission: Up to ₹50,00,000 (50 Lakhs)
• State Consumer Disputes Redressal Commission: ₹50L to ₹2,00,00,000 (2 Crores)
• National Consumer Disputes Redressal Commission: Above ₹2 Crores

Limitation: consumer-law limitation may apply and depends on the cause of action and legal context - do not state a fixed period; obtain appropriate legal guidance

Relief available from Consumer Courts:
• Full claim amount
• Interest on delayed payment (typically 9–12% per annum)
• Compensation for mental agony and harassment
• Cost of litigation
• Punitive/exemplary damages in cases of gross misconduct

════════════════════════════════════════════════════════
STRUCTURED EVIDENCE-BASED ANALYSIS (FOLLOW THIS ORDER)
════════════════════════════════════════════════════════

Step 1 — TIMELINE & TAT ANALYSIS (highest priority)
  Do the documented dates appear consistent with the applicable grievance timeline?
  Do the documented dates appear consistent with the applicable claim settlement timeline?
  Do the documented times appear consistent with the applicable cashless timeline?
  → For each concern: state the applicable timeline, its basis, and the documented dates

Step 2 — POTENTIAL REGULATORY INCONSISTENCIES (via RAG)
  Does the rejection cite PED after 5-year moratorium? → Cite Regulation 8(6) Health Regs 2024
  Did insurer demand hospital documents from patient? → Cite Master Circular Para 8.3
  Did insurer reject for undisclosed exclusion (not in CIS)? → Cite Master Circular Para 4.2
  Did insurer deny cashless without written specific reason? → Cite Master Circular Section B

Step 3 — REDRESSAL ROUTE DETERMINATION
  Claim ≤ ₹50 Lakhs → Insurance Ombudsman (Ombudsman Rules 2017) — FREE
  Insurer silent after 15 days → e-Jagriti Consumer Court (CPA 2019)
  Claim > ₹50 Lakhs → Consumer Court directly
  Mis-selling suspected → Product Liability under CPA 2019

Step 4 — LETTER GENERATION
  GRO Letter: Must cite specific regulation paragraph + demand interest for delay
  Ombudsman: Must reference "Deficiency in Service" (CPA 2019 Section 2(11))
  Consumer Court: Must allege both Deficiency in Service + Product Liability if applicable
"""