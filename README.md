# AWS Cost Detective

A read-only tool that scans an AWS account and reports wasted spend — over-provisioned
EC2 instances, unattached EBS volumes, old gp2 disks still in use, and idle Elastic IPs —
with plain-English explanations, copy-paste fix commands, and estimated monthly savings.

> Think of your AWS bill like a house where some lights are left on in empty rooms.
> This tool walks through the house, finds every light that's on for no reason, tells
> you which switch to flip, and adds up how much you'll save.

## What it finds

| Problem | What it means |
|---|---|
| Over-provisioned EC2 | A server much bigger than it needs to be, barely using its capacity |
| Unattached EBS volumes | A disk that's attached to nothing but still being billed |
| Old gp2 disks | Disks on the older "gp2" type when "gp3" is faster *and* cheaper |
| Idle Elastic IPs | A reserved IP address that isn't connected to anything (AWS charges for these) |

## How it works

```
  AWS  ─▶  1. Collector  ─▶  2. Analyzer  ─▶  3. Reasoner  ─▶  4. API server  ─▶  You
          (fetch raw data)  (rule-based    (plain-English    (serves the
                             detection)     explanation +     report)
                                            fix commands)
```

Detection (step 2) is deliberately **rule-based, not AI** — the analyzer decides what
counts as waste using fixed logic, so it can't hallucinate a problem that isn't there.
The AI (OpenAI API, optional) only rewrites the explanation in step 3 to be friendlier;
it never touches the underlying findings or numbers.

## Repo layout

```
files/          FastAPI backend
  collector.py    fetches raw AWS data via boto3 (or mock data)
  analyzer.py     rule-based waste detection
  reasoner.py     turns findings into explanations + fix commands (OpenAI API)
  main.py         FastAPI server tying the pipeline together
  models.py       Pydantic data shapes
  pricing.py      rough USD price estimates
  demo.py         terminal-only demo, no setup needed
  .env.example    config template (AWS keys, USE_MOCK_DATA flag, etc.)
frontend/        simple HTML frontend to trigger scans and view results
index.html       landing/demo page
Dockerfile       builds files/ + frontend/ into one runnable image
.dockerignore    keeps secrets (.env) and non-runtime files out of the image
SETUP_GUIDE.txt  day-to-day run instructions + client onboarding steps
```

## Quickstart (no AWS account needed)

The project ships with mock data, so you can see it work immediately:

```bash
cd files
pip install pydantic
python demo.py
```

## Run the full web server

```bash
cd files
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Then open `frontend/index.html` in a browser. It uses mock data until you set
`USE_MOCK_DATA=false` in `.env`.

- `http://127.0.0.1:8000/scan?region=us-east-1` → JSON report
- `http://127.0.0.1:8000/docs` → interactive API docs (FastAPI's built-in Swagger UI)

## Run it with Docker

No local Python install needed:

```bash
docker build -t aws-cost-detective .
docker run -p 8000:8000 -e USE_MOCK_DATA=true aws-cost-detective
```

Same URLs as above. Credentials for a real scan are passed at run time via
`-e`, never baked into the image — see `.dockerignore`, which keeps `.env`
out of the build context entirely.

## Scanning a real account

This tool only ever reads AWS data — it has no write permissions anywhere in its design.
For a consultant/agency use case, the account owner creates a cross-account IAM role
(read-only: `AmazonEC2ReadOnlyAccess` + `CloudWatchReadOnlyAccess`) and grants it to the
account running the scans, then shares the role ARN. No keys are ever exchanged, and no
write access is ever requested. See `SETUP_GUIDE.txt` for the exact steps.

## Tech stack

Python · FastAPI · boto3 · Pydantic · Docker · OpenAI API (optional) · HTML/JS frontend

## Ideas for growth

- More waste-detection rules (idle load balancers, old-generation instance types, S3 buckets with no lifecycle policy)
- A React frontend
- Scan history in Postgres
- Login / JWT auth
- Live scan progress via WebSocket

## Note on the numbers

Dollar figures are estimates based on common US-East pricing, not the live AWS Pricing API —
enough to see the shape of your savings without extra setup.
