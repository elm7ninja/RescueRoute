"""
Week 2 tests for src/metrics.py. 
Run with:
  python -m pytest tests/
or
  python -m unittest discover tests
"""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models import Assignment
from fifo import run_fifo
from data_loader import load_donations, load_recipients, load_volunteers
from metrics import compute_metrics
from test_fifo import make_donation, make_recipient, make_volunteer


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def make_assignment(did, status):
    # Hand-made decision 
    assigned = status == "assigned"
    return Assignment(
        donation_id=did,
        recipient_id="R-01" if assigned else "",
        volunteer_id="V-01" if assigned else "",
        scheduled_time=0 if assigned else -1,
        decision_reason="test",
        status=status,
    )


class TestMetrics(unittest.TestCase):
    def setUp(self):
        # Shelf lives are 30, 45, & 200 minutes. Makes D-1 & D-2 urgent.
        self.donations = [
            make_donation(did="D-1", quantity=10, ready=0, expiry=30),
            make_donation(did="D-2", quantity=20, ready=0, expiry=45),
            make_donation(did="D-3", quantity=5, ready=0, expiry=200),
        ]
        self.assignments = [
            make_assignment("D-1", "assigned"),
            make_assignment("D-2", "unassigned"),
            make_assignment("D-3", "assigned"),
        ]
        # Recipient capacity 40 + 60 = 100. Volunteer capacity 10 x 2 + 20 x 1 = 40.
        self.recipients = {
            "R-01": make_recipient(rid="R-01", capacity=40),
            "R-02": make_recipient(rid="R-02", capacity=60),
        }
        self.volunteers = {
            "V-01": make_volunteer(vid="V-01", vehicle_capacity=10, max_pickups=2),
            "V-02": make_volunteer(vid="V-02", vehicle_capacity=20, max_pickups=1),
        }
        self.metrics = compute_metrics(self.donations, self.recipients, self.volunteers, self.assignments)

    def test_donation_counts(self):
        self.assertEqual(self.metrics["donations_received"], 3)
        self.assertEqual(self.metrics["donations_assigned"], 2)
        self.assertEqual(self.metrics["donations_unassigned"], 1)

    def test_food_rescued_and_at_risk(self):
        self.assertEqual(self.metrics["food_rescued"], 15)
        self.assertEqual(self.metrics["food_at_risk"], 20)

    def test_urgent_rescue_rate(self):
        # 1 of the 2 urgent donations is assigned
        self.assertEqual(self.metrics["urgent_rescue_rate"], 50.0)

    def test_capacity_utilization(self):
        self.assertEqual(self.metrics["recipient_utilization"], 15.0)
        self.assertEqual(self.metrics["volunteer_utilization"], 37.5)

    def test_fifo_metrics_on_sample_data(self):
        donations_by_id, _ = load_donations(os.path.join(DATA_DIR, "donations.csv"))
        recipients, _ = load_recipients(os.path.join(DATA_DIR, "recipients.csv"))
        volunteers, _ = load_volunteers(os.path.join(DATA_DIR, "volunteers.csv"))
        donations = list(donations_by_id.values())

        assignments = run_fifo(donations, copy.deepcopy(recipients), copy.deepcopy(volunteers))
        metrics = compute_metrics(donations, recipients, volunteers, assignments)

        self.assertEqual(metrics["donations_received"], 8)
        self.assertEqual(metrics["donations_assigned"], 7)
        self.assertEqual(metrics["donations_unassigned"], 1)
        self.assertEqual(metrics["food_rescued"], 170)
        self.assertEqual(metrics["food_at_risk"], 100)
        self.assertEqual(metrics["urgent_rescue_rate"], 100.0)
        self.assertEqual(metrics["recipient_utilization"], 68.0)
        self.assertEqual(metrics["volunteer_utilization"], 27.4)


if __name__ == "__main__":
    unittest.main()
