"""
RAG Pipeline — RedoClaim
Qdrant vector DB for IRDAI regulations, policy chunks, CIS documents.
All embeddings generated locally via Ollama nomic-embed-text (no cloud).

Collections:
  - redoclaim_policy_chunks     : user policy document chunks
  - redoclaim_irdai_regulations : IRDAI Master Circular 2024 + Health Regs 2024
  - redoclaim_rejection_patterns: known unfair rejection tactics
  - redoclaim_cis_chunks        : Customer Information Sheet chunks
"""
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
EMBEDDING_DIM = 768  # nomic-embed-text

client = QdrantClient(url=settings.QDRANT_URL)

COLLECTIONS = {
    "policy":     settings.QDRANT_POLICY_COLLECTION,
    "irdai":      settings.QDRANT_IRDAI_COLLECTION,
    "rejections": settings.QDRANT_REJECTION_COLLECTION,
    "cis":        "redoclaim_cis_chunks",
}


async def ensure_collections():
    existing = {c.name for c in client.get_collections().collections}
    for name in COLLECTIONS.values():
        if name not in existing:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {name}")


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
    for chunk in chunks:
        try:
            vector = await generate_embeddings(chunk["text"])
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
        except Exception as e:
            logger.warning(f"Embed chunk {chunk['chunk_index']} failed: {e}")
    if points:
        client.upsert(collection_name=collection, points=points)
        logger.info(f"Stored {len(points)} chunks → {collection}")
    return len(points)


async def search_irdai_regulations(query: str, top_k: int = 6) -> str:
    """
    RAG retrieval of IRDAI regulations relevant to the query.
    Falls back to hardcoded context if Qdrant is empty or unavailable.
    """
    await ensure_collections()
    try:
        vector = await generate_embeddings(query)
        results = client.search(
            collection_name=COLLECTIONS["irdai"],
            query_vector=vector,
            limit=top_k,
        )
        if results and len(results) >= 2:
            texts = [r.payload.get("text", "") for r in results]
            logger.info(f"RAG: retrieved {len(texts)} IRDAI chunks for query: {query[:60]}")
            return "\n\n---\n\n".join(texts)
        else:
            logger.info("Qdrant returned <2 results, using hardcoded IRDAI context")
            return _get_hardcoded_irdai_context()
    except Exception as e:
        logger.warning(f"Qdrant search failed: {e} — using hardcoded context")
        return _get_hardcoded_irdai_context()


async def search_rejection_patterns(rejection_text: str, top_k: int = 4) -> str:
    """RAG retrieval of known unfair rejection patterns."""
    await ensure_collections()
    try:
        vector = await generate_embeddings(rejection_text[:500])
        results = client.search(
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
        results = client.search(
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
        results = client.search(
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
    client.delete(
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
IRDAI MASTER CIRCULAR ON PROTECTION OF POLICYHOLDERS
INTERESTS (2024) — KEY PROVISIONS FOR AI AUDIT
════════════════════════════════════════════════════════

[SECTION A — TURNAROUND TIMES (TATs)]
The following TATs are MANDATORY. Violation = automatic grounds for appeal.

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
• Resolution by GRO: Within 15 DAYS of complaint receipt
• If unresolved in 15 days → insurer must auto-escalate to senior officer

Interest on Delayed Claims (Para 7.4):
If insurer delays settlement beyond 30 days due to their own fault:
→ Interest = Bank Rate + 2% per annum on the pending amount (MANDATORY)
→ Policyholder can claim this interest in any appeal or court filing

[SECTION B — CASHLESS TREATMENT RIGHTS]
• Insurer CANNOT refuse cashless and ask for reimbursement if network hospital exists
• Pre-authorisation CANNOT be denied without citing a specific policy exclusion
• Hospital cannot demand upfront cash if cashless pre-auth is active
• Insurer/TPA CANNOT demand documents that the hospital/treating doctor must provide
• Rejection cannot cite "insufficient documents" without specifying EXACTLY which documents
  are missing and WHY they are required
• All cashless decisions must be communicated in writing
• Verbal denials of cashless are INVALID and violate the Master Circular

[SECTION C — CUSTOMER INFORMATION SHEET (CIS)]
• Every insurer MUST provide a CIS at policy issuance (Para 4.2)
• CIS must clearly state in simple language:
  - All INCLUSIONS (what is covered)
  - All EXCLUSIONS (what is NOT covered)
  - Waiting periods (type, duration)
  - Sub-limits and co-payments
  - Key conditions for claim settlement
• If insurer failed to provide CIS → this is itself a regulatory violation
• AI should scan uploaded CIS to extract inclusions/exclusions automatically
• Insurer CANNOT enforce exclusions that are NOT mentioned in the CIS

[SECTION D — DOCUMENT DEMANDS]
• Insurer cannot repeatedly ask for documents already submitted
• Each document request must specify the document, reason needed, and deadline
• If insurer cites a document-related rejection after documents were already submitted:
  → This is a violation of Para 8.3 of the Master Circular
• Insurer bears the burden of specifying which documents are missing

════════════════════════════════════════════════════════
IRDAI (HEALTH INSURANCE) REGULATIONS 2024
════════════════════════════════════════════════════════

[MORATORIUM PERIOD — Regulation 8(6)]
After 5 CONTINUOUS YEARS of health insurance coverage:
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
• Maternity waiting period: As per policy (typically 9-12 months)

════════════════════════════════════════════════════════
INSURANCE OMBUDSMAN RULES 2017
════════════════════════════════════════════════════════

[JURISDICTION & ELIGIBILITY]
• Claim value: Up to ₹50,00,000 (Fifty Lakhs)
• Applies to: Life, Health, Motor, Property insurance
• Who can file: Policyholder, nominee, legal heir, assignee, authorised representative
• Filing deadline: Within 1 YEAR of insurer's final decision
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
CONSUMER PROTECTION ACT 2019 — INSURANCE CLAIMS
════════════════════════════════════════════════════════

[DEFICIENCY IN SERVICE — Section 2(11)]
Insurance claim rejection constitutes "Deficiency in Service" when:
• Claim is rejected unreasonably or arbitrarily without valid policy ground
• Settlement is delayed beyond IRDAI mandated 30-day period
• Insurer provides false or misleading information to reject claim
• Insurer fails to process documents within TAT
• Policy was mis-sold (features misrepresented at time of sale)
→ AI MUST use the exact legal term "Deficiency in Service" in all appeal letters

[PRODUCT LIABILITY — Section 2(34)]
If the insurance product itself was:
• Misleadingly marketed or mis-sold
• Designed with unfair terms not disclosed at sale
• Presented with false promises about coverage
→ This gives rise to a PRODUCT LIABILITY claim (separate from Deficiency in Service)

[E-DAAKHIL — ONLINE CONSUMER COURT FILING]
Portal: edaakhil.nic.in
Procedure:
1. Register on E-Daakhil portal
2. Fill online complaint form with policy + rejection details
3. Upload all documents digitally (rejection letter, policy, hospital records)
4. Pay nominal court fee online (₹200 for claims up to ₹5 Lakhs, varies by amount)
5. Receive case number and hearing schedule via email/SMS

Trigger for E-Daakhil: If insurer does NOT respond to complaint within 15 DAYS

Consumer Forums by claim amount:
• District Consumer Disputes Redressal Commission: Up to ₹50,00,000 (50 Lakhs)
• State Consumer Disputes Redressal Commission: ₹50L to ₹2,00,00,000 (2 Crores)
• National Consumer Disputes Redressal Commission: Above ₹2 Crores

Limitation period: 2 years from the date of cause of action (rejection date)

Relief available from Consumer Courts:
• Full claim amount
• Interest on delayed payment (typically 9–12% per annum)
• Compensation for mental agony and harassment
• Cost of litigation
• Punitive/exemplary damages in cases of gross misconduct

════════════════════════════════════════════════════════
HIERARCHY OF EVIDENCE (AI MUST FOLLOW THIS ORDER)
════════════════════════════════════════════════════════

Step 1 — SLA VIOLATION CHECK (highest priority)
  Did insurer miss 15-day GRO deadline? → AUTOMATIC violation
  Did insurer miss 30-day settlement TAT? → AUTOMATIC violation + interest applicable
  Did cashless take more than 1 hour? → AUTOMATIC violation
  → If YES to any: cite Para 7.3 of IRDAI Master Circular 2024

Step 2 — REGULATORY VIOLATION CHECK (via RAG)
  Does the rejection cite PED after 5-year moratorium? → Cite Regulation 8(6) Health Regs 2024
  Did insurer demand hospital documents from patient? → Cite Master Circular Para 8.3
  Did insurer reject for undisclosed exclusion (not in CIS)? → Cite Master Circular Para 4.2
  Did insurer deny cashless without written specific reason? → Cite Master Circular Section B

Step 3 — REDRESSAL ROUTE DETERMINATION
  Claim ≤ ₹50 Lakhs → Insurance Ombudsman (Ombudsman Rules 2017) — FREE
  Insurer silent after 15 days → E-Daakhil Consumer Court (CPA 2019)
  Claim > ₹50 Lakhs → Consumer Court directly
  Mis-selling suspected → Product Liability under CPA 2019

Step 4 — LETTER GENERATION
  GRO Letter: Must cite specific regulation paragraph + demand interest for delay
  Ombudsman: Must reference "Deficiency in Service" (CPA 2019 Section 2(11))
  Consumer Court: Must allege both Deficiency in Service + Product Liability if applicable
"""
