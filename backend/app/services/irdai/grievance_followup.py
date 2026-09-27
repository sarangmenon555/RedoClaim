"""
Grievance Follow-Up Reminder Generator — fully template-based, zero LLM
cost. Unlike the Appeal Generator (which builds case-specific legal
argumentation), a follow-up letter is structurally the same every time:
"I filed on X, your own deadline was Y, it's now Z days overdue, please
respond by [new deadline] or I will escalate." That's a fill-in-the-blanks
problem, not a judgment problem.
"""
from datetime import date, timedelta


def generate_followup_letter(
    user_name: str,
    insurer_name: str,
    policy_number: str,
    claim_amount: float,
    original_filed_date: date,
    deadline_type: str,  # "GRO response" | "IRDAI Ombudsman filing"
    deadline_date: date,
    escalation_target: str,  # what happens if this follow-up is also ignored
    as_of: date | None = None,
) -> dict:
    as_of = as_of or date.today()
    days_overdue = (as_of - deadline_date).days
    new_deadline = as_of + timedelta(days=7)

    subject = f"Follow-Up: Overdue Response on Claim — Policy {policy_number}"

    body = f"""To,
The Grievance Redressal Officer,
{insurer_name}

Subject: {subject}

Dear Sir/Madam,

This is a follow-up regarding my claim under Policy No. {policy_number}, originally filed on \
{original_filed_date.strftime('%d %B %Y')}, for an amount of Rs. {claim_amount:,.0f}.

Your stipulated timeline for {deadline_type} was {deadline_date.strftime('%d %B %Y')}. As of today, \
this deadline has passed by {days_overdue} day(s) with no response received on record.

I request that you provide a substantive response to my claim within 7 days of this letter, by \
{new_deadline.strftime('%d %B %Y')}. Please treat this as a formal reminder of your regulatory \
obligation under the applicable IRDAI grievance redressal timelines.

If no response is received by the above date, I will have no option but to escalate this matter to \
{escalation_target}, and will additionally bring this delay itself to their attention as a separate \
point of grievance.

I trust this matter will now receive your prompt attention.

Regards,
{user_name}
Policy No.: {policy_number}
Date: {as_of.strftime('%d %B %Y')}
"""

    return {
        "subject": subject,
        "letter_content": body,
        "days_overdue": days_overdue,
        "new_deadline": new_deadline.isoformat(),
        "escalation_target": escalation_target,
        "disclaimer": (
            "A template follow-up letter, not case-specific legal argumentation — use the Appeal Generator "
            "for a full case argument. Review names, dates, and figures before sending."
        ),
    }
