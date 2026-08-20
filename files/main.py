"""
main.py
-------
STAGE 4 of the assembly line: SERVE THE RESULT.

This is the web server (built with FastAPI). It connects all the stages:

    collector  ->  analyzer  ->  reasoner  ->  Report

The frontend (or you, in a browser) calls /scan, and gets back a tidy report
listing every problem, its fix, and the total money you could save.

Run it with:
    uvicorn main:app --reload
Then open:
    http://127.0.0.1:8000/              (the frontend)
    http://127.0.0.1:8000/scan?region=us-east-1
    http://127.0.0.1:8000/docs   (auto-generated, clickable API page)
"""

import os

from dotenv import load_dotenv
load_dotenv()  # read the .env file so USE_MOCK_DATA / keys are available

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import collector
import analyzer
import reasoner
from models import AnalyzedFinding, Report

app = FastAPI(title="AWS Cost Detective")

# Let the frontend (opened as a file, or served from elsewhere) talk to this server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for a real product, list only your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_INDEX = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")


@app.get("/")
def home():
    return FileResponse(FRONTEND_INDEX)


@app.get("/scan")
def scan(region: str = "us-east-1", role_arn: str | None = None) -> Report:
    """Scan one AWS region and return a full cost report.

    Pass role_arn to scan a different AWS account via cross-account role.
    Example: /scan?region=us-east-1&role_arn=arn:aws:iam::123456789012:role/CostDetectiveReadOnly
    """

    # STAGE 1: fetch raw data
    instances = collector.get_instances(region, role_arn)
    volumes = collector.get_volumes(region, role_arn)
    eips = collector.get_eips(region, role_arn)

    # STAGE 2: find the problems
    findings = analyzer.analyze_all(instances, volumes, eips, region)

    # STAGE 3: explain each one and attach a fix
    items = []
    for finding in findings:
        fix = reasoner.make_fix(finding)
        items.append(AnalyzedFinding(finding=finding, fix=fix))

    # Put the biggest savings at the top so the important stuff is first.
    items.sort(key=lambda x: x.fix.monthly_savings_usd, reverse=True)

    total = round(sum(x.fix.monthly_savings_usd for x in items), 2)

    # STAGE 4: hand back the finished report
    return Report(
        region=region,
        total_monthly_savings_usd=total,
        number_of_issues=len(items),
        items=items,
    )
