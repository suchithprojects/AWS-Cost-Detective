"""
demo.py
-------
Run the WHOLE tool in your terminal, with no AWS account and no web server.
This is the fastest way to see it work and to take a screenshot for your
portfolio.

    python demo.py

It uses the fake data in collector.py (mock mode), runs it through every
stage, and prints a nice report.
"""

import os
# Force mock mode for the demo so it always runs anywhere.
os.environ["USE_MOCK_DATA"] = "true"

import collector
import analyzer
import reasoner

REGION = "us-east-1"


def main():
    # Run the pipeline
    instances = collector.get_instances(REGION)
    volumes = collector.get_volumes(REGION)
    eips = collector.get_eips(REGION)
    findings = analyzer.analyze_all(instances, volumes, eips, REGION)

    items = [(f, reasoner.make_fix(f)) for f in findings]
    items.sort(key=lambda pair: pair[1].monthly_savings_usd, reverse=True)
    total = round(sum(fix.monthly_savings_usd for _, fix in items), 2)

    # Print it nicely
    print("\n" + "=" * 60)
    print("  AWS COST DETECTIVE  --  scan report")
    print("=" * 60)
    print(f"  Region: {REGION}")
    print(f"  Problems found: {len(items)}")
    print(f"  Estimated savings: ${total}/month")
    print("=" * 60 + "\n")

    for i, (finding, fix) in enumerate(items, start=1):
        print(f"[{i}] {finding.resource_type}  {finding.resource_id}")
        print(f"    Save ~${fix.monthly_savings_usd}/month   "
              f"(risk: {fix.risk_level})")
        print(f"    {fix.explanation}")
        print(f"    Fix: {fix.cli_command}")
        print("-" * 60)

    print(f"\n  TOTAL POSSIBLE SAVINGS: ${total}/month\n")
    print("  (Dollar amounts are estimates. Mock data was used.)\n")


if __name__ == "__main__":
    main()
