"""
pricing.py
----------
AWS pricing is huge and complicated. For a project, we don't need to be
perfect -- we just need good *estimates* so we can say "this wastes about
$X per month." These numbers are rough US East (N. Virginia) prices.

If you ever want exact numbers, AWS has a real Pricing API. But rough
estimates are honest and totally fine for a portfolio tool, as long as
you label them as estimates (we do).

Rule of thumb we use everywhere:
    monthly cost = hourly cost * 730     (730 = average hours in a month)
"""

HOURS_PER_MONTH = 730

# Approximate on-demand price per hour for common EC2 instance types.
EC2_PRICE_PER_HOUR = {
    "t3.micro": 0.0104,
    "t3.small": 0.0208,
    "t3.medium": 0.0416,
    "t3.large": 0.0832,
    "t3.xlarge": 0.1664,
    "t3.2xlarge": 0.3328,
    "m5.large": 0.096,
    "m5.xlarge": 0.192,
    "m5.2xlarge": 0.384,
    "m5.4xlarge": 0.768,
    "c5.large": 0.085,
    "c5.xlarge": 0.17,
    "c5.2xlarge": 0.34,
}

# If an instance is barely used, we suggest the next size down.
ONE_SIZE_DOWN = {
    "t3.2xlarge": "t3.xlarge",
    "t3.xlarge": "t3.large",
    "t3.large": "t3.medium",
    "t3.medium": "t3.small",
    "t3.small": "t3.micro",
    "m5.4xlarge": "m5.2xlarge",
    "m5.2xlarge": "m5.xlarge",
    "m5.xlarge": "m5.large",
    "c5.2xlarge": "c5.xlarge",
    "c5.xlarge": "c5.large",
}

# EBS (disk) storage price per GB per month.
EBS_PRICE_PER_GB = {
    "gp2": 0.10,
    "gp3": 0.08,   # gp3 is newer, faster, AND cheaper than gp2
}

# An Elastic IP that is just sitting there unused costs this per month.
UNUSED_EIP_MONTHLY = 3.60


def ec2_monthly_cost(instance_type: str) -> float:
    """How much does this EC2 instance cost per month (roughly)?"""
    hourly = EC2_PRICE_PER_HOUR.get(instance_type, 0.10)  # default guess
    return round(hourly * HOURS_PER_MONTH, 2)


def ebs_monthly_cost(volume_type: str, size_gb: int) -> float:
    """How much does this disk cost per month (roughly)?"""
    per_gb = EBS_PRICE_PER_GB.get(volume_type, 0.10)
    return round(per_gb * size_gb, 2)
