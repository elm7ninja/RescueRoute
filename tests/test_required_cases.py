"""
Week 2 tests for the required cases that test_fifo.py doesn't cover yet. 
Meant to run with:
    python -m pytest tests/
or
    python -m unittest discover tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fifo import run_fifo
from metrics import compute_metrics
from compare import compare_strategies, explain_changes, load_greedy
from test_fifo import make_donation, make_recipient, make_volunteer


run_greedy = load_greedy()


class TestRequiredCases(unittest.TestCase):
    def test_no_volunteer_with_enough_vehicle_capacity(self):
        # If the shelter has room for 80 meals but the only vehicle carries 50
        donation = make_donation(quantity=80)
        recipients = {"R-01": make_recipient(capacity=100)}
        volunteers = {"V-01": make_volunteer(vehicle_capacity=50)}

        [assignment] = run_fifo([donation], recipients, volunteers)

        self.assertEqual(assignment.status, "unassigned")
        self.assertIn("volunteer", assignment.decision_reason)
        # When a failed match shouldn't use up any capacity or pickups
        self.assertEqual(recipients["R-01"].remaining_capacity, 100)
        self.assertEqual(volunteers["V-01"].pickups_made, 0)

    def test_two_donations_competing_for_the_same_capacity(self):
        # 20 + 20 meals but the shelter only has room for 30.
        first = make_donation(did="D-01", quantity=20, ready=0)
        second = make_donation(did="D-02", quantity=20, ready=5)
        recipients = {"R-01": make_recipient(capacity=30)}
        volunteers = {"V-01": make_volunteer()}

        results = run_fifo([first, second], recipients, volunteers)

        self.assertEqual([a.status for a in results], ["assigned", "unassigned"])
        self.assertEqual(recipients["R-01"].remaining_capacity, 10)

    def test_empty_lists(self):
        assignments = run_fifo([], {}, {})
        metrics = compute_metrics([], {}, {}, assignments)

        self.assertEqual(assignments, [])
        self.assertEqual(metrics["donations_received"], 0)
        self.assertEqual(metrics["food_rescued"], 0)
        # When there's nothing to divide by so these are None instead of a ZeroDivisionError.
        self.assertIsNone(metrics["urgent_rescue_rate"])
        self.assertIsNone(metrics["recipient_utilization"])
        self.assertIsNone(metrics["volunteer_utilization"])


@unittest.skipIf(run_greedy is None, "greedy.py not merged yet")
class TestFifoVsGreedy(unittest.TestCase):
    def setUp(self):
        # When there's room for only one of these. D-EARLY arrives first but has 300 minutes
        # of shelf life. D-URGENT arrives 10 minutes later and has 30.
        self.donations = [
            make_donation(did="D-EARLY", quantity=30, ready=0, expiry=300),
            make_donation(did="D-URGENT", quantity=30, ready=10, expiry=40),
        ]
        self.recipients = {"R-01": make_recipient(capacity=30)}
        self.volunteers = {"V-01": make_volunteer()}
        self.results = compare_strategies(
            self.donations, self.recipients, self.volunteers, {"FIFO": run_fifo, "Greedy": run_greedy}
        )

    def status(self, strategy, did):
        for a in self.results[strategy]["assignments"]:
            if a.donation_id == did:
                return a.status
        return None

    def test_fifo_and_greedy_produce_different_results(self):
        self.assertEqual(self.status("FIFO", "D-EARLY"), "assigned")
        self.assertEqual(self.status("FIFO", "D-URGENT"), "unassigned")
        self.assertEqual(self.status("Greedy", "D-URGENT"), "assigned")
        # When greedy might call it "unassigned" or "deferred"
        self.assertNotEqual(self.status("Greedy", "D-EARLY"), "assigned")
        self.assertEqual(self.results["FIFO"]["metrics"]["urgent_rescue_rate"], 0.0)
        self.assertEqual(self.results["Greedy"]["metrics"]["urgent_rescue_rate"], 100.0)

    def test_starvation_case_explains_why_a_donation_was_deferred(self):
        # When greedy handles D-URGENT first even though it arrived second
        # so D-EARLY is deferred & by its turn the shelter is full

        greedy_order = [a.donation_id for a in self.results["Greedy"]["assignments"]]
        self.assertEqual(greedy_order, ["D-URGENT", "D-EARLY"])

        changes = explain_changes(
            self.donations,
            self.recipients,
            self.results["FIFO"]["assignments"],
            self.results["Greedy"]["assignments"],
        )
        [early] = [line for line in changes if line.startswith("D-EARLY")]
        self.assertIn("not under greedy", early)
        self.assertIn("D-URGENT", early)
        self.assertIn("least shelf life goes first", early)


if __name__ == "__main__":
    unittest.main()
