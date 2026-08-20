"""
reasoner.py
-----------
STAGE 3 of the assembly line: EXPLAIN IT AND WRITE THE FIX.

Now that the analyzer has found the problems, we turn each one into something
a human can act on: a friendly explanation, a risk level, and the exact AWS
command that fixes it.

This file works in TWO ways:

  A) WITHOUT AI (default):
     We use clear, hand-written templates. This always works, costs nothing,
     and never needs an internet key. Great for beginners and demos.

  B) WITH AI (optional):
     If you set an OPENAI_API_KEY, we ask the AI to write a nicer, more
     natural explanation. The important part is that the AI only *rewrites*
     -- it never decides what's wasteful. The rules already did that. This
     keeps the tool trustworthy: the AI can't invent fake problems.
"""

import os
from models import Finding, Fix

USE_AI = bool(os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------------------------------------
# PART A: the always-works template fixes
# ---------------------------------------------------------------------------

def _template_fix(finding: Finding) -> Fix:
    r = finding.region
    rid = finding.resource_id

    if finding.issue_type == "over_provisioned":
        return Fix(
            explanation=(
                f"{finding.reason} Shrinking it keeps everything running but "
                f"lowers the bill. This needs a short restart, so do it during "
                f"a quiet time."
            ),
            risk_level="medium",  # requires a brief restart
            monthly_savings_usd=finding.monthly_waste_usd,
            cli_command=(
                f"aws ec2 stop-instances --instance-ids {rid} --region {r} && "
                f"aws ec2 modify-instance-attribute --instance-id {rid} "
                f"--instance-type <smaller-type> --region {r} && "
                f"aws ec2 start-instances --instance-ids {rid} --region {r}"
            ),
        )

    if finding.issue_type == "unattached" and finding.resource_type == "EBS":
        return Fix(
            explanation=(
                f"{finding.reason} Take a quick snapshot first (a backup), then "
                f"delete the disk. If you never need it again, you stop paying "
                f"for it."
            ),
            risk_level="medium",  # deleting data -- back up first
            monthly_savings_usd=finding.monthly_waste_usd,
            cli_command=(
                f"aws ec2 create-snapshot --volume-id {rid} --region {r} && "
                f"aws ec2 delete-volume --volume-id {rid} --region {r}"
            ),
        )

    if finding.issue_type == "gp2_volume":
        return Fix(
            explanation=(
                f"{finding.reason} This one is easy and safe -- it happens live "
                f"with no downtime."
            ),
            risk_level="low",
            monthly_savings_usd=finding.monthly_waste_usd,
            cli_command=(
                f"aws ec2 modify-volume --volume-id {rid} "
                f"--volume-type gp3 --region {r}"
            ),
        )

    if finding.issue_type == "unattached" and finding.resource_type == "EIP":
        return Fix(
            explanation=(
                f"{finding.reason} Releasing it stops the charge. Only do this "
                f"if you don't need to keep this exact IP address."
            ),
            risk_level="low",
            monthly_savings_usd=finding.monthly_waste_usd,
            cli_command=(
                f"aws ec2 release-address --allocation-id {rid} --region {r}"
            ),
        )

    # A safe fallback if we ever add a rule but forget a template.
    return Fix(
        explanation=finding.reason,
        risk_level="low",
        monthly_savings_usd=finding.monthly_waste_usd,
        cli_command="# No automatic command available -- review manually.",
    )


# ---------------------------------------------------------------------------
# PART B: optional AI rewrite of the explanation
# ---------------------------------------------------------------------------

def _ai_polish(finding: Finding, base_fix: Fix) -> Fix:
    """Ask the AI to rewrite the explanation in a friendlier way.
    If anything goes wrong, we quietly fall back to the template text."""
    try:
        from openai import OpenAI
        client = OpenAI()
        prompt = (
            "Rewrite this AWS cost tip in 2 short, friendly sentences a "
            "beginner could understand. Do not change the numbers or the "
            "recommended action.\n\n"
            f"Problem: {finding.reason}\n"
            f"Fix idea: {base_fix.explanation}"
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
        )
        nicer = response.choices[0].message.content.strip()
        # Keep everything the same, only swap in the nicer explanation.
        return base_fix.model_copy(update={"explanation": nicer})
    except Exception:
        return base_fix  # AI failed? No problem -- use the template.


# ---------------------------------------------------------------------------
# PUBLIC FUNCTION
# ---------------------------------------------------------------------------

def make_fix(finding: Finding) -> Fix:
    """Turn one Finding into one Fix (with or without AI)."""
    fix = _template_fix(finding)
    if USE_AI:
        fix = _ai_polish(finding, fix)
    return fix
