# Shows what changed between FIFO and greedy and why.
#
# Usage:
#   python src/what_changed.py
#   python src/what_changed.py data/tight_capacity

import os
import sys

from data_loader import load_donations, load_recipients, load_volunteers
from fifo import run_fifo
from greedy import run_greedy
from compare import compare_strategies, explain_changes, format_metrics_table, summarize_changes


def main() -> None:
    # Use the folder passed in or data/ if there isn't one
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "data")

    donations, _ = load_donations(os.path.join(folder, "donations.csv"))
    recipients, _ = load_recipients(os.path.join(folder, "recipients.csv"))
    volunteers, _ = load_volunteers(os.path.join(folder, "volunteers.csv"))
    donations = list(donations.values())

    # Each strategy gets its own copy of the data (compare.py)
    results = compare_strategies(donations, recipients, volunteers, {"FIFO": run_fifo, "Greedy": run_greedy})
    fifo = results["FIFO"]
    greedy = results["Greedy"]

    print(format_metrics_table(results))
    print("\nWhat changed and why:")
    for line in summarize_changes(fifo["metrics"], greedy["metrics"]):
        print("-", line)
    for line in explain_changes(donations, recipients, fifo["assignments"], greedy["assignments"]):
        print("-", line)


if __name__ == "__main__":
    main()
