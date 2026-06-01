"""
Motor & Life Insurance IRDAI Rules Engine — RedoClaim

Sources:
  - IRDAI (Motor Insurance) Guidelines 2017 & Amendments
  - IRDAI Motor Insurance Service Provider (MISP) Guidelines 2017
  - Insurance Regulatory and Development Authority of India Act 1999
  - Motor Vehicles Act 1988 (MV Act)
  - IRDAI (Life Insurance) Regulations 2023
  - IRDAI Master Circular on Protection of Policyholders Interests (2024)
  - Insurance Ombudsman Rules 2017
  - Consumer Protection Act 2019
"""
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MotorInsuranceRulesEngine:
    """
    IRDAI-compliant rules for motor insurance claim rejection analysis.
    Covers Own Damage (OD) and Third-Party (TP) claims.
    """

    # ── TATs from IRDAI Master Circular 2024 ──────────────────────
    TAT_SURVEY_HOURS = 48           # Surveyor appointment within 48 hours of intimation
    TAT_SURVEY_REPORT_DAYS = 30     # Final survey report within 30 days
    TAT_CLAIM_SETTLEMENT_DAYS = 30  # Final settlement within 30 days of survey report
    TAT_GRO_DAYS = 15
    OMBUDSMAN_MAX_RUPEES = 5_000_000

    # ── Step 1: SLA Violation Check (Motor) ──────────────────────
    def check_sla_violations(
        self,
        claim_intimation_date: Optional[datetime],
        survey_appointment_date: Optional[datetime],
        survey_report_date: Optional[datetime],
        rejection_date: Optional[datetime],
        grievance_date: Optional[datetime] = None,
    ) -> dict:
        """
        Check IRDAI-mandated TATs for motor insurance claims.
        IRDAI Motor Surveyor Regulations 2015 & Master Circular 2024.
        """
        violations = []
        now = datetime.now()

        # 48-hour surveyor appointment TAT
        if claim_intimation_date and survey_appointment_date:
            hours = (survey_appointment_date - claim_intimation_date).total_seconds() / 3600
            if hours > self.TAT_SURVEY_HOURS:
                violations.append({
                    "type": "surveyor_appointment_delayed",
                    "regulation": "IRDAI (Surveyors and Loss Assessors) Regulations 2015, Regulation 13",
                    "detail": (
                        f"Surveyor was appointed {hours:.0f} hours after claim intimation. "
                        f"IRDAI mandates appointment within {self.TAT_SURVEY_HOURS} hours."
                    ),
                    "severity": "high",
                    "legal_citation": "IRDAI Motor Guidelines 2017 — Surveyor Appointment TAT",
                })

        # 30-day survey report TAT
        if survey_appointment_date and survey_report_date:
            days = (survey_report_date - survey_appointment_date).days
            if days > self.TAT_SURVEY_REPORT_DAYS:
                excess = days - self.TAT_SURVEY_REPORT_DAYS
                violations.append({
                    "type": "survey_report_delayed",
                    "regulation": "IRDAI (Surveyors and Loss Assessors) Regulations 2015, Regulation 19",
                    "detail": (
                        f"Survey report submitted {days} days after appointment. "
                        f"IRDAI limit is {self.TAT_SURVEY_REPORT_DAYS} days. "
                        f"Excess delay: {excess} days."
                    ),
                    "severity": "medium",
                    "legal_citation": "IRDAI Surveyor Regulations 2015, Regulation 19 — Survey Report Timeline",
                })

        # 30-day final settlement TAT after survey
        if survey_report_date and rejection_date:
            days = (rejection_date - survey_report_date).days
            if days > self.TAT_CLAIM_SETTLEMENT_DAYS:
                excess = days - self.TAT_CLAIM_SETTLEMENT_DAYS
                violations.append({
                    "type": "settlement_delayed_post_survey",
                    "regulation": "IRDAI Master Circular 2024, Para 7.3",
                    "detail": (
                        f"Claim took {days} days to settle after survey report. "
                        f"IRDAI limit: {self.TAT_CLAIM_SETTLEMENT_DAYS} days. "
                        f"Excess: {excess} days."
                    ),
                    "severity": "high",
                    "interest_applicable": True,
                    "interest_note": (
                        "Insurer liable to pay interest at Bank Rate + 2% per annum "
                        f"on the claim amount for {excess} excess days."
                    ),
                    "legal_citation": "IRDAI Master Circular 2024, Para 7.4 — Interest on Delayed Claims",
                })

        # GRO overdue check
        if grievance_date:
            days_since = (now - grievance_date).days
            if days_since > self.TAT_GRO_DAYS:
                violations.append({
                    "type": "gro_resolution_overdue",
                    "regulation": "IRDAI Master Circular 2024, Para 10.2",
                    "detail": (
                        f"GRO complaint filed {days_since} days ago. "
                        f"Resolution mandated within {self.TAT_GRO_DAYS} days."
                    ),
                    "severity": "high",
                    "edaakhil_trigger": True,
                    "legal_citation": "Consumer Protection Act 2019 — E-Daakhil applicable",
                })

        deadlines = {}
        if rejection_date:
            deadlines["gro_deadline"] = rejection_date + timedelta(days=15)
            deadlines["ombudsman_deadline"] = rejection_date + timedelta(days=45)
            deadlines["consumer_court_limit"] = rejection_date + timedelta(days=365 * 2)
            deadlines["days_left_for_gro"] = max(0, (deadlines["gro_deadline"] - now).days)
            deadlines["days_left_for_ombudsman"] = max(0, (deadlines["ombudsman_deadline"] - now).days)

        return {
            "sla_violations": violations,
            "violations_found": len(violations),
            "deadlines": deadlines,
            "interest_applicable": any(v.get("interest_applicable") for v in violations),
        }

    # ── Step 2: Common Motor Rejection Grounds Check ─────────────
    def check_rejection_grounds(self, rejection_reason: str) -> dict:
        """
        Map motor rejection reasons to IRDAI-defensible arguments.
        """
        text = rejection_reason.lower()
        arguments = []

        # Driving without valid licence
        if any(kw in text for kw in ["driving licence", "licence expired", "no valid licence", "unlicensed"]):
            arguments.append({
                "ground": "driving_licence",
                "insurer_claim": "Vehicle driven without valid driving licence",
                "regulation": "IRDAI Motor Guidelines 2017 — Policy Conditions",
                "policyholder_argument": (
                    "Mere expiry of DL is not sufficient to deny claim if insurer "
                    "cannot prove the licence was expired at the exact time of accident. "
                    "Courts have consistently held that a valid DL that lapsed due to "
                    "administrative delay is not ground for full claim repudiation. "
                    "If the DL was valid but recently expired, demand proportionate settlement."
                ),
                "case_law": "National Insurance v. Swaran Singh (2004) Supreme Court of India — "
                            "Insurers cannot deny TP claims solely on DL expiry.",
                "severity": "medium",
            })

        # Drunk driving
        if any(kw in text for kw in ["drunk", "alcohol", "intoxicated", "dui", "blood alcohol"]):
            arguments.append({
                "ground": "drunk_driving",
                "insurer_claim": "Driver was under the influence of alcohol",
                "regulation": "Motor Vehicles Act 1988, Section 185",
                "policyholder_argument": (
                    "The insurer must produce the Medicolegal Certificate (MLC) or BAC report "
                    "from a certified lab to prove intoxication. A police FIR allegation alone "
                    "is insufficient. Challenge the evidence produced for BAC level."
                ),
                "severity": "high",
            })

        # Void policy conditions
        if any(kw in text for kw in ["policy lapsed", "premium not paid", "renewal overdue"]):
            arguments.append({
                "ground": "policy_lapse",
                "insurer_claim": "Policy was not in force at time of loss",
                "regulation": "IRDAI Master Circular 2024, Para 5 — Policy Continuity",
                "policyholder_argument": (
                    "Check the exact policy expiry date and time vs. the accident date/time. "
                    "If within the grace period, demand the insurer honour the claim. "
                    "Many insurers attempt to deny claims citing lapse without verifying "
                    "the precise window of cover."
                ),
                "severity": "high",
            })

        # Consequential damage vs direct damage
        if any(kw in text for kw in ["consequential", "not covered", "wear and tear", "mechanical breakdown"]):
            arguments.append({
                "ground": "consequential_damage",
                "insurer_claim": "Damage is consequential, not covered under OD policy",
                "regulation": "IRDAI Motor Policy Standard Terms",
                "policyholder_argument": (
                    "If the mechanical breakdown directly resulted from the insured accident "
                    "(e.g., engine seizure caused by accident-related water ingress), "
                    "it is an INSURED peril, not a standard exclusion. "
                    "Demand the surveyor's report specifically addresses causation."
                ),
                "severity": "medium",
            })

        # Depreciation disputes
        if any(kw in text for kw in ["depreciation", "deduction", "idv", "insured declared value"]):
            arguments.append({
                "ground": "depreciation_dispute",
                "insurer_claim": "Claim reduced due to depreciation deduction",
                "regulation": "IRDAI Motor Tariff 2002 (erstwhile) — Depreciation Schedule",
                "policyholder_argument": (
                    "If you hold a Zero Depreciation (Nil Dep) add-on rider, "
                    "the insurer CANNOT apply depreciation. Produce your policy schedule. "
                    "If no Zero Dep, verify the depreciation percentage applied matches "
                    "IRDAI's schedule for vehicle age — any excess deduction is wrongful."
                ),
                "severity": "medium",
            })

        # Use of vehicle for hire/reward
        if any(kw in text for kw in ["hire", "reward", "commercial use", "ola", "uber", "taxi"]):
            arguments.append({
                "ground": "vehicle_use_violation",
                "insurer_claim": "Vehicle used for hire/reward against policy conditions",
                "regulation": "Motor Vehicles Act 1988, Section 66 — Permit Rules",
                "policyholder_argument": (
                    "The insurer must prove the vehicle was being operated commercially "
                    "at the exact time of the accident. Casual or one-off use does not "
                    "void the entire policy. Challenge the insurer to produce evidence "
                    "of commercial operation at time of loss."
                ),
                "severity": "medium",
            })

        return {
            "rejection_arguments": arguments,
            "arguments_found": len(arguments),
            "defensibility": "strong" if len(arguments) > 0 else "requires_further_analysis",
        }

    def get_rejection_category(self, rejection_text: str) -> str:
        text = rejection_text.lower()
        categories = {
            "driving_licence": ["driving licence", "licence expired", "no valid licence", "unlicensed"],
            "drunk_driving": ["drunk", "alcohol", "intoxicated", "dui"],
            "policy_lapse": ["policy lapsed", "premium not paid", "renewal overdue"],
            "consequential_damage": ["consequential", "wear and tear", "mechanical breakdown"],
            "depreciation_dispute": ["depreciation", "deduction", "idv"],
            "vehicle_use_violation": ["hire", "commercial use", "ola", "uber"],
            "fraud": ["fraud", "fabricated", "false claim", "staged"],
            "theft_conditions": ["keys left", "unattended", "negligent", "fir not filed"],
        }
        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category
        return "other"


class LifeInsuranceRulesEngine:
    """
    IRDAI-compliant rules for life insurance claim rejection analysis.
    Covers Term, Endowment, ULIP, and Whole Life policies.
    """

    # ── TATs from IRDAI Life Regulations 2023 ────────────────────
    TAT_CLAIM_SETTLEMENT_DAYS = 30     # Settlement within 30 days of documents
    TAT_INVESTIGATION_DAYS = 90        # Investigation (early claims) max 90 days
    TAT_GRO_DAYS = 15
    OMBUDSMAN_MAX_RUPEES = 5_000_000

    # Early claim threshold (within 3 years = enhanced scrutiny is permitted)
    EARLY_CLAIM_YEARS = 3

    # Incontestability period (after 3 years, only fraud can void)
    INCONTESTABILITY_YEARS = 3

    # ── Step 1: SLA Violation Check (Life) ───────────────────────
    def check_sla_violations(
        self,
        claim_submission_date: Optional[datetime],
        documents_complete_date: Optional[datetime],
        rejection_date: Optional[datetime],
        grievance_date: Optional[datetime] = None,
    ) -> dict:
        """
        Check IRDAI-mandated TATs for life insurance claims.
        IRDAI (Life Insurance) Regulations 2023.
        """
        violations = []
        now = datetime.now()

        # 30-day settlement after complete documents
        if documents_complete_date and rejection_date:
            days = (rejection_date - documents_complete_date).days
            if days > self.TAT_CLAIM_SETTLEMENT_DAYS:
                excess = days - self.TAT_CLAIM_SETTLEMENT_DAYS
                violations.append({
                    "type": "settlement_delayed",
                    "regulation": "IRDAI (Life Insurance) Regulations 2023, Regulation 23(5)",
                    "detail": (
                        f"Claim took {days} days post complete documentation. "
                        f"IRDAI mandates settlement within {self.TAT_CLAIM_SETTLEMENT_DAYS} days. "
                        f"Excess: {excess} days."
                    ),
                    "severity": "high",
                    "interest_applicable": True,
                    "interest_note": (
                        "Insurer liable to pay interest at prevailing bank rate + 2% "
                        f"for {excess} excess days of delay."
                    ),
                    "legal_citation": "IRDAI Master Circular 2024, Para 7.4 — Interest on Delayed Claims",
                })

        # GRO overdue check
        if grievance_date:
            days_since = (now - grievance_date).days
            if days_since > self.TAT_GRO_DAYS:
                violations.append({
                    "type": "gro_resolution_overdue",
                    "regulation": "IRDAI Master Circular 2024, Para 10.2",
                    "detail": (
                        f"GRO complaint filed {days_since} days ago. "
                        f"IRDAI mandates resolution within {self.TAT_GRO_DAYS} days."
                    ),
                    "severity": "high",
                    "edaakhil_trigger": True,
                    "legal_citation": "Consumer Protection Act 2019 — E-Daakhil applicable",
                })

        deadlines = {}
        if rejection_date:
            deadlines["gro_deadline"] = rejection_date + timedelta(days=15)
            deadlines["ombudsman_deadline"] = rejection_date + timedelta(days=45)
            deadlines["consumer_court_limit"] = rejection_date + timedelta(days=365 * 2)
            deadlines["days_left_for_gro"] = max(0, (deadlines["gro_deadline"] - now).days)
            deadlines["days_left_for_ombudsman"] = max(0, (deadlines["ombudsman_deadline"] - now).days)

        return {
            "sla_violations": violations,
            "violations_found": len(violations),
            "deadlines": deadlines,
            "interest_applicable": any(v.get("interest_applicable") for v in violations),
        }

    # ── Step 2a: Incontestability Period Check ───────────────────
    def check_incontestability(
        self,
        policy_inception_date: Optional[datetime],
        rejection_reason: str,
    ) -> dict:
        """
        IRDAI (Life Insurance) Regulations 2023, Regulation 27.
        After 3 continuous years, insurer CANNOT contest a claim on
        non-disclosure grounds EXCEPT proven fraud.
        """
        if not policy_inception_date:
            return {
                "incontestability_applies": False,
                "note": "Policy inception date not provided — cannot assess incontestability.",
            }

        years_active = (datetime.now() - policy_inception_date).days / 365.25
        non_disclosure_keywords = [
            "non-disclosure", "non disclosure", "undisclosed", "concealment",
            "material fact", "misrepresentation", "not disclosed",
            "false declaration", "incorrect information", "material misrepresentation",
        ]
        rejection_lower = rejection_reason.lower()
        is_non_disclosure = any(kw in rejection_lower for kw in non_disclosure_keywords)

        if years_active >= self.INCONTESTABILITY_YEARS and is_non_disclosure:
            return {
                "incontestability_applies": True,
                "years_active": round(years_active, 1),
                "regulation": "IRDAI (Life Insurance) Regulations 2023, Regulation 27",
                "argument": (
                    f"The policy has been in force for {round(years_active, 1)} years. "
                    f"Under IRDAI (Life Insurance) Regulations 2023, Regulation 27, "
                    f"after {self.INCONTESTABILITY_YEARS} continuous years, a life insurer "
                    f"CANNOT repudiate a claim based on non-disclosure or misrepresentation "
                    f"UNLESS it can prove FRAUDULENT intent. The burden of proving fraud "
                    f"lies entirely with the insurer. Administrative omissions, innocent "
                    f"errors, or undisclosed conditions that are unrelated to the cause "
                    f"of death do NOT constitute fraud. This rejection is legally untenable."
                ),
                "strength": "very_strong",
                "counter_to_insurer": (
                    "Demand the insurer produce evidence of intentional fraudulent intent. "
                    "An undisclosed pre-existing condition that is unrelated to the cause "
                    "of death CANNOT be used to void the policy after 3 years."
                ),
            }

        if years_active < self.INCONTESTABILITY_YEARS and is_non_disclosure:
            remaining = self.INCONTESTABILITY_YEARS - years_active
            return {
                "incontestability_applies": False,
                "years_active": round(years_active, 1),
                "years_remaining": round(remaining, 1),
                "note": (
                    f"Incontestability requires {self.INCONTESTABILITY_YEARS} continuous years. "
                    f"Current: {round(years_active, 1)} years. "
                    f"Policy is in the 'early claim' contestable window."
                ),
                "early_claim_note": (
                    "Insurer is permitted to investigate early claims more thoroughly, "
                    "but must still prove material misrepresentation caused the loss. "
                    "Investigation must be completed within 90 days (IRDAI Life Regs 2023, Reg 23)."
                ),
            }

        return {
            "incontestability_applies": False,
            "years_active": round(years_active, 1),
            "note": "Rejection does not appear to be non-disclosure-based; incontestability check N/A.",
        }

    # ── Step 2b: Common Life Rejection Grounds Check ─────────────
    def check_rejection_grounds(self, rejection_reason: str) -> dict:
        """
        Map life insurance rejection reasons to IRDAI-defensible arguments.
        """
        text = rejection_reason.lower()
        arguments = []

        # Suicide exclusion (within 1 year)
        if any(kw in text for kw in ["suicide", "self-inflicted", "self inflicted"]):
            arguments.append({
                "ground": "suicide_exclusion",
                "insurer_claim": "Death due to suicide — excluded under policy",
                "regulation": "IRDAI (Life Insurance) Regulations 2023, Regulation 27(7)",
                "policyholder_argument": (
                    "IRDAI mandates that for policies in force for more than 1 year, "
                    "the insurer MUST pay at least 80% of premiums paid or surrender value, "
                    "whichever is higher, even in suicide cases. "
                    "For policies >3 years: insurer must pay full sum assured "
                    "unless suicide exclusion is specifically and prominently disclosed in the CIS. "
                    "Demand the insurer produce the CIS showing this exclusion was prominently disclosed."
                ),
                "severity": "high",
            })

        # Non-disclosure / material misrepresentation
        if any(kw in text for kw in ["non-disclosure", "misrepresentation", "undisclosed", "concealment"]):
            arguments.append({
                "ground": "non_disclosure",
                "insurer_claim": "Material non-disclosure / misrepresentation at proposal stage",
                "regulation": "Insurance Act 1938, Section 45 & IRDAI Life Regulations 2023, Reg 27",
                "policyholder_argument": (
                    "Under Section 45 of Insurance Act 1938, after 3 years the insurer "
                    "cannot repudiate on non-disclosure grounds except for fraud. "
                    "Even within 3 years, the insurer must prove: (1) the fact was material, "
                    "(2) the policyholder knew it was material, AND (3) the non-disclosure "
                    "was intentional. Mere non-disclosure of a condition unrelated to the "
                    "cause of death is insufficient ground for repudiation."
                ),
                "severity": "high",
            })

        # Free-look cancellation mis-used
        if any(kw in text for kw in ["free look", "free-look", "surrender", "lapsed"]):
            arguments.append({
                "ground": "policy_lapse",
                "insurer_claim": "Policy lapsed / surrendered before claim",
                "regulation": "IRDAI Master Circular 2024 — Revival of Lapsed Policies",
                "policyholder_argument": (
                    "If premiums were paid but incorrectly not applied by the insurer, "
                    "demand the premium payment receipts and bank statement evidence. "
                    "If the policy lapsed due to insurer's failure to send renewal notice, "
                    "this constitutes Deficiency in Service under CPA 2019, S.2(11)."
                ),
                "severity": "medium",
            })

        # Accidental death benefit disputes
        if any(kw in text for kw in ["accident", "accidental death", "natural cause", "not accident"]):
            arguments.append({
                "ground": "accidental_death_dispute",
                "insurer_claim": "Death not due to accident / accident benefit not applicable",
                "regulation": "IRDAI (Life Insurance) Regulations 2023 — Claim Settlement",
                "policyholder_argument": (
                    "The insurer must rely on the post-mortem report (PMR) and medical "
                    "evidence — not merely the death certificate — to distinguish accidental "
                    "from natural death. If PMR is inconclusive or unavailable, the benefit "
                    "of doubt must go to the claimant under consumer protection principles. "
                    "Challenge the insurer to produce the specific medical evidence relied upon."
                ),
                "severity": "medium",
            })

        return {
            "rejection_arguments": arguments,
            "arguments_found": len(arguments),
            "defensibility": "strong" if len(arguments) > 0 else "requires_further_analysis",
        }

    def get_rejection_category(self, rejection_text: str) -> str:
        text = rejection_text.lower()
        categories = {
            "non_disclosure": ["non-disclosure", "misrepresentation", "undisclosed", "concealment"],
            "suicide": ["suicide", "self-inflicted"],
            "policy_lapse": ["lapsed", "premium not paid", "surrender"],
            "early_claim": ["early claim", "within 3 years", "contestable"],
            "nominee_dispute": ["nominee", "beneficiary", "succession"],
            "accidental_death": ["accident", "accidental death", "natural cause"],
            "fraud": ["fraud", "fabricated", "false claim"],
        }
        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category
        return "other"


# ── Module-level singletons ───────────────────────────────────────
motor_engine = MotorInsuranceRulesEngine()
life_engine = LifeInsuranceRulesEngine()
