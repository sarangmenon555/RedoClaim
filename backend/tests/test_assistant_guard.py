import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.assistant.guard import check_answer
from app.services.assistant.ombudsman_lookup import find_offices
from app.services.assistant.planner import _keyword_intents
from app.services.assistant.verified_facts import facts_text, retrieve_facts
from app.services.irdai.consumer_fees import describe, fee_for, forum_for

BAD_VERIFY_ANSWER = """How to verify the insurer's (non-)response and move forward

Check the claim's current status in RedoClaim
Open the RedoClaim app, go to My Claims and look for the latest "Insurer Response" date.
IRDAI (Protection of Policy-holders' Interests) Regulations 2020, Regulation 5.2.1 requires the insurer to reply within 14 calendar days of receiving a grievance.
Use the calculate_deadline tool with rule: "gro_response_tat" to see the exact deadline that has passed.
Determine the appropriate consumer-court forum
| Claim amount (including any interest) | Forum (online) | Typical filing fee* |
| up to Rs 1 crore | District Consumer Disputes Redressal Commission (DCDRC) | Rs 100 - Rs 500 |
| above Rs 1 crore but up to Rs 10 crore | State Consumer Disputes Redressal Commission (SCDRC) | Rs 1,000 - Rs 2,000 |
Online filing steps (e-DCDRC portal)
The IRDAI will forward the matter to the insurer and expect a response within 30 days of the grievance.
Ombudsman: the typical filing window is 30 days from the insurer's final reply.
The insurer must acknowledge the grievance immediately and resolve it within 14 days.
"""

GOOD_ANSWER = """You can file on e-Jagriti (e-jagriti.gov.in).

- Because your premium was Rs. 50,000, the case goes to the District Consumer Disputes Redressal Commission.
- The court fee is nil, since the fee follows the premium and nothing is charged up to Rs. 5 lakh.
- The legal basis is the Consumer Protection Act, 2019, Section 2(11) (deficiency in service).
"""


def _allowed(question, history=""):
    facts = retrieve_facts(question, history)
    return facts_text(facts), facts


def test_guard_removes_known_wrong_content():
    allowed, facts = _allowed("how to verify?", "insurer has not responded e-jagriti 50,000 premium")
    fallback = "- Insurer grievance timeline: the insurer must resolve a grievance within 14 days."
    result = check_answer(BAD_VERIFY_ANSWER, allowed, fallback, "how to verify? 50,000 premium")
    text = result["answer"].lower()
    for banned in ["dcdrc", "5.2.1", "calculate_deadline", "my claims", "insurer response", "|", "within 30 days", "typical filing"]:
        assert banned not in text, f"still present: {banned}"
    assert result["fallback"] is True, "a mostly unverifiable answer should fall back to verified facts"
    assert "14 days" in text, "the verified fallback should be shown"
    assert result["dropped"] >= 5


def test_guard_keeps_a_correct_answer():
    allowed, _ = _allowed("e-jagriti fee for premium 50,000", "")
    result = check_answer(GOOD_ANSWER, allowed, "", "e-jagriti fee for premium 50,000")
    assert result["dropped"] == 0, result["flags"]
    assert "District Consumer Disputes Redressal Commission" in result["answer"]


def test_guard_blocks_unsupported_figures_and_citations():
    allowed, facts = _allowed("cashless approval", "")
    wrong = "The insurer has 3 hours to approve a cashless request under Regulation 12(3)."
    result = check_answer(wrong, allowed, "- Cashless: one hour.", "cashless approval")
    assert result["fallback"] is True
    ok_line = "The insurer must decide within one hour and give discharge authorisation within three hours."
    assert check_answer(ok_line, allowed, "", "cashless approval")["dropped"] == 0


def test_guard_blocks_unverified_addresses():
    allowed, _ = _allowed("ombudsman", "")
    result = check_answer("File at ombudsman-india.example.com today.\nThe Ombudsman limit is Rs. 50 lakh.", allowed, "", "ombudsman")
    assert "example.com" not in result["answer"]
    assert "50 lakh" in result["answer"]


def test_fact_retrieval_picks_the_right_cards():
    assert retrieve_facts("how to verify?", "insurer not responded grievance 14 days")[0]["id"] == "grievance_timeline"
    assert retrieve_facts("what is the e-jagriti fee for 50000 premium")[0]["id"] == "consumer_forum_fee"
    assert retrieve_facts("is cashless approval one hour")[0]["id"] == "cashless"
    assert retrieve_facts("what is the ombudsman limit")[0]["id"] == "ombudsman"


def test_planner_keywords():
    assert "verify_response" in _keyword_intents("how do I verify the insurer has not responded", False)
    assert "ombudsman_contact" in _keyword_intents("address of the ombudsman in Gujarat", False)
    assert "ejagriti_guide" in _keyword_intents("how do I file on e-jagriti", False)
    assert "draft_appeal" not in _keyword_intents("how do I file a consumer court complaint on e-jagriti", False)
    assert "draft_appeal" not in _keyword_intents("How long does the insurer have to resolve my grievance?", False)
    assert "draft_appeal" in _keyword_intents("please draft an appeal letter for me", False)
    assert "general_question" in _keyword_intents("What is the moratorium period in health insurance?", False)
    assert "explain_term" in _keyword_intents("what is subrogation", False)
    assert "general_question" in _keyword_intents("What is the penalty under Regulation 99 of the Health Rules?", False)


def test_fee_and_forum_boundaries():
    assert fee_for(500000) == 0 and fee_for(500001) == 200
    assert fee_for(5000000) == 1000 and fee_for(5000001) == 2000
    assert fee_for(100000000) == 6000 and fee_for(100000001) == 7500
    assert forum_for(5000000) == "district" and forum_for(5000001) == "state" and forum_for(20000001) == "national"
    assert describe(50000)["forum_key"] == "district" and describe(50000)["fee"] == 0


def test_ombudsman_lookup():
    assert [o["center"] for o in find_offices("Gujarat")["offices"]] == ["Ahmedabad"]
    assert [o["center"] for o in find_offices("Navi Mumbai")["offices"]] == ["Thane"]
    assert [o["center"] for o in find_offices("Bangalore")["offices"]] == ["Bengaluru"]
    assert all(o["email"].startswith("oio.") for o in find_offices("Maharashtra")["offices"])


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except AssertionError as exc:
                failed += 1
                print("FAIL", name, exc)
    sys.exit(1 if failed else 0)
