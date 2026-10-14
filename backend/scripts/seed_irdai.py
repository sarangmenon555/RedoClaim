"""
scripts/seed_irdai.py — Seed Qdrant with IRDAI regulations for RAG.

Run once after setting up your OpenAI API key:
  cd backend
  python scripts/seed_irdai.py

Requirements:
  - OPENAI_API_KEY set in environment or .env file
  - QDRANT_URL and QDRANT_API_KEY set in environment or .env file
  - pip install qdrant-client openai python-dotenv

This populates the `irdai_regulations` Qdrant collection so that
rejection audits use real vector search instead of the hardcoded fallback.
"""
import asyncio
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
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_EMBEDDING_MODEL = os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
EMBED_PROVIDER = "gemini" if GEMINI_API_KEY else ("openai" if OPENAI_API_KEY else None)
QDRANT_URL    = os.environ.get("QDRANT_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
COLLECTION    = os.environ.get("QDRANT_IRDAI_COLLECTION", "irdai_regulations")
EMBEDDING_DIM = 768  # OpenAI text-embedding-3-small, truncated via `dimensions` param
EMBEDDING_MODEL = "text-embedding-3-small"


# ── IRDAI Regulation Chunks ───────────────────────────────────────
# Each entry becomes one vector in Qdrant.
# Add more chunks here as you find more relevant regulation text.
IRDAI_CHUNKS = [
    {
        "title": "TAT - Cashless Pre-Authorisation",
        "text": (
            "IRDAI Master Circular on Health Insurance Business, 2024, Para 15: An insurer must "
            "decide on a request for cashless authorisation immediately, and not later than one "
            "hour from receiving it. Insurers must also provide pre-authorisation to the "
            "policyholder in digital mode, and may arrange dedicated help desks at hospitals. A "
            "decision that comes later than one hour appears inconsistent with the circular."
        ),
        "regulation": "IRDAI Master Circular on Health Insurance Business, 2024, Para 15",
        "category": "tat_sla",
    },
    {
        "title": "TAT - Cashless Final Discharge",
        "text": (
            "IRDAI Master Circular on Health Insurance Business, 2024, Para 16: The insurer "
            "must grant final authorisation within three hours of receiving the hospital's "
            "discharge authorisation request, and the policyholder must not be made to wait to "
            "be discharged. If there is a delay beyond three hours, any additional amount "
            "charged by the hospital is borne by the insurer from the shareholders' fund. If "
            "the policyholder dies during treatment, the insurer must immediately process the "
            "claim settlement and get the mortal remains released from the hospital "
            "immediately."
        ),
        "regulation": "IRDAI Master Circular on Health Insurance Business, 2024, Para 16",
        "category": "tat_sla",
    },
    {
        "title": "TAT - Reimbursement Settlement",
        "text": (
            "IRDAI Master Circular on Protection of Policyholders' Interests, 2024 (Part B, "
            "health insurance): Claims other than cashless must be settled within fifteen days "
            "from submission of the claim. If a claim is not settled within the specified "
            "timelines, the claimant is entitled to interest at Bank Rate plus 2% per annum "
            "from the date of receipt of the claim intimation until the date of payment, and "
            "the insurer must pay this interest on its own (suo moto)."
        ),
        "regulation": "IRDAI Master Circular on Protection of Policyholders' Interests, 2024, Part B",
        "category": "tat_sla",
    },
    {
        "title": "Interest on Delayed Claims",
        "text": (
            "IRDAI Master Circular on Protection of Policyholders' Interests, 2024: For health, "
            "retail general and life insurance claims, if a claim is not settled within the "
            "specified timelines, the claimant is entitled to interest at Bank Rate plus 2% per "
            "annum from the date of receipt of the claim intimation until the date of payment. "
            "The insurer must pay it on its own (suo moto). Ask for this interest in appeal "
            "letters and Ombudsman complaints; it is in addition to the claim amount."
        ),
        "regulation": "IRDAI Master Circular on Protection of Policyholders' Interests, 2024 (claims sections of Parts A, B and C)",
        "category": "interest_delay",
    },
    {
        "title": "GRO Resolution Timeline",
        "text": (
            "IRDAI Master Circular on Protection of Policyholders' Interests, 2024 and IRDAI "
            "Master Circular on Operations and Allied Matters of Insurers, 2024 (clause 24): An "
            "insurer must acknowledge a grievance immediately. It may seek further details from "
            "the complainant only once, within one week. It must resolve the grievance and "
            "issue its final letter of resolution within two weeks (14 days), giving reasons "
            "and reference to the specific policy terms if the complaint is not accepted, and "
            "including the contact details of the concerned Insurance Ombudsman. A grievance "
            "may be closed if the complainant does not reply within eight weeks. Under the "
            "Insurance Ombudsman Rules, 2017 (Rule 14), a policyholder may approach the "
            "Ombudsman if the insurer rejects the representation, does not reply within one "
            "month, or the reply is unsatisfactory."
        ),
        "regulation": "IRDAI Master Circulars, 2024: Protection of Policyholders' Interests; Operations and Allied Matters of Insurers (clause 24)",
        "category": "grievance_redressal",
    },
    {
        "title": "Cashless Authorisation Rules",
        "text": (
            "IRDAI Master Circular on Health Insurance Business, 2024, Paras 15 to 17: An "
            "insurer must decide on a cashless authorisation request immediately, and within "
            "one hour of receiving it. Final authorisation for discharge must be given within "
            "three hours of the hospital's request; if it is delayed beyond three hours, any "
            "additional amount charged by the hospital is borne by the insurer from the "
            "shareholders' fund. No claim may be repudiated without the approval of the "
            "insurer's Product Management Committee or its three-member Claims Review "
            "Committee, and when a claim is repudiated or partly disallowed, the claimant must "
            "be told in full, with reference to the specific terms and conditions of the "
            "policy."
        ),
        "regulation": "IRDAI Master Circular on Health Insurance Business, 2024, Paras 15-17",
        "category": "cashless_rights",
    },
    {
        "title": "Document Demand Restrictions",
        "text": (
            "IRDAI Master Circular on Protection of Policyholders' Interests, 2024: No claim "
            "shall be rejected or closed for want of documents or for delayed intimation of "
            "claim. In health insurance, insurers and TPAs collect the required documents from "
            "the hospital after the claim is intimated, and the policyholder is not required to "
            "submit them. In motor and other retail general insurance, the customer submits "
            "only the documents directly related to the claim, such as the claim form, driving "
            "licence, FIR, and repair bills where cashless is not available."
        ),
        "regulation": "IRDAI Master Circular on Protection of Policyholders' Interests, 2024 (claims sections of Parts A, B and C); IRDAI Master Circular on Health Insurance Business, 2024, Para 17",
        "category": "document_rights",
    },
    {
        "title": "Customer Information Sheet (CIS) - Mandatory Disclosure",
        "text": (
            "IRDAI Master Circular on Health Insurance Business, 2024, Para 4 (and IRDAI Master "
            "Circular on Operations and Allied Matters of Insurers, 2024, clause 40): Insurers "
            "must give every policyholder a Customer Information Sheet (CIS) with the policy "
            "and obtain acknowledgement. It must explain in simple words the type of insurance, "
            "sum insured, coverage, a summary of exclusions, sub-limits, deductibles, waiting "
            "periods, free look period, renewal, migration, portability and moratorium, along "
            "with the claims procedure, policy servicing and grievance redressal, including the "
            "contact details of the Insurance Ombudsman. If no CIS was provided, this appears "
            "non-compliant. The CIS is a summary and does not replace the policy document, but "
            "a rejection that relies on an exclusion or waiting period the CIS did not disclose "
            "may be worth raising in a complaint."
        ),
        "regulation": "IRDAI Master Circular on Health Insurance Business, 2024, Para 4",
        "category": "cis_disclosure",
    },
    {
        "title": "Moratorium Period - Pre-Existing Disease",
        "text": (
            "IRDAI Master Circular on Health Insurance Business, 2024, Para 13: No health "
            "insurance policy or claim can be contested on any ground of non-disclosure or "
            "misrepresentation, except established fraud, after the completion of the "
            "moratorium period of 60 months (5 years) of continuous coverage. Credits gained "
            "under ported and migrated policies count towards the moratorium period. The "
            "moratorium period was reduced from 8 years to 5 years in 2024."
        ),
        "regulation": "IRDAI Master Circular on Health Insurance Business, 2024, Para 13",
        "category": "moratorium_ped",
    },
    {
        "title": "PED Waiting Period Maximum",
        "text": (
            "IRDAI (Insurance Products) Regulations, 2024 (effective 1 April 2024): The waiting "
            "period for pre-existing diseases that the insured person disclosed can be at most "
            "36 months (3 years) of continuous coverage; it was 4 years earlier. A longer "
            "pre-existing disease waiting period appears inconsistent with the regulations. "
            "Insurers commonly apply an initial waiting period of about 30 days, except for "
            "accidents. Reports on the 2024 reforms indicate that waiting periods for specific "
            "named diseases are also capped at 3 years, although many insurers use 2 years, so "
            "check the waiting period stated in the policy document. Credits for waiting "
            "periods already served carry forward on migration or portability, to the extent of "
            "the sum insured."
        ),
        "regulation": "IRDAI (Insurance Products) Regulations, 2024",
        "category": "waiting_periods",
    },
    {
        "title": "Portability Rights",
        "text": (
            "IRDAI Master Circular on Health Insurance Business, 2024, Para 12, and IRDAI "
            "Master Circular on Protection of Policyholders' Interests, 2024 (Part B, Chapter "
            "VI): A policyholder can port a health indemnity policy, with all family members, "
            "to another insurer and transfer the credits gained, to the extent of the sum "
            "insured: no-claim bonus, specific waiting periods, waiting period for pre-existing "
            "diseases and moratorium period. The policyholder must apply to the new insurer at "
            "least 30 days before, and not earlier than 60 days from, the renewal due date; "
            "insurers may also consider a request made within 15 days of the renewal date, "
            "provided there is no break in the policy. The existing insurer must provide the "
            "information sought within 72 hours through the Insurance Information Bureau of "
            "India, and the new insurer must decide and communicate on the proposal within 5 "
            "days of receiving it. No charges are levied for porting in or porting out."
        ),
        "regulation": "IRDAI Master Circular on Health Insurance Business, 2024, Para 12; IRDAI Master Circular on Protection of Policyholders' Interests, 2024, Part B, Chapter VI",
        "category": "portability",
    },
    {
        "title": "Deficiency in Service - Consumer Protection Act, 2019",
        "text": (
            "Consumer Protection Act, 2019, Section 2(11): Insurance claim rejection can "
            "constitute 'Deficiency in Service' when a claim is rejected unreasonably or "
            "arbitrarily without valid policy grounds, when settlement is delayed beyond the "
            "applicable IRDAI timeline, when the insurer gives false or misleading information "
            "to reject a claim, when it fails to process documents within the applicable "
            "timelines, or when the policy was mis-sold with misrepresented features. A "
            "Consumer Commission can award the claim amount, interest, compensation and "
            "litigation costs depending on the facts of the case. The e-Jagriti portal "
            "(e-jagriti.gov.in) enables online filing."
        ),
        "regulation": "Consumer Protection Act, 2019, Section 2(11)",
        "category": "consumer_protection",
    },
    {
        "title": "Insurance Ombudsman - Eligibility and Process",
        "text": (
            "Insurance Ombudsman Rules, 2017 and IRDAI Master Circular on Protection of "
            "Policyholders' Interests, 2024 (Part B): A policyholder who is not satisfied with "
            "the insurer's resolution of a grievance can escalate an unresolved or partly "
            "resolved complaint to the Insurance Ombudsman of competent jurisdiction where the "
            "claim amount is up to Rs. 50 lakh. Filing is free: in person, online at "
            "cioins.co.in/Complaint/Online (Council for Insurance Ombudsmen), or in writing by "
            "post or email with complete details. Under Rule 14 the complaint must generally be "
            "made within one year of the insurer's rejection or unsatisfactory reply, or after "
            "one month has passed without a reply to the written representation. A complaint is "
            "not maintainable on a matter that is pending before, or was decided by, a court, "
            "consumer forum or arbitrator. The insurer must comply with an Ombudsman award "
            "within 30 days of receiving it; if it does not, a penalty of Rs. 5,000 per day is "
            "payable to the complainant, unless the insurer appeals within 30 days. The insurer "
            "must give the Ombudsman's contact details in its grievance resolution letter."
        ),
        "regulation": "Insurance Ombudsman Rules, 2017; IRDAI Master Circular on Protection of Policyholders' Interests, 2024, Part B",
        "category": "ombudsman",
    },
    {
        "title": "Non-Medically Necessary Hospitalisation Disputes",
        "text": (
            "IRDAI Master Circular on Health Insurance Business, 2024, Para 17: When an insurer "
            "rejects a claim citing 'non-medically necessary hospitalisation', the repudiation "
            "must have the approval of the insurer's Product Management Committee or Claims "
            "Review Committee and must be explained with reference to the specific terms and "
            "conditions of the policy. A bare assertion of non-necessity without supporting "
            "medical evidence is open to challenge. The policyholder should obtain a letter "
            "from the treating doctor confirming medical necessity, and a second opinion from "
            "another qualified doctor can strengthen the appeal. This type of rejection is "
            "commonly disputed before the Ombudsman."
        ),
        "regulation": "IRDAI Master Circular on Health Insurance Business, 2024, Para 17",
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
        "title": "Motor and Retail General Insurance - Surveyor and Claim Decision Timelines",
        "text": (
            "IRDAI Master Circular on Protection of Policyholders' Interests, 2024 (Part C, "
            "retail general insurance): A loss of Rs. 50,000 or more under a motor policy (Rs. "
            "1 lakh or more for other retail general policies) must be surveyed by a registered "
            "surveyor and loss assessor. The surveyor must be allocated within 24 hours of the "
            "claim report and must submit the survey report within 15 days of allocation; if "
            "the surveyor is late, Rs. 500 per day is payable to the claimant. The insurer must "
            "decide on the claim within 7 days of receiving the survey report, or after expiry "
            "of 15 days from allocation of the surveyor, whichever is earlier (this timeline "
            "does not apply to property policies on a reinstatement value basis). The insurer "
            "cannot repudiate a claim in full or in part where the breach of a warranty or "
            "condition is not relevant to the nature or circumstances of the loss, or on "
            "account of a delay by the policyholder that has not increased the assessed loss. "
            "No claim may be rejected or closed for want of documents or for delayed "
            "intimation."
        ),
        "regulation": "IRDAI Master Circular on Protection of Policyholders' Interests, 2024, Part C",
        "category": "motor_surveyor",
    },
    {
        "title": "Claim Rejection Must Cite Specific Clause",
        "text": (
            "IRDAI Master Circular on Health Insurance Business, 2024, Para 17, and IRDAI "
            "Master Circular on Protection of Policyholders' Interests, 2024 (Part B): If a "
            "claim is repudiated, rejected or partly disallowed, the details must be "
            "communicated to the claimant in full, with reference to the specific terms and "
            "conditions of the policy document. A vague rejection that does not point to a "
            "specific policy term can be challenged. A health claim cannot be repudiated "
            "without the approval of the insurer's Product Management Committee or Claims "
            "Review Committee. The insurer's reply to a grievance must also include the contact "
            "details of the Insurance Ombudsman where the complaint can be escalated."
        ),
        "regulation": "IRDAI Master Circular on Health Insurance Business, 2024, Para 17; IRDAI Master Circular on Protection of Policyholders' Interests, 2024, Part B",
        "category": "rejection_grounds",
    },
    {
        "title": "Life Insurance - Claim Settlement Timelines",
        "text": (
            "IRDAI Master Circular on Protection of Policyholders' Interests, 2024 (Part A, "
            "life insurance): A death claim must be settled within 15 days of the date of "
            "intimation, except where an investigation is warranted, in which case within 45 "
            "days. A surrender or partial withdrawal request must be processed within 7 days of "
            "receipt, and maturity benefits, survival benefits, annuity payouts and income "
            "benefits are due on the due date. If a claim is not settled within the specified "
            "timelines, interest at Bank Rate plus 2% per annum is payable from the date of "
            "receipt of intimation until payment, on the insurer's own initiative. No claim "
            "shall be rejected or closed for want of documents or for delayed intimation of "
            "claim."
        ),
        "regulation": "IRDAI Master Circular on Protection of Policyholders' Interests, 2024, Part A",
        "category": "tat_sla_life",
    },
    {
        "title": "Consumer Commission - Forum and Filing Fee",
        "text": (
            "Consumer Protection Act, 2019 and the Consumer Protection (Jurisdiction of the "
            "District Commission, the State Commission and the National Commission) Rules, "
            "2021: The forum is decided by the value of the goods or services paid as "
            "consideration, not by the claim amount. The District Commission hears complaints "
            "up to Rs. 50 lakh, the State Commission above Rs. 50 lakh up to Rs. 2 crore, and "
            "the National Commission above Rs. 2 crore. For an insurance policy the "
            "consideration is the premium paid, so most insurance complaints are filed before "
            "the District Commission; the Supreme Court confirmed the consideration-based test "
            "in 2025. The filing fee also depends on the value paid as consideration: nil up to "
            "Rs. 5 lakh; Rs. 200 above Rs. 5 lakh up to Rs. 10 lakh; Rs. 400 above Rs. 10 lakh "
            "up to Rs. 20 lakh; Rs. 1,000 above Rs. 20 lakh up to Rs. 50 lakh; Rs. 2,000 above "
            "Rs. 50 lakh up to Rs. 1 crore; Rs. 2,500 above Rs. 1 crore up to Rs. 2 crore; Rs. "
            "3,000 above Rs. 2 crore up to Rs. 4 crore; Rs. 4,000 above Rs. 4 crore up to Rs. 6 "
            "crore; Rs. 5,000 above Rs. 6 crore up to Rs. 8 crore; Rs. 6,000 above Rs. 8 crore "
            "up to Rs. 10 crore; Rs. 7,500 above Rs. 10 crore. Fees are paid online on "
            "e-Jagriti."
        ),
        "regulation": "Consumer Protection Act, 2019; Consumer Protection (Jurisdiction) Rules, 2021",
        "category": "consumer_forum_fee",
    },
]


# ── Embedding Function ────────────────────────────────────────────
async def embed_text(text: str, client: "AsyncOpenAI") -> list[float]:
    if EMBED_PROVIDER == "gemini":
        resp = await client.embeddings.create(
            model=GEMINI_EMBEDDING_MODEL,
            input=text,
            dimensions=EMBEDDING_DIM,
        )
        vector = list(resp.data[0].embedding)
        norm = sum(x * x for x in vector) ** 0.5
        return [x / norm for x in vector] if norm else vector
    resp = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        dimensions=EMBEDDING_DIM,
    )
    return resp.data[0].embedding


# ── Main Seeding Function ─────────────────────────────────────────
async def seed():
    # Validate config
    if EMBED_PROVIDER is None:
        logger.error("Set GEMINI_API_KEY (preferred, same as the app) or OPENAI_API_KEY in .env")
        sys.exit(1)
    logger.info(f"Embedding provider: {EMBED_PROVIDER}")
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
    from openai import AsyncOpenAI
    points = []
    if EMBED_PROVIDER == "gemini":
        openai_client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url=GEMINI_BASE_URL)
    else:
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    for i, chunk in enumerate(IRDAI_CHUNKS):
            try:
                logger.info(f"Embedding chunk {i+1}/{len(IRDAI_CHUNKS)}: {chunk['title']}")
                vector = await embed_text(chunk["text"], openai_client)

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
        logger.error(f"No points to upsert — check your {EMBED_PROVIDER} API key")
        sys.exit(1)

    # Upsert all points in one batch
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue, FilterSelector
    try:
        qdrant.create_payload_index(collection_name=COLLECTION, field_name="source", field_schema="keyword")
    except Exception as e:
        logger.warning(f"Could not create payload index on 'source': {e}")
    try:
        qdrant.delete(
            collection_name=COLLECTION,
            points_selector=FilterSelector(
                filter=Filter(must=[FieldCondition(key="source", match=MatchValue(value="seed_irdai.py"))])
            ),
        )
    except Exception as e:
        logger.warning(f"Could not clear earlier seed points (fine on a fresh collection): {e}")
    qdrant.upsert(collection_name=COLLECTION, points=points)
    logger.info(f"Successfully seeded {len(points)} regulation chunks into '{COLLECTION}'")
    logger.info("RAG is now active — rejection audits will use vector search instead of hardcoded fallback.")


if __name__ == "__main__":
    asyncio.run(seed())