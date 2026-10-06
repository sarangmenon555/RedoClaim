"""
IRDAI Rules Engine — RedoClaim
Structured evidence-based analysis: timeline and TAT analysis, potential regulatory
inconsistencies, and redressal route. Outputs are AI-assisted references for user
review and are not official legal or regulatory determinations.

Sources:
  - IRDAI Master Circular on Protection of Policyholders Interests (2024)
  - IRDAI (Health Insurance) Regulations 2024
  - Insurance Ombudsman Rules 2017
  - Consumer Protection Act, 2019
"""
from datetime import datetime, timedelta
from typing import Optional
import logging

from app.services.irdai.timeline_model import (
    build_timeline, naive, TAT_BREACH_CAVEAT, GRO_RESPONSE_TAT_DAYS,
    OMBUDSMAN_CONDITIONAL_NOTE, CONSUMER_LAW_NOTE, GRO_FILING_NOTE,
)

logger = logging.getLogger(__name__)


class IRDAIRulesEngine:

    # ── TATs from IRDAI Master Circular 2024 ──────────────────────
    TAT_CASHLESS_HOURS          = 1     # cashless pre-auth within 1 hour
    TAT_CLAIM_DAYS              = 30    # reference timeline used only with its stated basis; not a universal deadline
    TAT_GRO_DAYS                = 15    # GRO must resolve within 15 days
    TAT_GRO_ACK_DAYS            = 3     # GRO acknowledgement within 3 working days
    TAT_SURVEY_DAYS             = 3     # survey for claims >50k within 3 days
    MORATORIUM_YEARS            = 5     # 5 continuous years (2024 reform)
    MORATORIUM_MONTHS           = 60    # the same period, as IRDAI material states it: 60 continuous months
    OMBUDSMAN_MAX_RUPEES        = 5_000_000   # ₹50 Lakhs
    INTEREST_RATE_BUFFER        = 2     # Bank Rate + 2% for delayed claims
    EJAGRITI_TRIGGER_DAYS       = 15    # if insurer silent for 15 days → e-Jagriti

    # ── Step 1: Timeline & TAT Analysis ───────────────────────────
    def check_sla_violations(
        self,
        claim_date: Optional[datetime],
        rejection_date: Optional[datetime],
        grievance_date: Optional[datetime] = None,
        cashless_request_time: Optional[datetime] = None,
        cashless_decision_time: Optional[datetime] = None,
    ) -> dict:
        """
        Step 1: Timeline & TAT analysis.
        Compares documented dates with the applicable timeline for each event and
        reports where the documented dates appear inconsistent with it. The applicable
        timeline and its basis are returned with every finding.
        """
        violations = []
        now = datetime.now()

        if claim_date and rejection_date:
            days_to_settle = (rejection_date - claim_date).days
            if days_to_settle > self.TAT_CLAIM_DAYS:
                excess = days_to_settle - self.TAT_CLAIM_DAYS
                violations.append({
                    "type": "settlement_timeline_inconsistency",
                    "regulation": "IRDAI Master Circular on Health Insurance, 2024 (settlement timeline)",
                    "applicable_timeline": f"{self.TAT_CLAIM_DAYS} days",
                    "basis": "Claim settlement timeline referenced in the IRDAI Master Circular on Health Insurance, 2024; the period runs from the applicable event, such as receipt of the last necessary document. Verify against the primary source.",
                    "detail": (
                        f"The documented dates show {days_to_settle} days between the claim date and the decision. "
                        f"Applicable timeline: {self.TAT_CLAIM_DAYS} days, subject to the start event stated in the basis. "
                        f"This appears to be {excess} days longer than that timeline and should be checked against the actual start event."
                    ),
                    "severity": "medium",
                    "interest_applicable": True,
                    "interest_note": (
                        f"If the delay is confirmed against the applicable provision, interest may be claimable at Bank Rate + {self.INTEREST_RATE_BUFFER}% "
                        f"per annum for the excess period. Verify the current provision before relying on this."
                    ),
                    "legal_citation": "IRDAI Master Circular on Health Insurance, 2024 — provisions on interest for delayed claim settlement (verify paragraph in primary source)",
                })

        # Insurer grievance-resolution TAT (a turnaround the INSURER must meet).
        # Note: the date the grievance was filed is an EVENT, not a deadline.
        if grievance_date:
            grievance_naive = naive(grievance_date)
            days_since_grievance = (now - grievance_naive).days
            if days_since_grievance > self.TAT_GRO_DAYS:
                violations.append({
                    "type": "gro_timeline_inconsistency",
                    "regulation": "IRDAI grievance redressal provisions (verify paragraph in primary source)",
                    "applicable_timeline": f"approximately {self.TAT_GRO_DAYS} days from receipt",
                    "basis": "Grievance resolution timeline referenced in IRDAI / Bima Bharosa grievance material (some IRDAI text states 14 days for the decision); verify the current period for your insurer and complaint channel.",
                    "detail": (
                        f"The grievance was filed {days_since_grievance} days ago. "
                        f"Applicable insurer turnaround: approximately {self.TAT_GRO_DAYS} days from receipt. "
                        f"No resolution is documented within that timeline."
                    ),
                    "severity": "medium",
                    "ejagriti_trigger": days_since_grievance >= self.EJAGRITI_TRIGGER_DAYS,
                    "legal_citation": "Consumer Protection Act, 2019 - e-Jagriti may be an available forum",
                })

        # Cashless 1-hour pre-authorisation TAT.
        # Reported as POTENTIAL TAT non-compliance - never as proof the cashless
        # decision itself is invalid.
        if cashless_request_time and cashless_decision_time:
            hours_taken = (naive(cashless_decision_time) - naive(cashless_request_time)).total_seconds() / 3600
            if hours_taken > self.TAT_CASHLESS_HOURS:
                violations.append({
                    "type": "cashless_tat_potential_non_compliance",
                    "regulation": "IRDAI Master Circular on Health Insurance, 2024 (cashless authorisation timeline)",
                    "applicable_timeline": f"{self.TAT_CASHLESS_HOURS} hour",
                    "basis": "Cashless pre-authorisation timeline in IRDAI health-insurance material (decision immediately and not later than one hour); verify against the primary source.",
                    "detail": (
                        f"Potential TAT non-compliance: the documented times show the cashless "
                        f"pre-authorisation decision took {hours_taken:.1f} hours against an applicable "
                        f"timeline of {self.TAT_CASHLESS_HOURS} hour. This may warrant clarification or "
                        f"grievance escalation. {TAT_BREACH_CAVEAT}"
                    ),
                    "severity": "medium",
                    "does_not_establish_invalidity": True,
                    "legal_citation": "IRDAI Master Circular on Health Insurance, 2024 - cashless treatment provisions",
                })

        # Timeline model: events, insurer TATs, conditional routes and limitation
        # windows are kept separate. See timeline_model.py.
        deadlines = build_timeline(
            rejection_date=rejection_date,
            grievance_date=grievance_date,
            now=now,
        )

        return {
            "sla_violations": violations,
            "violations_found": len(violations),
            "deadlines": deadlines,
            "timeline_items": deadlines.get("timeline_items", []),
            "timeline_model_version": deadlines.get("timeline_model_version"),
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

        policy_start_date = naive(policy_start_date)
        years_covered = (datetime.now() - policy_start_date).days / 365.25
        months_covered = round(years_covered * 12, 1)
        ped_keywords = [
            "pre-existing", "pre existing", "ped", "non-disclosure",
            "undisclosed", "concealment", "material fact", "prior condition",
            "prior disease", "previous illness", "pre-existing disease",
            "non disclosure", "not disclosed",
        ]
        rejection_lower = rejection_reason.lower()
        is_ped_rejection = any(kw in rejection_lower for kw in ped_keywords)
        label = f"{self.MORATORIUM_MONTHS} continuous months"

        if years_covered >= self.MORATORIUM_YEARS and is_ped_rejection:
            return {
                "moratorium_applies": True,
                "years_covered": round(years_covered, 1),
                "months_covered": months_covered,
                "moratorium_period": label,
                "regulation": "IRDAI (Health Insurance) Regulations 2024, Regulation 8(6)",
                "argument": (
                    f"The policy records about {months_covered:.0f} months of coverage. IRDAI material describes "
                    f"the moratorium as {label}. After that period, an insurer generally cannot "
                    f"repudiate a claim on the grounds of non-disclosure of a pre-existing "
                    f"disease, except in cases of proven fraudulent misrepresentation. "
                    f"The burden of proving fraud lies with the insurer, and mere suspicion or "
                    f"inference is generally not enough. If the coverage really has been continuous, "
                    f"this rejection ground may warrant review. Confirm continuity and the exact "
                    f"provision before relying on it."
                ),
                "strength": "strong_if_verified",
                "counter_to_insurer": (
                    "If the insurer alleges fraud, you can ask for the documentary proof of intentional "
                    "concealment. A medical opinion that the condition 'may have existed before' "
                    "is generally not proof of fraud - verify the provision."
                ),
                "portability_note": (
                    f"Coverage with previous insurers (via portability) can count toward "
                    f"the {label} - confirm continuity with your policy history."
                ),
            }

        if years_covered < self.MORATORIUM_YEARS and is_ped_rejection:
            remaining_months = max(0.0, self.MORATORIUM_MONTHS - months_covered)
            return {
                "moratorium_applies": False,
                "years_covered": round(years_covered, 1),
                "months_covered": months_covered,
                "years_remaining": round(self.MORATORIUM_YEARS - years_covered, 1),
                "moratorium_period": label,
                "note": (
                    f"The moratorium requires {label}. "
                    f"Coverage on record: about {months_covered:.0f} months. "
                    f"About {remaining_months:.0f} more months would be needed."
                ),
                "recommendation": (
                    "While the moratorium does not yet apply, check whether the waiting period "
                    "for this specific condition has been served, and whether the CIS "
                    "clearly disclosed this exclusion."
                ),
            }

        return {
            "moratorium_applies": False,
            "years_covered": round(years_covered, 1),
            "months_covered": months_covered,
            "moratorium_period": label,
            "note": "Rejection does not appear to be PED-based; moratorium check not applicable.",
        }

    # ── Step 2b: CIS Consistency Check ────────────────────────────
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
                    "disclosed in the Customer Information Sheet (CIS) that was uploaded. "
                    "The IRDAI Master Circular on Health Insurance, 2024 refers to the CIS as the summary of "
                    "inclusions and exclusions provided at policy issuance. This is a potential "
                    "inconsistency the user may wish to raise; verify the CIS and the provision in the primary source."
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
        evidence_status: str = "sufficient",
    ) -> dict:
        """
        Consumer Protection Act, 2019, Section 2(11).
        Indicates whether a Deficiency in Service allegation could be considered.
        """
        if evidence_status == "insufficient":
            return {
                "deficiency_in_service": False,
                "withheld_reason": (
                    "Insufficient evidence: no legal classification is made until the missing "
                    "documents are obtained and reviewed."
                ),
            }
        reasons = []
        if sla_violations:
            reasons.append("Documented dates that appear inconsistent with the applicable timeline")
        if irdai_violations:
            reasons.append("Potential inconsistency with IRDAI Master Circular provisions")
        if rejection_appears_arbitrary:
            reasons.append("Arbitrary rejection without valid policy/regulatory basis")

        if reasons:
            return {
                "deficiency_in_service": True,
                "legal_basis": "Consumer Protection Act, 2019, Section 2(11)",
                "reasons": reasons,
                "statement": (
                    "The complainant may allege 'Deficiency in Service' as defined under "
                    "Section 2(11) of the Consumer Protection Act, 2019, "
                    "on the following grounds: " + "; ".join(reasons) + ". "
                    "Whether this is established is for the relevant forum to decide. "
                    "Relief that may be sought under the Consumer Protection Act, 2019 includes "
                    "the claim amount, interest, compensation and costs."
                ),
                "product_liability_note": (
                    "If the policy was mis-sold or its features misrepresented at the time of "
                    "sale, an additional Product Liability claim under Section 2(34) of the "
                    "Consumer Protection Act, 2019 may also be maintainable."
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
        Step 3: Redressal route.
        Suggests a redressal route based on claim amount and status.
        """
        now = datetime.now()
        rejection_date = naive(rejection_date)
        paths = []

        # Step 1: GRO (always first unless already filed)
        paths.append({
            "step": 1,
            "route": "GRO — Grievance Redressal Officer",
            "regulation": "IRDAI Master Circular 2024, Para 10",
            "deadline": "No specific filing deadline established from the information provided; the insurer's response turnaround is approximately 15 days from receipt (verify with your insurer's grievance policy)",
            "how": (
                "Write to the insurer's GRO. The GRO name and address is on your policy document "
                "and the insurer's website. Send by registered post AND email."
            ),
            "cost": "Free",
            "expected_resolution": "As per the insurer's grievance timeline",
            "if_no_response": "If there is no response within the applicable timeline, consider Step 2",
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
            "deadline": "Eligibility and time limits depend on the applicable Ombudsman rules - generally within one year of the relevant rejection/decision or expiry of the applicable insurer-response period, subject to eligibility requirements",
            "how": "Online at igms.irda.gov.in | Find your state ombudsman at ecoi.co.in",
            "cost": "Completely FREE",
            "expected_resolution": "3 months",
            "powers": "Can award full claim + ₹5,000 costs. Binding on insurer.",
            "when_to_use": (
                "If the grievance is not resolved within the applicable timeline, is rejected, or the reply is unsatisfactory. "
                "Check the eligibility conditions in the Insurance Ombudsman Rules, 2017."
            ),
            "not_eligible_reason": (
                None if is_ombudsman_eligible
                else f"Claim amount ₹{claim_amount:,.0f} exceeds Ombudsman limit of ₹50 Lakhs"
            ),
        })

        # Step 3: e-Jagriti / Consumer Court
        forum = self._get_consumer_forum(claim_amount)
        ejagriti_applicable = (
            gro_filed and gro_days_elapsed >= self.EJAGRITI_TRIGGER_DAYS
        ) or (
            rejection_date and (now - rejection_date).days >= self.EJAGRITI_TRIGGER_DAYS
        )
        paths.append({
            "step": 3,
            "route": f"e-Jagriti — {forum}",
            "regulation": "Consumer Protection Act, 2019",
            "legal_basis": "Deficiency in Service — Section 2(11) CPA 2019",
            "deadline": "Consumer-law limitation may apply; it depends on the cause of action and legal context - obtain appropriate legal guidance rather than relying on an estimate",
            "how": (
                "File online at e-jagriti.gov.in — register, fill complaint form, "
                "upload all documents, pay minimal court fee online. "
                "Receive case number and hearing schedule by email/SMS."
            ),
            "cost": "Nominal court fee (₹200 for claims up to ₹5L; varies for higher amounts)",
            "expected_resolution": "3–6 months",
            "ejagriti_now_applicable": ejagriti_applicable,
            "trigger_note": (
                "e-Jagriti may be considered if the insurer has not responded within the applicable grievance timeline"
                if ejagriti_applicable else
                "e-Jagriti may be considered if the insurer does not respond within the applicable grievance timeline"
            ),
            "relief_available": [
                "Full claim amount",
                "Interest on delayed payment, as the forum may decide",
                "Compensation, as the forum may decide",
                "Cost of litigation, as the forum may decide",
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
        rejection_date = naive(rejection_date)
        if not gro_filed:
            return (
                "Consider filing a written grievance with the insurer's GRO soon. "
                "Check the insurer's grievance policy for the applicable timeline."
            )
        if gro_days_elapsed >= self.EJAGRITI_TRIGGER_DAYS:
            return (
                "The applicable grievance timeline appears to have passed without resolution. Consider the Insurance Ombudsman "
                "and/or e-Jagriti (e-jagriti.gov.in), after verifying eligibility."
            )
        if rejection_date and (now - rejection_date).days > 30:
            return (
                "The documented dates may indicate a delay beyond the applicable settlement timeline. "
                "Verify the timeline and its basis; if it is confirmed, you may request interest in your appeal."
            )
        return "File a grievance with the insurer and track the applicable resolution timeline."

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
                f"Moratorium credit: about {min(years_covered, 5) * 12:.0f} of {self.MORATORIUM_MONTHS} continuous months served",
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
