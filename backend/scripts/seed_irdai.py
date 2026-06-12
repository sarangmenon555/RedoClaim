"""
scripts/seed_irdai.py — Seed Qdrant with IRDAI regulations for RAG.

Run once after setting up Jina AI embeddings:
  cd backend
  python scripts/seed_irdai.py

Requirements:
  - JINA_API_KEY set in environment or .env file
  - QDRANT_URL and QDRANT_API_KEY set in environment or .env file
  - pip install qdrant-client httpx python-dotenv

This populates the `irdai_regulations` Qdrant collection so that
rejection audits use real vector search instead of the hardcoded fallback.
"""
import asyncio
import httpx
import uuid
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded .env file")
except ImportError:
    logger.info("python-dotenv not installed, reading from environment directly")

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct

# ── Config ────────────────────────────────────────────────────────
JINA_API_KEY  = os.environ.get("JINA_API_KEY", "")
QDRANT_URL    = os.environ.get("QDRANT_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
COLLECTION    = os.environ.get("QDRANT_IRDAI_COLLECTION", "irdai_regulations")
EMBEDDING_DIM = 768  # jina-embeddings-v2-base-en


# ── IRDAI Regulation Chunks ───────────────────────────────────────
# Each entry becomes one vector in Qdrant.
# Add more chunks here as you find more relevant regulation text.
IRDAI_CHUNKS = [
    {
        "title": "TAT - Cashless Pre-Authorisation",
        "text": (
            "IRDAI Master Circular on Protection of Policyholders Interests 2024, Para 7.1: "
            "Cashless pre-authorisation must be granted or denied within 1 HOUR of receiving "
            "complete documents from the network hospital. Any delay beyond 1 hour constitutes "
            "a TAT violation and grounds for regulatory complaint."
        ),
        "regulation": "IRDAI Master Circular 2024, Para 7.1",
        "category": "tat_sla",
    },
    {
        "title": "TAT - Cashless Final Discharge",
        "text": (
            "IRDAI Master Circular 2024, Para 7.2: Final discharge authorisation for cashless "
            "treatment must be granted within 3 hours of the hospital submitting the discharge "
            "request with complete documents. Delays cause the patient to be held at hospital "
            "and constitute deficiency in service under CPA 2019 Section 2(11)."
        ),
        "regulation": "IRDAI Master Circular 2024, Para 7.2",
        "category": "tat_sla",
    },
    {
        "title": "TAT - Reimbursement Settlement",
        "text": (
            "IRDAI Master Circular 2024, Para 7.3: Reimbursement claims must be settled within "
            "30 DAYS of receipt of the last necessary document. If the insurer fails to settle "
            "within 30 days due to reasons attributable to the insurer, interest at Bank Rate "
            "plus 2% per annum must be paid on the pending amount."
        ),
        "regulation": "IRDAI Master Circular 2024, Para 7.3",
        "category": "tat_sla",
    },
    {
        "title": "Interest on Delayed Claims",
        "text": (
            "IRDAI Master Circular 2024, Para 7.4: When an insurer delays claim settlement "
            "beyond the mandated 30-day period due to reasons attributable to the insurer, "
            "interest at Bank Rate plus 2% per annum is compulsorily payable. The policyholder "
            "must demand this interest in all appeal letters and ombudsman complaints. "
            "This interest demand is separate from and in addition to the claim amount."
        ),
        "regulation": "IRDAI Master Circular 2024, Para 7.4",
        "category": "interest_delay",
    },
    {
        "title": "GRO Resolution Timeline",
        "text": (
            "IRDAI Master Circular 2024: The Grievance Redressal Officer (GRO) must acknowledge "
            "complaints within 3 working days and resolve them within 15 days of receipt. "
            "If unresolved in 15 days, the insurer must auto-escalate to a senior officer. "
            "After 30 days without resolution, the policyholder may approach the Insurance "
            "Ombudsman without waiting further."
        ),
        "regulation": "IRDAI Master Circular 2024",
        "category": "grievance_redressal",
    },
    {
        "title": "Cashless Denial - Written Reason Required",
        "text": (
            "IRDAI Master Circular 2024, Section B: Insurers and TPAs cannot verbally deny "
            "cashless treatment. All cashless pre-authorisation decisions must be communicated "
            "in writing specifying the exact policy clause or exclusion being invoked. "
            "Verbal denial of cashless treatment is invalid and constitutes deficiency in service. "
            "The insurer cannot cite 'insufficient documents' without specifying exactly which "
            "documents are missing and why they are required."
        ),
        "regulation": "IRDAI Master Circular 2024, Section B",
        "category": "cashless_rights",
    },
    {
        "title": "Document Demand Restrictions",
        "text": (
            "IRDAI Master Circular 2024, Para 8.3: Insurers cannot repeatedly demand documents "
            "already submitted. Each document request must specify the document name, reason "
            "it is required, and deadline for submission. Insurers cannot demand documents from "
            "the policyholder that the hospital or treating doctor is required to provide. "
            "If an insurer cites document deficiency after documents were already submitted, "
            "this constitutes a violation of Para 8.3."
        ),
        "regulation": "IRDAI Master Circular 2024, Para 8.3",
        "category": "document_rights",
    },
    {
        "title": "Customer Information Sheet (CIS) - Mandatory Disclosure",
        "text": (
            "IRDAI Master Circular 2024, Para 4.2: Every insurer must provide a Customer "
            "Information Sheet (CIS) at policy issuance. The CIS must clearly state in simple "
            "language: all inclusions, all exclusions, waiting periods, sub-limits, co-payments, "
            "and key conditions for claim settlement. If the insurer failed to provide a CIS, "
            "this is a regulatory violation. The insurer cannot enforce exclusions that are "
            "not mentioned in the CIS provided to the policyholder."
        ),
        "regulation": "IRDAI Master Circular 2024, Para 4.2",
        "category": "cis_disclosure",
    },
    {
        "title": "Moratorium Period - Pre-Existing Disease",
        "text": (
            "IRDAI (Health Insurance) Regulations 2024, Regulation 8(6): After 5 continuous "
            "years of health insurance coverage, the insurer CANNOT reject a claim on grounds "
            "of non-disclosure of a Pre-Existing Disease (PED). The only exception is if the "
            "insurer can PROVE intentional fraudulent misrepresentation at the time of policy "
            "purchase. The burden of proof lies entirely on the insurer, not the policyholder. "
            "Forgetting to disclose a condition does NOT constitute fraud. The moratorium period "
            "was reduced from 8 years to 5 years in the 2024 regulations. For ported policies, "
            "years of coverage with the previous insurer count toward the moratorium."
        ),
        "regulation": "IRDAI Health Regulations 2024, Regulation 8(6)",
        "category": "moratorium_ped",
    },
    {
        "title": "PED Waiting Period Maximum",
        "text": (
            "IRDAI (Health Insurance) Regulations 2024: The maximum waiting period for "
            "Pre-Existing Diseases (PED) is 3 years (36 months) of continuous coverage. "
            "Any insurer imposing a longer PED waiting period violates IRDAI regulations. "
            "The initial waiting period for any claim (except accidents) is maximum 30 days. "
            "The maximum waiting period for specific named diseases is 2 years (24 months). "
            "Accidents are covered from Day 1 of the policy with no waiting period applicable."
        ),
        "regulation": "IRDAI Health Regulations 2024",
        "category": "waiting_periods",
    },
    {
        "title": "Portability Rights",
        "text": (
            "IRDAI (Health Insurance) Regulations 2024, Regulation 17: A policyholder has the "
            "right to port their health insurance policy to any other IRDAI-registered insurer. "
            "The new insurer must accept the portability application and cannot arbitrarily refuse. "
            "All waiting periods already served with the previous insurer carry forward to the "
            "new insurer — no fresh initial waiting period applies. The portability request must "
            "be submitted 45 days before the policy renewal date. The new insurer cannot increase "
            "premium solely due to portability. Moratorium credits also transfer with the policy."
        ),
        "regulation": "IRDAI Health Regulations 2024, Regulation 17",
        "category": "portability",
    },
    {
        "title": "Deficiency in Service - Consumer Protection Act",
        "text": (
            "Consumer Protection Act 2019, Section 2(11): Insurance claim rejection constitutes "
            "'Deficiency in Service' when the claim is rejected unreasonably or arbitrarily "
            "without valid policy grounds, when settlement is delayed beyond IRDAI-mandated "
            "30-day period, when the insurer provides false or misleading information to reject "
            "a claim, when the insurer fails to process documents within TAT, or when the policy "
            "was mis-sold with misrepresented features. The Consumer Court can award the full "
            "claim amount, interest at 9-12% per annum, compensation for mental agony, and "
            "litigation costs. The E-Daakhil portal (edaakhil.nic.in) enables online filing."
        ),
        "regulation": "Consumer Protection Act 2019, Section 2(11)",
        "category": "consumer_protection",
    },
    {
        "title": "Insurance Ombudsman - Eligibility and Process",
        "text": (
            "Insurance Ombudsman Rules 2017: The Insurance Ombudsman handles complaints for "
            "claim values up to Rs. 50,00,000 (Fifty Lakhs). Filing is completely FREE for "
            "policyholders. The Ombudsman can award the full claim amount plus up to Rs. 5,000 "
            "as costs. The policyholder can approach the Ombudsman if: the insurer rejects the "
            "grievance, or the GRO does not resolve within 30 days, or the policyholder is "
            "unsatisfied with GRO resolution. File online at www.igms.irda.gov.in. "
            "The award is binding on the insurer if the policyholder accepts it. "
            "The complaint must be filed within 1 year of the insurer's final decision."
        ),
        "regulation": "Insurance Ombudsman Rules 2017",
        "category": "ombudsman",
    },
    {
        "title": "Non-Medically Necessary Hospitalisation Disputes",
        "text": (
            "IRDAI Master Circular 2024: When an insurer rejects a claim citing 'non-medically "
            "necessary hospitalisation', the insurer must provide medical justification from "
            "a qualified doctor explaining why the treating doctor's recommendation was wrong. "
            "The insurer cannot simply assert non-necessity without medical evidence. "
            "The policyholder should obtain a letter from the treating doctor confirming medical "
            "necessity. A second opinion from another qualified doctor strengthens the appeal. "
            "This type of rejection is commonly disputed at the Ombudsman level."
        ),
        "regulation": "IRDAI Master Circular 2024",
        "category": "medical_necessity",
    },
    {
        "title": "Room Rent Sub-Limit Proportionate Reduction",
        "text": (
            "IRDAI and policy terms: When a health insurance policy has a room rent sub-limit "
            "(e.g. Rs. 5,000 per day), and the insured occupies a room above this limit, "
            "the insurer proportionately reduces ALL associated medical charges. For example, "
            "if the room rent is Rs. 8,000 but the sub-limit is Rs. 5,000, only 62.5% of all "
            "bills (doctor fees, ICU charges, procedures) will be reimbursed. This is a "
            "high-risk clause. Policyholders should always check the room rent sub-limit before "
            "admission and choose a room within the sub-limit to avoid proportionate reduction."
        ),
        "regulation": "Policy Terms - Room Rent Sub-Limit",
        "category": "sub_limits",
    },
    {
        "title": "Life Insurance Incontestability - Section 45",
        "text": (
            "Insurance Act 1938, Section 45: A life insurance policy cannot be called into "
            "question on any ground after 3 years from the date of issuance, commencement, "
            "or revival of the policy. IRDAI (Life Insurance) Regulations 2023, Regulation 27 "
            "reinforces this incontestability principle. After 3 years, even if there was "
            "non-disclosure, the insurer cannot repudiate the claim unless it can prove "
            "FRAUDULENT misrepresentation with clear evidence. Mere omission or forgetting "
            "to disclose does not constitute fraud for incontestability purposes."
        ),
        "regulation": "Insurance Act 1938, Section 45; IRDAI Life Regs 2023, Reg 27",
        "category": "life_incontestability",
    },
    {
        "title": "Motor Insurance - Surveyor TAT Requirements",
        "text": (
            "IRDAI Motor Insurance Guidelines 2017 and IRDAI (Surveyors and Loss Assessors) "
            "Regulations 2015: For motor insurance claims above Rs. 50,000, a licensed surveyor "
            "must be appointed within 3 working days of claim intimation. The surveyor must "
            "submit the survey report to the insurer within 15 days of completing the survey. "
            "The policyholder has the right to receive a copy of the Survey Report. "
            "If the insurer rejects based on the survey without sharing the report, this "
            "constitutes a violation. Demand the full Survey Report under Regulation 19."
        ),
        "regulation": "IRDAI Motor Guidelines 2017; IRDAI Surveyors Regs 2015, Reg 19",
        "category": "motor_surveyor",
    },
    {
        "title": "Claim Rejection Must Cite Specific Clause",
        "text": (
            "IRDAI Master Circular on Protection of Policyholders Interests 2024: When an "
            "insurer rejects or repudiates a claim, the rejection letter MUST cite the specific "
            "policy clause and/or specific IRDAI regulation that justifies the rejection. "
            "A vague rejection citing general policy terms without specific clause numbers "
            "is insufficient and can be challenged. The rejection letter must also clearly "
            "inform the policyholder of their right to approach the GRO, Ombudsman, and "
            "Consumer Court. Failure to cite specific grounds is itself a regulatory violation."
        ),
        "regulation": "IRDAI Master Circular 2024",
        "category": "rejection_grounds",
    },
]


# ── Embedding Function ────────────────────────────────────────────
async def embed_text(text: str, client: httpx.AsyncClient) -> list[float]:
    resp = await client.post(
        "https://api.jina.ai/v1/embeddings",
        headers={
            "Authorization": f"Bearer {JINA_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "jina-embeddings-v2-base-en",
            "input": [text],
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]


# ── Main Seeding Function ─────────────────────────────────────────
async def seed():
    # Validate config
    if not JINA_API_KEY:
        logger.error("JINA_API_KEY not set. Get your free key at jina.ai")
        sys.exit(1)
    if not QDRANT_URL:
        logger.error("QDRANT_URL not set.")
        sys.exit(1)
    if not QDRANT_API_KEY:
        logger.error("QDRANT_API_KEY not set.")
        sys.exit(1)

    logger.info(f"Seeding {len(IRDAI_CHUNKS)} IRDAI regulation chunks into Qdrant...")
    logger.info(f"Collection: {COLLECTION}")
    logger.info(f"Qdrant URL: {QDRANT_URL}")

    # Connect to Qdrant
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # Ensure collection exists with correct dimensions
    existing = {c.name for c in qdrant.get_collections().collections}
    if COLLECTION not in existing:
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        logger.info(f"Created collection: {COLLECTION}")
    else:
        logger.info(f"Collection already exists: {COLLECTION}")

    # Embed and upsert each chunk
    points = []
    async with httpx.AsyncClient() as http:
        for i, chunk in enumerate(IRDAI_CHUNKS):
            try:
                logger.info(f"Embedding chunk {i+1}/{len(IRDAI_CHUNKS)}: {chunk['title']}")
                vector = await embed_text(chunk["text"], http)

                if not vector:
                    logger.warning(f"Empty vector for chunk {i+1}, skipping")
                    continue

                points.append(PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "text": chunk["text"],
                        "title": chunk["title"],
                        "regulation": chunk["regulation"],
                        "category": chunk["category"],
                        "source": "seed_irdai.py",
                    },
                ))
            except Exception as e:
                logger.error(f"Failed to embed chunk {i+1} ({chunk['title']}): {e}")

    if not points:
        logger.error("No points to upsert — check your Jina API key")
        sys.exit(1)

    # Upsert all points in one batch
    qdrant.upsert(collection_name=COLLECTION, points=points)
    logger.info(f"Successfully seeded {len(points)} regulation chunks into '{COLLECTION}'")
    logger.info("RAG is now active — rejection audits will use vector search instead of hardcoded fallback.")


if __name__ == "__main__":
    asyncio.run(seed())