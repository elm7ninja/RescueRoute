"""
RescueRoute CLI entry point (Week 1 scope: FIFO baseline only).

Usage:
    python src/main.py
    python src/main.py --donations data/donations.csv --recipients data/recipients.csv --volunteers data/volunteers.csv
"""

import argparse
import os

from data_loader import load_donations, load_recipients, load_volunteers
from fifo import run_fifo


def main() -> None:
    parser = argparse.ArgumentParser(description="RescueRoute FIFO baseline runner")
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument("--donations", default=os.path.join(here, "data", "donations.csv"))
    parser.add_argument("--recipients", default=os.path.join(here, "data", "recipients.csv"))
    parser.add_argument("--volunteers", default=os.path.join(here, "data", "volunteers.csv"))
    args = parser.parse_args()

    donations_by_id, d_issues = load_donations(args.donations)
    recipients, r_issues = load_recipients(args.recipients)
    volunteers, v_issues = load_volunteers(args.volunteers)

    for issue in d_issues + r_issues + v_issues:
        print(f"[WARN] {issue}")

    # Arrival order = input file order, preserved because dicts keep
    # insertion order in Python 3.7+.
    donations = list(donations_by_id.values())

    assignments = run_fifo(donations, recipients, volunteers)

    assigned = [a for a in assignments if a.status == "assigned"]
    unassigned = [a for a in assignments if a.status == "unassigned"]

    print(f"\nDonations received: {len(donations)}")
    print(f"Donations assigned: {len(assigned)}")
    print(f"Donations unassigned: {len(unassigned)}\n")

    for a in assignments:
        print(f"[{a.status.upper():10}] {a.decision_reason}")


if __name__ == "__main__":
    main()
