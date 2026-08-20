# AWS Cost Detective 🕵️

An AI-powered tool that hunts down wasted money in your AWS cloud account.

You point it at an AWS region, and it acts like a detective: it looks at your
servers, disks, and IP addresses, spots the ones that are wasting money, and
hands you a plain-English report with the exact command to fix each one — plus
how much you'd save every month.

> Think of your AWS bill like a house where some lights are left on in empty
> rooms. This tool walks through the house, finds every light that's on for no
> reason, tells you which switch to flip, and adds up how much you'll save.

---

## What it finds (right now)

| # | Problem | Plain-English meaning |
|---|---------|-----------------------|
| 1 | **Over-provisioned servers** | An EC2 server that's way bigger than it needs to be (barely using its power). |
| 2 | **Unused disks** | An EBS disk that's attached to nothing but still charged for. |
| 3 | **Old disk type (gp2)** | A disk using the older "gp2" type when the newer "gp3" is faster *and* cheaper. |
| 4 | **Idle IP addresses** | An Elastic IP that's reserved but connected to nothing. AWS charges for these. |

These four are the "greatest hits" of AWS waste — common, easy to explain, and
real money. You can add more rules later (see *How to grow this* below).

---

## How it works (the assembly line)

The code is split into 4 small steps. Data flows through them like an assembly
line. Each step has ONE job, which makes the whole thing easy to understand.

```
   AWS  ─▶  1. COLLECTOR  ─▶  2. ANALYZER  ─▶  3. REASONER  ─▶  4. SERVER  ─▶  You
           (get the data)    (find problems)  (explain + fix)   (send report)
```

| File | Step | Its one job |
|------|------|-------------|
| `collector.py` | 1 | Fetch raw info from AWS (or fake data). Nothing else. |
| `analyzer.py`  | 2 | Apply simple rules to decide what's wasteful. |
| `reasoner.py`  | 3 | Write a friendly explanation + the fix command. |
| `main.py`      | 4 | A web server that runs all steps and returns a report. |
| `models.py`    | — | The "shapes" our data must follow. |
| `pricing.py`   | — | Rough price estimates to turn waste into dollars. |
| `demo.py`      | — | Run the whole thing in your terminal, no setup needed. |

**Why the AI only does step 3:** the *finding* of problems is done by plain
rules (step 2), not the AI. The AI just makes the explanation friendlier. This
is on purpose — it means the AI can never invent a fake problem or give you a
wrong number. The rules stay in charge; the AI just talks nicely. This is the
part that makes the tool trustworthy, and it's worth saying out loud in an
interview.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Cloud data | **boto3** (AWS's official Python toolkit) |
| Backend | **Python + FastAPI** |
| AI (optional) | **OpenAI API** |
| Data checking | **Pydantic** |
| Frontend (next step) | React (Vite + TypeScript + Tailwind) |

---

## Try it in 30 seconds (no AWS account needed)

The project ships with **mock mode** — realistic fake data — so you can see it
work immediately.

```bash
cd backend
pip install pydantic          # the only thing demo.py needs
python demo.py
```

You'll get a report in your terminal showing about **$200/month** of pretend
savings. Take a screenshot — that's your first portfolio image. 📸

---

## Run the real web server

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # then open .env and set your options
uvicorn main:app --reload
```

Now open these in your browser:

- `http://127.0.0.1:8000/scan?region=us-east-1` → the JSON report
- `http://127.0.0.1:8000/docs` → a clickable page to test it (FastAPI gives
  you this for free)

It still uses fake data until you flip `USE_MOCK_DATA=false` in `.env`.

---

## Scan a real AWS account (safely)

⚠️ **Read this part carefully — it's the most important safety step.**

This tool only ever *looks*; it never changes anything. But to be safe, give it
**read-only** keys so it *can't* change anything even by accident.

1. In the AWS Console go to **IAM → Users → Create user**.
2. Attach the built-in policy named **`ReadOnlyAccess`**.
3. Create an **access key** for that user.
4. Put the key + secret in your `.env` file and set `USE_MOCK_DATA=false`.

Never put write/admin keys in a project you might share or push to GitHub.
And add `.env` to your `.gitignore` so your keys never get uploaded.

---

## How to grow this (ideas for later)

You built a clean pipeline — adding features is now easy. In rough order of
effort:

1. **More rules** — idle load balancers, old-generation instances, S3 buckets
   with no lifecycle policy. Just add a new function in `analyzer.py`.
2. **A React frontend** — a real webpage that shows the report as cards, with a
   big "You could save $X/month" number at the top. This is what makes the demo
   *look* great.
3. **Save history** — store each scan in a database (Amazon RDS PostgreSQL) so
   you can show savings over time.
4. **Login** — add accounts with JWT so different users see their own scans.
5. **Live progress** — use a WebSocket to show "scanning… 60%" while it runs.

Build them one at a time. Each one is a separate, showable win.

---

## A note on the numbers

All dollar figures are **estimates** based on common US-East prices, so you can
see the *shape* of your savings without any complex setup. For exact figures,
AWS has a real Pricing API you can plug into `pricing.py` later.
