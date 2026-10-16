"""
RescueRoute CLI entry point.

Runs FIFO and Greedy urgency-first scheduling and compares their results

Usage:
    python src/main.py
    python src/main.py --donations data/donations.csv --recipients data/recipients.csv --volunteers data/volunteers.csv
"""

import argparse
import copy
import os

from data_loader import load_donations, load_recipients, load_volunteers
from fifo import run_fifo
from greedy import run_greedy
from metrics import compute_metrics, METRIC_LABELS, PERCENT_METRICS


def main() -> None:
    parser = argparse.ArgumentParser(description="RescueRoute scheduler")
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

    # Run FIFO and Greedy with independent copies of the data
    fifo_assignments = run_fifo(
        donations, copy.deepcopy(recipients), copy.deepcopy(volunteers)
    )
    greedy_assignments = run_greedy(
        donations, copy.deepcopy(recipients), copy.deepcopy(volunteers)
    )

    # Calculate metrics for both strategies
    fifo_metrics = compute_metrics(
        donations, recipients, volunteers, fifo_assignments
    )

    greedy_metrics = compute_metrics(
        donations, recipients, volunteers, greedy_assignments
    )

    # Display FIFO results
    print("\n========== FIFO Results ==========")
    for assignment in fifo_assignments:
        print(f"[{assignment.status.upper():10}] {assignment.decision_reason}")

    # Display Greedy results
    print("\n========== Greedy Results ==========")
    for assignment in greedy_assignments:
        print(f"[{assignment.status.upper():10}] {assignment.decision_reason}")

    # Compare metrics
    print("\n========== FIFO vs Greedy Metrics ==========")
    print(f"{'Metric':<35} {'FIFO':<12} {'Greedy':<12}")

    for key, label in METRIC_LABELS.items():
        fifo_value = fifo_metrics[key]
        greedy_value = greedy_metrics[key]

        if key in PERCENT_METRICS:
            fifo_display = "N/A" if fifo_value is None else f"{fifo_value:.1f}%"
            greedy_display = "N/A" if greedy_value is None else f"{greedy_value:.1f}%"
        else:
            fifo_display = str(fifo_value)
            greedy_display = str(greedy_value)

        print(f"{label:<35} {fifo_display:<12} {greedy_display:<12}")
                                                               
                                                               
if __name__ == "__main__":
    main()
