"""
collector.py
------------
STAGE 1 of the assembly line: GO GET THE DATA.

This file only fetches raw information from AWS. It does NOT decide what is
good or bad -- that is the analyzer's job. Keeping "fetching" and "thinking"
separate makes the code easy to read and test.

We use boto3, which is Amazon's official Python toolkit for talking to AWS.

IMPORTANT SAFETY NOTE:
    The AWS keys you give this tool should be READ-ONLY. This tool never
    changes anything in your account -- it only looks. See the README.

MOCK MODE:
    If USE_MOCK_DATA=true in your .env file, we return realistic FAKE data
    instead of calling AWS. This lets you run the whole project with zero
    AWS setup -- perfect for a first run or a demo.
"""

import os
from datetime import datetime, timedelta, timezone

USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# We only import boto3 when we actually need it (real mode). That way the
# project still runs in mock mode even if boto3 isn't installed yet.
if not USE_MOCK_DATA:
    import boto3


def _assume_role_session(role_arn: str):
    """Return a boto3 session whose credentials come from assuming role_arn."""
    sts = boto3.client("sts")
    creds = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName="CostDetectiveScan",
    )["Credentials"]
    return boto3.Session(
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
    )


# ---------------------------------------------------------------------------
# FAKE DATA (used when USE_MOCK_DATA=true)
# ---------------------------------------------------------------------------

def _mock_instances():
    return [
        {"id": "i-0aa11bb22cc33dd44", "type": "t3.2xlarge", "avg_cpu": 3.1},
        {"id": "i-0ee55ff66gg77hh88", "type": "m5.xlarge", "avg_cpu": 6.4},
        {"id": "i-0ii99jj00kk11ll22", "type": "t3.medium", "avg_cpu": 55.0},  # healthy
    ]


def _mock_volumes():
    return [
        {"id": "vol-0aa11bb22cc33dd44", "type": "gp2", "size_gb": 200, "attached": True},
        {"id": "vol-0xx99yy88zz77ww66", "type": "gp3", "size_gb": 100, "attached": False},
        {"id": "vol-0mm44nn55oo66pp77", "type": "gp3", "size_gb": 50, "attached": True},  # healthy
    ]


def _mock_eips():
    return [
        {"id": "eipalloc-0aa11bb22cc33dd44", "attached": False},
        {"id": "eipalloc-0zz99yy88xx77ww66", "attached": True},  # healthy
    ]


# ---------------------------------------------------------------------------
# REAL DATA (used when USE_MOCK_DATA=false)
# ---------------------------------------------------------------------------

def _average_cpu(cloudwatch, instance_id, days=14):
    """Ask CloudWatch: what was this instance's average CPU % over N days?"""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    result = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=start,
        EndTime=end,
        Period=86400,          # one data point per day
        Statistics=["Average"],
    )
    points = result.get("Datapoints", [])
    if not points:
        return 0.0
    return round(sum(p["Average"] for p in points) / len(points), 1)


def _real_instances(region, session):
    ec2 = session.client("ec2", region_name=region)
    cloudwatch = session.client("cloudwatch", region_name=region)
    out = []
    pages = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )
    for reservation in pages["Reservations"]:
        for inst in reservation["Instances"]:
            out.append({
                "id": inst["InstanceId"],
                "type": inst["InstanceType"],
                "avg_cpu": _average_cpu(cloudwatch, inst["InstanceId"]),
            })
    return out


def _real_volumes(region, session):
    ec2 = session.client("ec2", region_name=region)
    out = []
    for vol in ec2.describe_volumes()["Volumes"]:
        out.append({
            "id": vol["VolumeId"],
            "type": vol["VolumeType"],
            "size_gb": vol["Size"],
            # "available" means the disk is attached to nothing = wasted
            "attached": vol["State"] != "available",
        })
    return out


def _real_eips(region, session):
    ec2 = session.client("ec2", region_name=region)
    out = []
    for addr in ec2.describe_addresses()["Addresses"]:
        out.append({
            "id": addr.get("AllocationId", addr.get("PublicIp")),
            # if it has no AssociationId, nothing is using it = wasted
            "attached": "AssociationId" in addr,
        })
    return out


# ---------------------------------------------------------------------------
# PUBLIC FUNCTIONS -- the rest of the app only calls these three.
# ---------------------------------------------------------------------------

def _session(role_arn: str | None):
    """Return a boto3 session — assumed-role session if role_arn given, else default."""
    if role_arn:
        return _assume_role_session(role_arn)
    return boto3.Session()


def get_instances(region, role_arn=None):
    return _mock_instances() if USE_MOCK_DATA else _real_instances(region, _session(role_arn))


def get_volumes(region, role_arn=None):
    return _mock_volumes() if USE_MOCK_DATA else _real_volumes(region, _session(role_arn))


def get_eips(region, role_arn=None):
    return _mock_eips() if USE_MOCK_DATA else _real_eips(region, _session(role_arn))
