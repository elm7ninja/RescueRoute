"""
Week 1 test suite. Run with:
    python -m pytest tests/
or
    python -m unittest discover tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models import Donation, Recipient, Volunteer
from fifo import run_fifo
from data_loader import load_donations


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def make_recipient(rid="R-01", food_types=None, capacity=50, area="north", closing_time=500):
    return Recipient(
        recipient_id=rid,
        org_name="Test Shelter",
        accepted_food_types=food_types or {"prepared_meals"},
        capacity=capacity,
        area=area,
        closing_time=closing_time,
    )


def make_volunteer(vid="V-01", vehicle_capacity=50, area="north", start=0, end=200, max_pickups=3):
    return Volunteer(
        volunteer_id=vid,
        vehicle_capacity=vehicle_capacity,
        area=area,
        available_start=start,
        available_end=end,
        max_pickups=max_pickups,
    )


def make_donation(did="D-01", food_type="prepared_meals", quantity=10, ready=0, expiry=100, area="north"):
    return Donation(
        donation_id=did,
        donor_name="Test Donor",
        food_type=food_type,
        quantity=quantity,
        ready_time=ready,
        expiry_time=expiry,
        pickup_area=area,
    )


class TestFifoBaseline(unittest.TestCase):
    def test_normal_match_is_assigned(self):
        donation = make_donation()
        recipients = {"R-01": make_recipient()}
        volunteers = {"V-01": make_volunteer()}

        [assignment] = run_fifo([donation], recipients, volunteers)

        self.assertEqual(assignment.status, "assigned")
        self.assertEqual(assignment.recipient_id, "R-01")
        self.assertEqual(assignment.volunteer_id, "V-01")
        self.assertIn("assigned to", assignment.decision_reason)

    def test_incompatible_food_type_is_unassigned(self):
        donation = make_donation(food_type="dairy")
        recipients = {"R-01": make_recipient(food_types={"prepared_meals"})}
        volunteers = {"V-01": make_volunteer()}

        [assignment] = run_fifo([donation], recipients, volunteers)

        self.assertEqual(assignment.status, "unassigned")
        self.assertIn("no compatible recipient", assignment.decision_reason)

    def test_insufficient_recipient_capacity_is_unassigned(self):
        donation = make_donation(quantity=100)
        recipients = {"R-01": make_recipient(capacity=10)}
        volunteers = {"V-01": make_volunteer(vehicle_capacity=200)}

        [assignment] = run_fifo([donation], recipients, volunteers)

        self.assertEqual(assignment.status, "unassigned")

    def test_expired_donation_is_unassigned(self):
        # ready_time after expiry_time simulates a donation that is
        # already expired by the time it would be picked up.
        donation = make_donation(ready=50, expiry=10)
        recipients = {"R-01": make_recipient(closing_time=500)}
        volunteers = {"V-01": make_volunteer()}

        [assignment] = run_fifo([donation], recipients, volunteers)

        self.assertEqual(assignment.status, "unassigned")

    def test_duplicate_donation_id_is_rejected_by_loader(self):
        os.makedirs(FIXTURES, exist_ok=True)
        path = os.path.join(FIXTURES, "duplicate_donations.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write("donation_id,donor_name,food_type,quantity,ready_time,expiry_time,pickup_area\n")
            f.write("D-1,Donor A,bread,5,0,100,north\n")
            f.write("D-1,Donor B,bread,5,0,100,north\n")

        donations, issues = load_donations(path)

        self.assertEqual(len(donations), 1)
        self.assertTrue(any("Duplicate donation_id" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
