"""
analyzer.py
-----------
STAGE 2 of the assembly line: FIND THE PROBLEMS.

This file takes the raw data from the collector and applies simple, clear
RULES to decide what is wasteful. There is no AI here and no AWS here -- just
plain "if this, then that" logic. That makes it easy to trust and easy to test.

Each rule produces a Finding (defined in models.py).

Our rules for now:
  1. EC2 instance with very low CPU  -> it's too big (over-provisioned)
  2. EBS disk attached to nothing     -> it's wasted (unattached)
  3. EBS disk using old "gp2" type    -> switch to cheaper "gp3"
  4. Elastic IP attached to nothing   -> it's wasted (unattached)
"""

from models import Finding
import pricing

# If average CPU is below this % for 2 weeks, the instance is probably too big.
LOW_CPU_THRESHOLD = 10.0


def analyze_instances(instances, region):
    findings = []
    for inst in instances:
        if inst["avg_cpu"] < LOW_CPU_THRESHOLD and inst["type"] in pricing.ONE_SIZE_DOWN:
            current_cost = pricing.ec2_monthly_cost(inst["type"])
            smaller = pricing.ONE_SIZE_DOWN[inst["type"]]
            smaller_cost = pricing.ec2_monthly_cost(smaller)
            waste = round(current_cost - smaller_cost, 2)
            findings.append(Finding(
                resource_id=inst["id"],
                resource_type="EC2",
                region=region,
                issue_type="over_provisioned",
                severity="high",
                monthly_waste_usd=waste,
                reason=(
                    f"This server ({inst['type']}) used only {inst['avg_cpu']}% "
                    f"of its CPU on average -- it is much bigger than it needs "
                    f"to be. A {smaller} would handle this easily."
                ),
            ))
    return findings


def analyze_volumes(volumes, region):
    findings = []
    for vol in volumes:
        # Rule 2: a disk attached to nothing is pure waste.
        if not vol["attached"]:
            cost = pricing.ebs_monthly_cost(vol["type"], vol["size_gb"])
            findings.append(Finding(
                resource_id=vol["id"],
                resource_type="EBS",
                region=region,
                issue_type="unattached",
                severity="high",
                monthly_waste_usd=cost,
                reason=(
                    f"This {vol['size_gb']} GB disk is not attached to any "
                    f"server, so you are paying for storage nobody uses."
                ),
            ))
        # Rule 3: gp2 disks should almost always be gp3 (faster AND cheaper).
        elif vol["type"] == "gp2":
            gp2_cost = pricing.ebs_monthly_cost("gp2", vol["size_gb"])
            gp3_cost = pricing.ebs_monthly_cost("gp3", vol["size_gb"])
            waste = round(gp2_cost - gp3_cost, 2)
            findings.append(Finding(
                resource_id=vol["id"],
                resource_type="EBS",
                region=region,
                issue_type="gp2_volume",
                severity="medium",
                monthly_waste_usd=waste,
                reason=(
                    f"This {vol['size_gb']} GB disk uses the older 'gp2' type. "
                    f"Switching to 'gp3' is faster and about 20% cheaper, with "
                    f"no downtime."
                ),
            ))
    return findings


def analyze_eips(eips, region):
    findings = []
    for eip in eips:
        # Rule 4: an Elastic IP attached to nothing is charged by AWS.
        if not eip["attached"]:
            findings.append(Finding(
                resource_id=eip["id"],
                resource_type="EIP",
                region=region,
                issue_type="unattached",
                severity="low",
                monthly_waste_usd=pricing.UNUSED_EIP_MONTHLY,
                reason=(
                    "This public IP address is reserved but not connected to "
                    "anything. AWS charges for reserved IPs that sit unused."
                ),
            ))
    return findings


def analyze_all(instances, volumes, eips, region):
    """Run every rule and return one combined list of Findings."""
    findings = []
    findings += analyze_instances(instances, region)
    findings += analyze_volumes(volumes, region)
    findings += analyze_eips(eips, region)
    return findings
