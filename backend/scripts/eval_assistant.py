import argparse
import asyncio
import contextlib
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.services.assistant import engine

GLOBAL_BANNED = ["e-dcdrc", "calculate_deadline", "regulation 5.2.1", "my claims page"]

CASES = [
    {"q": "How long does the insurer have to resolve my grievance?", "any": [["14 days"]]},
    {"q": "How do I verify that the insurer has not responded?", "history": [
        {"role": "user", "content": "my insurer has not responded to my grievance"}], "any": [["14 days"], ["bima bharosa"]]},
    {"q": "How to verify?", "history": [
        {"role": "user", "content": "the insurer hasn't responded, I need to file online"},
        {"role": "assistant", "content": "You can file on e-Jagriti."}], "any": [["14 days"], ["timeline"]]},
    {"q": "Which consumer commission hears my case if I paid a premium of 50,000 and what is the fee?", "any": [["district"]], "none": ["1 crore"]},
    {"q": "What is the address of the Insurance Ombudsman in Gujarat?", "any": [["ahmedabad"], ["oio.ahmedabad@cioins.co.in"]]},
    {"q": "How fast must cashless approval be given?", "any": [["one hour", "1 hour"]]},
    {"q": "Within how many days must a reimbursement claim be settled?", "any": [["15 days"]]},
    {"q": "What is the moratorium period in health insurance?", "any": [["60 months", "5 years"]]},
    {"q": "When should I apply to port my health policy?", "any": [["30 days"], ["60 days"]]},
    {"q": "What is the claim limit for the Insurance Ombudsman?", "any": [["50 lakh"]]},
    {"q": "What is the time limit for filing with the Insurance Ombudsman?", "any": [["one year", "1 year"]]},
    {"q": "How long does a motor insurer have to appoint a surveyor?", "any": [["24 hours"]]},
    {"q": "Within how many days must a life insurer settle a death claim?", "any": [["15 days"]]},
    {"q": "What is the free look period?", "any": [["30 days"]]},
    {"q": "Can an insurer reject my claim for missing documents?", "any": [["want of documents", "missing documents", "documents"]]},
    {"q": "Which pages does RedoClaim have?", "any": [["timeline"]]},
    {"q": "What is the penalty under Regulation 99 of the Health Rules?", "none": ["regulation 99 provides", "regulation 99 states"], "any": [["not have", "could not verify", "cannot verify", "unable to verify"]]},
]


class StubDB:
    @contextlib.asynccontextmanager
    async def begin_nested(self):
        yield

    async def get(self, *args):
        return None


async def no_documents(db, user, ids):
    return []


async def run(limit):
    engine.load_documents = no_documents
    user = types.SimpleNamespace(id="eval-user")
    passed = 0
    cases = CASES[:limit] if limit else CASES
    for number, case in enumerate(cases, 1):
        try:
            reply = await engine.handle_message(StubDB(), user, "en", case["q"], [], [], {}, case.get("history", []))
            text = reply["answer"].lower()
        except Exception as exc:
            print(f"[{number:02}] ERROR {case['q'][:60]} -> {exc}")
            continue
        problems = []
        for group in case.get("any", []):
            if not any(option in text for option in group):
                problems.append("missing one of " + " / ".join(group))
        for banned in GLOBAL_BANNED + case.get("none", []):
            if banned in text:
                problems.append("contains '" + banned + "'")
        if problems:
            print(f"[{number:02}] FAIL {case['q'][:70]}\n       " + "; ".join(problems))
            print("       answer: " + reply["answer"][:240].replace("\n", " | "))
        else:
            passed += 1
            print(f"[{number:02}] PASS {case['q'][:70]}")
    print(f"\n{passed}/{len(cases)} passed")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run known-answer questions through the RedoClaim assistant using the configured AI keys")
    parser.add_argument("--limit", type=int, default=0, help="run only the first N questions (saves free-tier quota)")
    args = parser.parse_args()
    sys.exit(asyncio.run(run(args.limit)))
