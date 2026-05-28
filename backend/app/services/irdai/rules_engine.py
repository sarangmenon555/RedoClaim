"""
IRDAI Rules Engine — RedoClaim
Strict legal logic implementing the Hierarchy of Evidence.

Sources:
  - IRDAI Master Circular on Protection of Policyholders Interests (2024)
  - IRDAI (Health Insurance) Regulations 2024
  - Insurance Ombudsman Rules 2017
  - Consumer Protection Act 2019
"""
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class IRDAIRulesEngine:

    # ── TATs from IRDAI Master Circular 2024 ──────────────────────
    TAT_CASHLESS_HOURS          = 1     # cashless pre-auth within 1 hour
    TAT_CLAIM_DAYS              = 30    # final settlement within 30 days
    TAT_GRO_DAYS                = 15    # GRO must resolve within 15 days
    TAT_GRO_ACK_DAYS            = 3     # GRO acknowledgement within 3 working days
    TAT_SURVEY_DAYS             = 3     # survey for claims >50k within 3 days
    MORATORIUM_YEARS            = 5     # 5 continuous years (2024 reform)
    OMBUDSMAN_MAX_RUPEES        = 5_000_000   # ₹50 Lakhs
    INTEREST_RATE_BUFFER        = 2     # Bank Rate + 2% for delayed claims
    EDAAKHIL_TRIGGER_DAYS       = 15    # if insurer silent for 15 days → E-Daakhil

    # ── Step 1: SLA Violation Check ───────────────────────────────
    def check_sla_violations(
        self,
        claim_date: Optional[datetime],
        rejection_date: Optional[datetime],
        grievance_date: Optional[datetime] = None,
        cashless_request_time: Optional[datetime] = None,
        cashless_decision_time: Optional[datetime] = None,
    ) -> dict:
        """
        Step 1 of Hierarchy of Evidence.
        Checks every IRDAI-mandated TAT. Violations = automatic appeal grounds.
        """
        violations = []
        now = datetime.now()

        # 30-day settlement TAT
        if claim_date and rejection_date:
            days_to_settle = (rejection_date - claim_date).days
            if days_to_settle > self.TAT_CLAIM_DAYS:
                excess = days_to_settle - self.TAT_CLAIM_DAYS
                violations.append({
                    "type": "delayed_settlement",
                    "regulation": "IRDAI Master Circular 2024, Para 7.3",
                    "detail": (
                        f"Claim took {days_to_settle} days to process "
                        f"(IRDAI limit: {self.TAT_CLAIM_DAYS} days). "
                        f"Excess: {excess} days."
                    ),
                    "severity": "high",
                    "interest_applicable": True,
                    "interest_note": (
                        f"Insurer liable to pay interest at Bank Rate + {self.INTEREST_RATE_BUFFER}% "
                        f"per annum on the claim amount for {excess} excess days."
                    ),
                    "legal_citation": "IRDAI Master Circular 2024, Para 7.4 — Interest on Delayed Claims",
                })

        # GRO 15-day TAT
        if grievance_date and rejection_date:
            days_since_grievance = (now - grievance_date).days
            if days_since_grievance > self.TAT_GRO_DAYS:
                violations.append({
                    "type": "gro_resolution_overdue",
                    "regulation": "IRDAI Master Circular 2024, Para 10.2",
                    "detail": (
                        f"GRO complaint filed {days_since_grievance} days ago. "
                        f"Resolution mandated within {self.TAT_GRO_DAYS} days."
                    ),
                    "severity": "high",
                    "edaakhil_trigger": days_since_grievance >= self.EDAAKHIL_TRIGGER_DAYS,
                    "legal_citation": "Consumer Protection Act 2019 — E-Daakhil applicable",
                })

        # Cashless 1-hour TAT
        if cashless_request_time and cashless_decision_time:
            hours_taken = (cashless_decision_time - cashless_request_time).seconds / 3600
            if hours_taken > self.TAT_CASHLESS_HOURS:
                violations.append({
                    "type": "cashless_decision_delayed",
                    "regulation": "IRDAI Master Circular 2024, Section B",
                    "detail": (
                        f"Cashless pre-authorisation took {hours_taken:.1f} hours "
                        f"(IRDAI limit: {self.TAT_CASHLESS_HOURS} hour)."
                    ),
                    "severity": "high",
                    "legal_citation": "IRDAI Master Circular 2024 — Cashless Treatment Rights",
                })

        # Compute deadlines from rejection date
        deadlines = {}
        if rejection_date:
            deadlines["gro_deadline"]         = rejection_date + timedelta(days=15)
            deadlines["ombudsman_deadline"]   = rejection_date + timedelta(days=45)
            deadlines["edaakhil_trigger"]     = rejection_date + timedelta(days=15)
            deadlines["consumer_court_limit"] = rejection_date + timedelta(days=365 * 2)
            deadlines["days_left_for_gro"]    = max(0, (deadlines["gro_deadline"] - now).days)
            deadlines["days_left_for_ombudsman"] = max(0, (deadlines["ombudsman_deadline"] - now).days)

        return {
            "sla_violations": violations,
            "violations_found": len(violations),
            "deadlines": deadlines,
            "interest_applicable": any(v.get("interest_applicable") for v in violations),
        }

    # ── Step 2a: Moratorium Check ─────────────────────────────────
    def check_moratorium(
        self,
        policy_start_date: Optional[datetime],
        rejection_reason: str,
    ) -> dict:
        """
        IRDAI Health Insurance Regulations 2024, Regulation 8(6).
        After 5 continuous years, PED-based rejection is INVALID (unless proven fraud).
        """
        if not policy_start_date:
            return {
                "moratorium_applies": False,
                "note": "Policy start date not provided — cannot assess moratorium.",
                "recommendation": "Provide policy inception date for moratorium check.",
            }

        years_covered = (datetime.now() - policy_start_date).days / 365.25
        ped_keywords = [
            "pre-existing", "pre existing", "ped", "non-disclosure",
            "undisclosed", "concealment", "material fact", "prior condition",
            "prior disease", "previous illness", "pre-existing disease",
            "non disclosure", "not disclosed",
        ]
        rejection_lower = rejection_reason.lower()
        is_ped_rejection = any(kw in rejection_lower for kw in ped_keywords)

        if years_covered >= self.MORATORIUM_YEARS and is_ped_rejection:
            return {
                "moratorium_applies": True,
                "years_covered": round(years_covered, 1),
                "regulation": "IRDAI (Health Insurance) Regulations 2024, Regulation 8(6)",
                "argument": (
                    f"The policyholder has {round(years_covered, 1)} years of continuous "
                    f"health insurance coverage. Under IRDAI (Health Insurance) Regulations 2024, "
                    f"Regulation 8(6), after {self.MORATORIUM_YEARS} continuous years, an insurer "
                    f"CANNOT repudiate a claim on the grounds of non-disclosure of a pre-existing "
                    f"disease, EXCEPT in cases of PROVEN fraudulent misrepresentation. "
                    f"The burden of proving fraud lies entirely with the insurer. "
                    f"Mere suspicion, medical opinion, or administrative inference does NOT "
                    f"constitute proof of fraud. This rejection is therefore legally untenable."
                ),
                "strength": "very_strong",
                "counter_to_insurer": (
                    "If insurer claims fraud: demand they provide documentary proof of intentional "
                    "concealment. A medical opinion that the condition 'may have existed before' "
                    "is NOT sufficient proof of fraud under Regulation 8(6)."
                ),
                "portability_note": (
                    "Years of coverage with previous insurers (via portability) count toward "
                    "the 5-year moratorium calculation."
                ),
            }

        if years_covered < self.MORATORIUM_YEARS and is_ped_rejection:
            remaining = self.MORATORIUM_YEARS - years_covered
            return {
                "moratorium_applies": False,
                "years_covered": round(years_covered, 1),
                "years_remaining": round(remaining, 1),
                "note": (
                    f"Moratorium requires {self.MORATORIUM_YEARS} continuous years. "
                    f"Current coverage: {round(years_covered, 1)} years. "
                    f"Moratorium will activate in ~{round(remaining, 1)} more years."
                ),
                "recommendation": (
                    "While moratorium does not yet apply, check if the waiting period "
                    "for this specific condition has been served, and whether the CIS "
                    "clearly disclosed this exclusion."
                ),
            }

        return {
            "moratorium_applies": False,
            "years_covered": round(years_covered, 1),
            "note": "Rejection does not appear to be PED-based; moratorium check not applicable.",
        }

    # ── Step 2b: CIS Violation Check ─────────────────────────────
    def check_cis_violation(
        self,
        rejection_reason: str,
        cis_exclusions: list[str],
    ) -> dict:
        """
        IRDAI Master Circular 2024, Para 4.2.
        Insurer cannot enforce an exclusion not stated in the CIS.
        """
        if not cis_exclusions:
            return {
                "cis_check_done": False,
                "note": "No CIS uploaded. Upload the Customer Information Sheet for this check.",
            }

        rejection_lower = rejection_reason.lower()
        cis_lower = [e.lower() for e in cis_exclusions]
        matched = [e for e in cis_lower if any(word in rejection_lower for word in e.split()[:3])]

        if not matched:
            return {
                "cis_violation": True,
                "regulation": "IRDAI Master Circular 2024, Para 4.2",
                "argument": (
                    "The rejection cites an exclusion that does not appear to be "
                    "disclosed in the Customer Information Sheet (CIS). Under the "
                    "IRDAI Master Circular 2024, Para 4.2, insurers CANNOT enforce "
                    "exclusions that were not clearly disclosed in the CIS provided "
                    "at policy issuance. This is an independent ground for appeal."
                ),
                "severity": "high",
            }
        return {
            "cis_violation": False,
            "note": "The cited exclusion appears to be present in the CIS.",
        }

    # ── Step 2c: Deficiency in Service Check ─────────────────────
    def check_deficiency_in_service(
        self,
        sla_violations: list,
        irdai_violations: list,
        rejection_appears_arbitrary: bool = False,
    ) -> dict:
        """
        Consumer Protection Act 2019, Section 2(11).
        Determines if Deficiency in Service can be alleged.
        """
        reasons = []
        if sla_violations:
            reasons.append("Failure to settle within IRDAI-mandated TAT")
        if irdai_violations:
            reasons.append("Violation of IRDAI Master Circular 2024 provisions")
        if rejection_appears_arbitrary:
            reasons.append("Arbitrary rejection without valid policy/regulatory basis")

        if reasons:
            return {
                "deficiency_in_service": True,
                "legal_basis": "Consumer Protection Act 2019, Section 2(11)",
                "reasons": reasons,
                "statement": (
                    "The acts and omissions of the insurer constitute 'Deficiency in Service' "
                    "as defined under Section 2(11) of the Consumer Protection Act, 2019, "
                    "specifically: " + "; ".join(reasons) + ". "
                    "This entitles the complainant to relief under the Consumer Protection Act, "
                    "including the claim amount, interest, compensation for mental agony, "
                    "and costs of litigation."
                ),
                "product_liability_note": (
                    "If the policy was mis-sold or its features misrepresented at the time of "
                    "sale, an additional Product Liability claim under Section 2(34) of the "
                    "Consumer Protection Act 2019 may also be maintainable."
                ),
            }
        return {"deficiency_in_service": False}

    # ── Step 3: Redressal Route ───────────────────────────────────
    def determine_escalation_path(
        self,
        claim_amount: Optional[float],
        gro_filed: bool = False,
        gro_days_elapsed: int = 0,
        rejection_date: Optional[datetime] = None,
    ) -> dict:
        """
        Step 3 of Hierarchy of Evidence.
        Determines the correct redressal route based on claim amount and status.
        """
        now = datetime.now()
        paths = []

        # Step 1: GRO (always first unless already filed)
        paths.append({
            "step": 1,
            "route": "GRO — Grievance Redressal Officer",
            "regulation": "IRDAI Master Circular 2024, Para 10",
            "deadline": "Within 15 days of rejection",
            "how": (
                "Write to the insurer's GRO. The GRO name and address is on your policy document "
                "and the insurer's website. Send by registered post AND email."
            ),
            "cost": "Free",
            "expected_resolution": "15 days",
            "if_no_response": f"If no response in {self.EDAAKHIL_TRIGGER_DAYS} days → proceed to Step 2",
            "gro_already_filed": gro_filed,
            "gro_overdue": gro_filed and gro_days_elapsed > self.TAT_GRO_DAYS,
        })

        # Step 2: Ombudsman (if claim ≤ ₹50L)
        is_ombudsman_eligible = claim_amount is None or claim_amount <= self.OMBUDSMAN_MAX_RUPEES
        paths.append({
            "step": 2,
            "route": "Insurance Ombudsman",
            "regulation": "Insurance Ombudsman Rules 2017",
            "eligible": is_ombudsman_eligible,
            "max_claim": "₹50,00,000 (50 Lakhs)",
            "deadline": "Within 1 year of insurer's final decision",
            "how": "Online at igms.irda.gov.in | Find your state ombudsman at ecoi.co.in",
            "cost": "Completely FREE",
            "expected_resolution": "3 months",
            "powers": "Can award full claim + ₹5,000 costs. Binding on insurer.",
            "when_to_use": (
                "If GRO fails to resolve within 30 days OR insurer gives unsatisfactory reply"
            ),
            "not_eligible_reason": (
                None if is_ombudsman_eligible
                else f"Claim amount ₹{claim_amount:,.0f} exceeds Ombudsman limit of ₹50 Lakhs"
            ),
        })

        # Step 3: E-Daakhil / Consumer Court
        forum = self._get_consumer_forum(claim_amount)
        edaakhil_applicable = (
            gro_filed and gro_days_elapsed >= self.EDAAKHIL_TRIGGER_DAYS
        ) or (
            rejection_date and (now - rejection_date).days >= self.EDAAKHIL_TRIGGER_DAYS
        )
        paths.append({
            "step": 3,
            "route": f"E-Daakhil — {forum}",
            "regulation": "Consumer Protection Act 2019",
            "legal_basis": "Deficiency in Service — Section 2(11) CPA 2019",
            "deadline": "Within 2 years of rejection date",
            "how": (
                "File online at edaakhil.nic.in — register, fill complaint form, "
                "upload all documents, pay minimal court fee online. "
                "Receive case number and hearing schedule by email/SMS."
            ),
            "cost": "Nominal court fee (₹200 for claims up to ₹5L; varies for higher amounts)",
            "expected_resolution": "3–6 months",
            "edaakhil_now_applicable": edaakhil_applicable,
            "trigger_note": (
                "E-Daakhil is triggered if insurer does NOT respond within 15 days of complaint"
                if edaakhil_applicable else
                f"E-Daakhil applicable if insurer silent for {self.EDAAKHIL_TRIGGER_DAYS} days"
            ),
            "relief_available": [
                "Full claim amount",
                "Interest on delayed payment (9–12% per annum)",
                "Compensation for mental agony and harassment",
                "Cost of litigation",
                "Punitive damages in cases of gross misconduct",
            ],
        })

        return {
            "escalation_path": paths,
            "recommended_immediate_action": self._get_immediate_action(
                gro_filed, gro_days_elapsed, claim_amount, rejection_date
            ),
        }

    def _get_consumer_forum(self, amount: Optional[float]) -> str:
        if not amount:
            return "District Consumer Disputes Redressal Commission"
        if amount <= 5_000_000:
            return "District Consumer Disputes Redressal Commission (claims up to ₹50 Lakhs)"
        elif amount <= 20_000_000:
            return "State Consumer Disputes Redressal Commission (₹50L – ₹2 Crores)"
        return "National Consumer Disputes Redressal Commission (above ₹2 Crores)"

    def _get_immediate_action(
        self,
        gro_filed: bool,
        gro_days_elapsed: int,
        claim_amount: Optional[float],
        rejection_date: Optional[datetime],
    ) -> str:
        now = datetime.now()
        if not gro_filed:
            return (
                "URGENT: File a written GRO complaint with the insurer immediately. "
                "The 15-day GRO window starts from your rejection date."
            )
        if gro_days_elapsed >= self.EDAAKHIL_TRIGGER_DAYS:
            return (
                "GRO deadline exceeded. File immediately with the Insurance Ombudsman "
                "(igms.irda.gov.in) AND/OR E-Daakhil Consumer Court (edaakhil.nic.in)."
            )
        if rejection_date and (now - rejection_date).days > 30:
            return (
                "30-day TAT exceeded. Insurer is liable to pay interest on the claim amount. "
                "Escalate to Ombudsman immediately and demand interest in your appeal."
            )
        return "File GRO complaint and track the 15-day resolution deadline."

    # ── Utilities ─────────────────────────────────────────────────
    def get_rejection_category(self, rejection_text: str) -> str:
        text = rejection_text.lower()
        categories = {
            "pre_existing_disease": [
                "pre-existing", "pre existing", "ped", "prior condition",
                "previously diagnosed", "prior disease",
            ],
            "waiting_period": [
                "waiting period", "initial waiting", "30 day", "90 day", "2 year wait",
                "waiting period not completed",
            ],
            "exclusion": [
                "excluded", "exclusion", "not covered", "policy excludes",
                "falls under exclusion",
            ],
            "documentation": [
                "documents", "documentation", "medical records", "bills not submitted",
                "insufficient documents", "missing documents",
            ],
            "cashless_denial": [
                "cashless not available", "not a network hospital", "cashless denied",
                "pre-auth denied", "pre-authorisation",
            ],
            "fraud": [
                "fraud", "fraudulent", "misrepresentation", "false claim",
                "fabricated", "inflated",
            ],
            "procedure_not_covered": [
                "procedure not covered", "treatment not covered",
                "surgery not covered", "experimental treatment",
            ],
            "sub_limit": [
                "sub limit", "room rent limit", "co-payment", "deductible",
                "sub-limit exceeded",
            ],
        }
        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category
        return "other"

    def portability_advisor(self, policy_clauses: dict, years_covered: float) -> dict:
        """
        Guide user on portability rights when insurer is acting in bad faith.
        IRDAI Health Insurance Regulations 2024, Regulation 17.
        """
        moratorium_credit = min(years_covered, self.MORATORIUM_YEARS)
        ped_waiting_remaining = max(0, 3 - years_covered)

        return {
            "portability_available": True,
            "regulation": "IRDAI (Health Insurance) Regulations 2024, Regulation 17",
            "key_rights": [
                "You can port your policy to any IRDAI-registered insurer",
                "All waiting periods already served carry forward to new insurer",
                f"Moratorium credit: {min(years_covered, 5):.1f} of 5 years served",
                f"PED waiting period remaining at new insurer: {ped_waiting_remaining:.1f} years",
                "New insurer CANNOT impose fresh initial waiting period",
                "Premium cannot be increased solely due to portability",
            ],
            "how_to_port": [
                "Apply 45 days before your policy renewal date",
                "Fill insurer's portability form with previous policy details",
                "New insurer must respond within 15 days",
                "If new insurer refuses without reason, file IRDAI complaint",
            ],
            "when_to_consider_porting": (
                "If current insurer has rejected a legitimate claim, delayed settlement, "
                "or is acting in bad faith — porting preserves all your continuity benefits "
                "while escaping a problematic insurer."
            ),
        }


irdai_engine = IRDAIRulesEngine()
