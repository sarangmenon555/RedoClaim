"""
seed_irdai.py — Seed IRDAI regulation texts into Qdrant.
Run once after setup: docker compose exec backend python scripts/seed_irdai.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag.rag_pipeline import upsert_document_chunks, ensure_collections
from app.core.config import settings

# ─── IRDAI REGULATION TEXTS ──────────────────────────────────────────────────
# These are curated summaries of key provisions.
# In production: load full PDFs of IRDAI circulars via OCR pipeline.

IRDAI_REGULATIONS = [
    {
        "id": "master_circular_2024_tat",
        "text": """IRDAI Master Circular on Protection of Policyholders Interests (2024)
TURNAROUND TIMES (TATs) - Mandatory Timelines:

Health Insurance Claims:
- Cashless pre-authorisation: Decision within 1 HOUR of receiving complete documents from hospital
- Cashless final discharge authorisation: Within 3 hours of receiving discharge request
- Reimbursement claim settlement: Within 30 days of receiving all documents
- Claim repudiation: Must provide specific reasons citing exact policy clause and regulation

Non-life claims (Motor/Property):
- Survey completion: Within 3 working days of intimation for claims above Rs. 50,000
- Survey report submission: Within 15 days for claims below Rs. 50 Lakhs
- Claim settlement after survey: Within 30 days

Internal Grievance:
- Acknowledgement: Within 3 working days of receiving complaint
- Resolution by GRO: Within 15 days of complaint receipt
- If not resolved in 15 days: Must escalate to senior officer automatically

Penalty for TAT violation:
- Interest at bank rate + 2% per annum on delayed claim amount
- This interest is mandatory, policyholder can claim it in appeal""",
        "category": "tat_timelines",
        "regulation": "IRDAI Master Circular 2024"
    },
    {
        "id": "master_circular_2024_cashless",
        "text": """IRDAI Master Circular 2024 - Cashless Treatment Rules:

1. RIGHT TO CASHLESS: Policyholder has right to cashless treatment at any network hospital
   - Insurer CANNOT ask policyholder to pay and reimburse if cashless facility exists
   - Pre-authorisation cannot be denied without valid policy-based reason
   
2. DOCUMENT DEMANDS: 
   - Insurer/TPA CANNOT demand documents directly from policyholder that hospital should provide
   - Insurer CANNOT reject claim citing "documents not submitted" if hospital was supposed to submit them
   - Any additional document request must specify exactly which document and why
   
3. DENIAL OF CASHLESS:
   - Must be communicated in writing with specific reason
   - Verbal denials are NOT acceptable
   - Denial must cite specific policy clause
   
4. ABUSE OF CASHLESS:
   - Insurer cannot arbitrarily de-empanel hospitals without notice
   - Minimum 3 months notice required for hospital de-empanelment
   
5. CUSTOMER INFORMATION SHEET (CIS):
   - Insurer MUST provide CIS at policy issuance
   - CIS must list all inclusions and exclusions in simple language
   - Failure to provide CIS = grounds for complaint""",
        "category": "cashless_rights",
        "regulation": "IRDAI Master Circular 2024"
    },
    {
        "id": "health_regs_2024_moratorium",
        "text": """IRDAI (Health Insurance) Regulations 2024 - Moratorium Period:

MORATORIUM PERIOD - KEY PROTECTION:
After 5 YEARS of continuous health insurance coverage with same or ported insurer:
- Insurer CANNOT repudiate (reject/cancel) a claim based on non-disclosure of Pre-Existing Disease (PED)
- EXCEPTION: Only if PROVEN FRAUD or intentional misrepresentation (burden of proof on insurer)

Key points:
- 5 years = 60 months continuous coverage (reduced from 8 years in 2024 reform)
- Continuity includes portability: years with previous insurer count
- Even if policyholder "forgot" to disclose a PED, after 5 years moratorium applies
- Insurer must PROVE fraud (mere suspicion is insufficient)
- Moratorium applies to all health insurance policies issued in India

PORTABILITY RIGHTS:
- Policyholder can port health policy to any other insurer
- New insurer must accept with waiting period credits from previous insurer
- No fresh waiting period for conditions already covered (waiting period exhausted)
- Portability application: 45 days before renewal
- Insurer CANNOT deny portability without documented reason
- Waiting period already served carries forward to new insurer

WAITING PERIOD RULES:
- Initial waiting period: 30 days (no claims except accidents)
- Pre-existing disease waiting period: Maximum 3 years (reduced in 2024 reforms)
- Specific disease waiting periods: Maximum 2 years""",
        "category": "moratorium_portability",
        "regulation": "IRDAI Health Insurance Regulations 2024"
    },
    {
        "id": "ombudsman_rules_2017",
        "text": """Insurance Ombudsman Rules 2017 - Grievance Redressal:

JURISDICTION:
- Claims up to Rs. 50,00,000 (50 Lakhs)
- All types of insurance: life, health, motor, property
- Must be filed within 1 year of insurer's final decision
- Free service - no fee for policyholders

WHO CAN FILE:
- Policyholder, nominee, legal heir, assignee
- Can authorise representative to file on their behalf

HOW TO FILE:
- Online: www.igms.irda.gov.in (Integrated Grievance Management System)
- Physical: Contact nearest Insurance Ombudsman office
- Find ombudsman by state on IRDAI website

PROCESS:
1. File complaint with insurer first (GRO)
2. If not resolved in 30 days OR unsatisfactory reply → file with Ombudsman
3. Ombudsman conducts inquiry, can call both parties
4. Award within 3 months of filing
5. Insurer must comply with award within 30 days

POWERS OF OMBUDSMAN:
- Can award full claim amount
- Can award up to Rs. 5,000 as legal costs
- Award is binding on insurer (if policyholder accepts)
- Policyholder can reject award and go to court

COMMON VALID GROUNDS:
- Partial or total repudiation of claims
- Delay in settlement beyond 30 days
- Failure to issue policy after premium payment
- Non-payment of surrender value
- Dispute regarding premium""",
        "category": "ombudsman_process",
        "regulation": "Insurance Ombudsman Rules 2017"
    },
    {
        "id": "consumer_protection_2019",
        "text": """Consumer Protection Act 2019 - Insurance Claims:

DEFICIENCY IN SERVICE:
Insurance rejection can constitute "Deficiency in Service" including:
- Unreasonable/arbitrary rejection of legitimate claim
- Delay in claim settlement beyond mandated period
- Failure to process documents within TAT
- Misleading information at time of policy sale (mis-selling)

E-DAAKHIL PORTAL:
- Online consumer court filing: edaakhil.nic.in
- Can file complaint entirely online
- Upload all documents digitally
- Pay minimal court fees online
- Receive updates via SMS/email

CONSUMER FORUMS (by claim amount):
- District Commission: Claims up to Rs. 50,00,000 (50 Lakhs)
- State Commission: Claims Rs. 50 Lakhs to Rs. 2,00,00,000 (2 Crores)
- National Commission: Claims above Rs. 2 Crores
- Appeals go to next higher forum within 30 days

IMPORTANT PROVISIONS:
- Limitation period: 2 years from date of cause of action
- Compensation for mental agony and harassment: Can be claimed
- Punitive damages for gross negligence: Available
- Product liability: If policy was defectively designed/sold
- Burden of proof: On service provider (insurer) to prove service was adequate

RELIEF AVAILABLE:
- Full claim amount
- Interest on delayed payment
- Compensation for mental harassment
- Legal costs
- Punitive damages in egregious cases""",
        "category": "consumer_protection",
        "regulation": "Consumer Protection Act 2019"
    },
    {
        "id": "common_rejection_tactics",
        "text": """Common Unfair Claim Rejection Tactics (IRDAI Identified):

1. PRE-EXISTING DISEASE (most common):
   - Rejecting claims citing undisclosed PED without proof
   - IRDAI Position: After 5-year moratorium, cannot reject on PED grounds
   - Counter: Cite moratorium, demand proof of fraudulent concealment

2. NON-STANDARD DOCUMENTS:
   - Rejecting because documents are "not in prescribed format"
   - IRDAI Position: If documents are genuine, format cannot be sole rejection ground
   - Counter: Cite Master Circular clause on document demands

3. POLICY LAPSE:
   - Claiming policy had lapsed when premium was actually paid
   - IRDAI Position: Grace period of 30 days for health policies
   - Counter: Show payment proof, cite grace period rules

4. SUBLIMIT MANIPULATION:
   - Applying sublimits not clearly mentioned in CIS
   - IRDAI Position: Sublimits must be prominently disclosed in CIS
   - Counter: Demand CIS, cite non-disclosure

5. EXPERIMENTAL TREATMENT:
   - Labeling standard treatments as "experimental" to deny
   - IRDAI Position: Treatments approved by medical boards cannot be called experimental
   - Counter: Get treating doctor certificate, cite AYUSH regulations if applicable

6. DELAYED FILING:
   - Claiming policyholder filed claim "too late"
   - IRDAI Position: Delay in filing does not automatically invalidate if genuine reason exists
   - Counter: Provide reason for delay, insurer must prove prejudice due to delay

7. INTERNAL POLICY:
   - Citing "internal policy" not in the actual policy document
   - IRDAI Position: Only policy wordings apply, internal policies cannot override
   - Counter: Demand specific policy clause reference""",
        "category": "rejection_tactics",
        "regulation": "IRDAI Enforcement Observations"
    },
]


async def seed():
    print("Seeding IRDAI regulations into Qdrant...")
    await ensure_collections()

    chunks = []
    for i, reg in enumerate(IRDAI_REGULATIONS):
        chunks.append({
            "text": reg["text"],
            "chunk_index": i,
            "char_start": 0,
            "char_end": len(reg["text"]),
        })

    count = await upsert_document_chunks(
        document_id="irdai_regulations_seed",
        user_id="system",
        chunks=chunks,
        collection=settings.QDRANT_IRDAI_COLLECTION,
    )
    print(f"✅ Seeded {count} IRDAI regulation chunks into Qdrant")
    print("   RAG pipeline will now retrieve relevant regulations during audits")


if __name__ == "__main__":
    asyncio.run(seed())
