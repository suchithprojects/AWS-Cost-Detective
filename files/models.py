"""
models.py
---------
These are the "shapes" of our data. Think of them as forms with blank
fields that must be filled in correctly. Pydantic checks the fields for
us, so if something is the wrong type (like a word where a number should
be), it complains instead of silently breaking.

We have three main shapes:
  1. Finding      -> "Here is one problem we found."
  2. Fix          -> "Here is how to solve that problem."
  3. Report       -> "Here is everything, added up, ready to show the user."
"""

from typing import Optional
from pydantic import BaseModel


class Finding(BaseModel):
    """One single cost problem we detected on one AWS resource."""
    resource_id: str          # e.g. "i-0abc123" or "vol-0def456"
    resource_type: str        # "EC2", "EBS", or "EIP"
    region: str               # e.g. "us-east-1"
    issue_type: str           # e.g. "over_provisioned", "unattached", "gp2_volume"
    severity: str             # "low", "medium", or "high"
    monthly_waste_usd: float  # roughly how many dollars/month this wastes
    reason: str               # plain-English why we flagged it


class Fix(BaseModel):
    """How to solve one Finding. This is what the user actually acts on."""
    explanation: str          # simple explanation of the problem + the fix
    risk_level: str           # "low", "medium", or "high" (how safe is the fix?)
    monthly_savings_usd: float
    cli_command: str          # the AWS command that applies the fix


class AnalyzedFinding(BaseModel):
    """A Finding glued together with its Fix. One complete item in the report."""
    finding: Finding
    fix: Fix


class Report(BaseModel):
    """The whole result of a scan, ready to show on screen."""
    region: str
    total_monthly_savings_usd: float
    number_of_issues: int
    items: list[AnalyzedFinding]
