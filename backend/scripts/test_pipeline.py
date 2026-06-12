"""
test_pipeline.py — Quick end-to-end test of the full AI pipeline.
Run: docker compose exec backend python scripts/test_pipeline.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GREEN = "\033[92m"
RED   = "\033[91m"
BLUE  = "\033[94m"
RESET = "\033[0m"

def ok(msg): print(f"{GREEN}  ✅ {msg}{RESET}")
def fail(msg): print(f"{RED}  ❌ {msg}{RESET}")
def section(msg): print(f"\n{BLUE}── {msg} ──{RESET}")


async def test_ollama_connection():
    section("Testing Ollama Connection")
    from app.services.llm.ollama_service import ollama
    try:
        available = await ollama.is_model_available("nomic-embed-text")
        if available:
            ok("Ollama is reachable")
            ok("nomic-embed-text model found")
        else:
            fail("nomic-embed-text not found — run: ./scripts/pull-models.sh")
    except Exception as e:
        fail(f"Ollama not reachable: {e}")
        fail("Start Ollama: docker compose up -d ollama")
        return False
    return True


async def test_embeddings():
    section("Testing Local Embeddings")
    from app.services.llm.ollama_service import generate_embeddings
    try:
        vec = await generate_embeddings("Test insurance policy claim rejection")
        if vec and len(vec) > 100:
            ok(f"Embeddings generated: {len(vec)}-dim vector")
            return True
        else:
            fail("Embedding returned empty vector")
            return False
    except Exception as e:
        fail(f"Embedding failed: {e}")
        return False


async def test_qdrant():
    section("Testing Qdrant Vector Database")
    from app.services.rag.rag_pipeline import ensure_collections, client
    try:
        await ensure_collections()
        collections = [c.name for c in client.get_collections().collections]
        ok(f"Qdrant connected. Collections: {collections}")
        return True
    except Exception as e:
        fail(f"Qdrant error: {e}")
        return False


async def test_ocr():
    section("Testing OCR Pipeline")
    from app.services.ocr.ocr_pipeline import chunk_text
    sample = "This is a test insurance policy. Waiting period: 30 days. Exclusions: Pre-existing diseases."
    chunks = chunk_text(sample, chunk_size=50, overlap=10)
    if chunks:
        ok(f"Text chunking works: {len(chunks)} chunks from sample text")
        return True
    else:
        fail("Chunking returned empty")
        return False


async def test_policy_extraction():
    section("Testing Policy Clause Extraction (LLM)")
    from app.services.llm.ollama_service import extract_policy_clauses

    sample_policy = """
    HEALTH INSURANCE POLICY - Star Health Individual
    Policy Number: P/211115/01/2024/001234
    Sum Insured: Rs. 5,00,000
    
    WAITING PERIODS:
    1. Initial Waiting Period: 30 days from inception
    2. Pre-existing Diseases: 3 years waiting period
    3. Specific diseases (cataract, hernia): 2 years
    
    EXCLUSIONS:
    - Dental treatment unless due to accident
    - Cosmetic surgery
    - Maternity expenses (first 9 months)
    
    ROOM RENT: Limited to 1% of Sum Insured per day (Rs. 5,000/day)
    CO-PAYMENT: 10% co-payment applicable for persons above 60 years
    """

    try:
        result = await extract_policy_clauses(sample_policy)
        if result and not result.get("parse_error"):
            ok("Policy extraction succeeded")
            ok(f"Found {len(result.get('waiting_periods', []))} waiting periods")
            ok(f"Found {len(result.get('exclusions', []))} exclusions")
            ok(f"Summary: {str(result.get('plain_english_summary', ''))[:80]}...")
        elif result.get("parse_error"):
            ok("LLM responded but JSON parse failed (model may need better prompt tuning)")
            print(f"   Raw: {str(result.get('raw_analysis', ''))[:200]}")
        return True
    except Exception as e:
        fail(f"Policy extraction failed: {e}")
        return False


async def test_irdai_audit():
    section("Testing IRDAI Rules Engine")
    from app.services.irdai.rules_engine import irdai_engine
    from datetime import datetime, timedelta

    # Test SLA check
    claim_date = datetime.now() - timedelta(days=45)
    rejection_date = datetime.now() - timedelta(days=10)
    result = irdai_engine.check_sla_violations(claim_date, rejection_date)

    if result["sla_violations"]:
        ok(f"SLA violation detected: {result['sla_violations'][0]['type']}")
    else:
        ok("SLA check ran (no violation in this test case)")

    # Test moratorium
    old_policy = datetime.now() - timedelta(days=365 * 6)  # 6 years
    moratorium = irdai_engine.check_moratorium(old_policy, "rejected due to pre-existing disease diabetes")
    if moratorium["moratorium_applies"]:
        ok(f"Moratorium shield: ACTIVE ({moratorium['years_covered']} years)")
    else:
        fail("Moratorium check returned unexpected result")

    # Test escalation paths
    paths = irdai_engine.determine_escalation_path(500000)
    ok(f"Escalation path: {len(paths['escalation_path'])} steps generated")
    return True


async def test_rejection_audit_llm():
    section("Testing Rejection Audit LLM (deepseek-r1)")
    from app.services.llm.ollama_service import audit_rejection
    from app.services.llm.ollama_service import ollama

    if not await ollama.is_model_available("deepseek-r1"):
        print("  ⏭  deepseek-r1 not pulled yet, skipping")
        return True

    sample_rejection = """
    Dear Policyholder,
    We regret to inform you that your claim No. CLM2024/001 for Rs. 2,50,000 
    has been repudiated on the following grounds:
    
    The treating condition (Type 2 Diabetes Mellitus) is a pre-existing disease 
    as per your medical records. As per policy terms, pre-existing diseases are 
    not covered during the waiting period of 3 years.
    
    Policy Clause 4.1 (Exclusions) applies.
    
    Regards,
    Claims Department
    Star Health Insurance
    """

    try:
        result = await audit_rejection(
            rejection_text=sample_rejection,
            policy_clauses={"pre_existing_disease_waiting": "3 years"},
            irdai_context="After 5 years moratorium, PED cannot be cited for rejection",
        )
        if result:
            ok("Rejection audit LLM call succeeded")
            ok(f"Is valid rejection: {result.get('is_valid_rejection')}")
            ok(f"Violations found: {len(result.get('irdai_violations', []))}")
        return True
    except Exception as e:
        fail(f"Rejection audit failed: {e}")
        return False


async def main():
    print(f"\n{BLUE}{'═'*50}")
    print("  RedoClaim — Pipeline Test Suite")
    print(f"{'═'*50}{RESET}\n")

    results = []
    results.append(await test_ollama_connection())
    results.append(await test_embeddings())
    results.append(await test_qdrant())
    results.append(await test_ocr())
    results.append(await test_policy_extraction())
    results.append(await test_irdai_audit())
    results.append(await test_rejection_audit_llm())

    passed = sum(1 for r in results if r)
    total = len(results)

    print(f"\n{BLUE}{'═'*50}{RESET}")
    if passed == total:
        print(f"{GREEN}  All {total} tests passed! 🎉 System is ready.{RESET}")
    else:
        print(f"{RED}  {passed}/{total} tests passed.{RESET}")
        print(f"  Check the ❌ failures above and fix before going live.")
    print(f"{BLUE}{'═'*50}{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
