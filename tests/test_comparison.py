"""
Week 2 tests for src/compare.py and the data/tight_capacity scenario. 
Meant to run with:
    python -m pytest tests/
or
    python -m unittest discover tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models import Assignment
from fifo import run_fifo
from data_loader import load_donations, load_recipients, load_volunteers
from compare import compare_strategies, explain_changes, format_difference, load_greedy, summarize_changes
from test_fifo import make_donation, make_recipient


run_greedy = load_greedy()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TIGHT_DIR = os.path.join(DATA_DIR, "tight_capacity")


def load_folder(folder):
    donations, d_issues = load_donations(os.path.join(folder, "donations.csv"))
    recipients, r_issues = load_recipients(os.path.join(folder, "recipients.csv"))
    volunteers, v_issues = load_volunteers(os.path.join(folder, "volunteers.csv"))
    return list(donations.values()), recipients, volunteers, d_issues + r_issues + v_issues


def assigned(did, rid="R-01", vid="V-01"):
    return Assignment(did, rid, vid, 0, "test", "assigned")


def unassigned(did):
    return Assignment(did, "", "", -1, "test", "unassigned")


class TestComparison(unittest.TestCase):
    def test_each_strategy_gets_a_fresh_copy_of_the_input(self):
        donations, recipients, volunteers, _ = load_folder(DATA_DIR)

        results = compare_strategies(donations, recipients, volunteers, {"Run 1": run_fifo, "Run 2": run_fifo})

        # When the second run didn't inherit the capacity the first run is used 
        self.assertEqual(results["Run 1"]["metrics"], results["Run 2"]["metrics"])
        self.assertEqual(results["Run 2"]["metrics"]["donations_assigned"], 7)
        # The original objects were never changed
        for recipient in recipients.values():
            self.assertEqual(recipient.remaining_capacity, recipient.capacity)
        for volunteer in volunteers.values():
            self.assertEqual(volunteer.pickups_made, 0)

    def test_explains_lost_and_gained_donations(self):
        # FIFO served D-EARLY first
        # Greedy served D-URGENT first (room for only one)
        donations = [
            make_donation(did="D-EARLY", quantity=30, ready=0, expiry=300),
            make_donation(did="D-URGENT", quantity=30, ready=10, expiry=40),
        ]
        recipients = {"R-01": make_recipient(capacity=30)}
        fifo = [assigned("D-EARLY"), unassigned("D-URGENT")]
        greedy = [assigned("D-URGENT"), unassigned("D-EARLY")]

        early, urgent = explain_changes(donations, recipients, fifo, greedy)

        self.assertIn("D-EARLY", early)
        self.assertIn("was assigned under FIFO (to Test Shelter) but not under greedy", early)
        self.assertIn("FIFO handled it at position 1 and greedy at position 2", early)
        self.assertIn("Greedy handled D-URGENT first (less shelf life)", early)
        self.assertIn("used up the room at Test Shelter", early)

        self.assertIn("D-URGENT", urgent)
        self.assertIn("was not assigned under FIFO but was assigned under greedy", urgent)
        self.assertIn("came after D-EARLY", urgent)

    def test_blames_volunteers_when_the_recipient_had_room(self):
        # The same as above but the shelter has room for 500 so space wasn't the problem
        donations = [
            make_donation(did="D-EARLY", quantity=30, ready=0, expiry=300),
            make_donation(did="D-URGENT", quantity=30, ready=10, expiry=40),
        ]
        recipients = {"R-01": make_recipient(capacity=500)}
        fifo = [assigned("D-EARLY"), unassigned("D-URGENT")]
        greedy = [assigned("D-URGENT"), unassigned("D-EARLY")]

        early, urgent = explain_changes(donations, recipients, fifo, greedy)

        self.assertIn("no volunteer was free", early)
        self.assertNotIn("room", early)
        self.assertIn("no volunteer was free", urgent)
        self.assertNotIn("room", urgent)

    def test_explains_a_change_of_recipient(self):
        donations = [make_donation(did="D-1"), make_donation(did="D-2")]
        pantry = make_recipient(rid="R-02")
        pantry.org_name = "Second Pantry"
        recipients = {"R-01": make_recipient(), "R-02": pantry}
        fifo = [assigned("D-1"), assigned("D-2")]
        greedy = [assigned("D-2"), assigned("D-1", rid="R-02")]

        [sentence] = explain_changes(donations, recipients, fifo, greedy)

        self.assertIn("D-1", sentence)
        self.assertIn("FIFO sent it to Test Shelter and greedy sent it to Second Pantry", sentence)
        self.assertIn("FIFO handled it at position 1 and greedy at position 2", sentence)

    def test_explains_a_change_of_volunteer(self):
        donations = [make_donation(did="D-1"), make_donation(did="D-2")]
        fifo = [assigned("D-1", vid="V-01"), assigned("D-2", vid="V-02")]
        greedy = [assigned("D-2", vid="V-01"), assigned("D-1", vid="V-02")]

        first, second = explain_changes(donations, {"R-01": make_recipient()}, fifo, greedy)

        self.assertIn("D-1 went to the same recipient", first)
        self.assertIn("picked up by V-01 under FIFO and V-02 under greedy", first)
        self.assertIn("picked up by V-02 under FIFO and V-01 under greedy", second)

    def test_nothing_to_explain_when_neither_strategy_places_it(self):
        # When greedy might mark a starved donation as "deferred" with no IDs
        donations = [make_donation(did="D-1")]
        fifo = [unassigned("D-1")]
        greedy = [Assignment("D-1", None, None, -1, "deferred", "deferred")]

        self.assertEqual(explain_changes(donations, {"R-01": make_recipient()}, fifo, greedy), [])

    def test_nothing_to_explain_when_nothing_changed(self):
        donations = [make_donation(did="D-1")]
        same = [assigned("D-1")]

        self.assertEqual(explain_changes(donations, {"R-01": make_recipient()}, same, same), [])

    def test_difference_column_is_greedy_minus_fifo(self):
        self.assertEqual(format_difference("donations_assigned", 4, 5), "+1")
        self.assertEqual(format_difference("food_rescued", 105, 100), "-5")
        self.assertEqual(format_difference("urgent_rescue_rate", 33.3, 100.0), "+66.7 pts")
        self.assertEqual(format_difference("food_rescued", 170, 170), "0")
        self.assertEqual(format_difference("urgent_rescue_rate", None, 50.0), "n/a")

    def test_summary_sentences(self):
        fifo = {"donations_received": 6, "donations_assigned": 4, "food_rescued": 105, "urgent_rescue_rate": 33.3}
        greedy = {"donations_received": 6, "donations_assigned": 5, "food_rescued": 100, "urgent_rescue_rate": 100.0}

        self.assertEqual(summarize_changes(fifo, greedy), [
            "Greedy assigned 5 of 6 donations and FIFO assigned 4 (+1 for greedy).",
            "Greedy rescued 100 units of food and FIFO rescued 105 (-5 for greedy).",
            "Greedy rescued 100.0% of urgent donations and FIFO rescued 33.3% (+66.7 points for greedy).",
        ])

    def test_tight_capacity_fifo_results(self):
        donations, recipients, volunteers, issues = load_folder(TIGHT_DIR)

        fifo = compare_strategies(donations, recipients, volunteers, {"FIFO": run_fifo})["FIFO"]
        status = {a.donation_id: a.status for a in fifo["assignments"]}

        self.assertEqual(issues, [])
        # D-2001 and D-2002 fill the shelter so urgent D-2003 and D-2006 dont fit
        self.assertEqual(status, {
            "D-2001": "assigned",
            "D-2002": "assigned",
            "D-2003": "unassigned",
            "D-2004": "assigned",
            "D-2005": "assigned",
            "D-2006": "unassigned",
        })
        self.assertEqual(fifo["metrics"]["urgent_rescue_rate"], 33.3)
        self.assertEqual(fifo["metrics"]["food_rescued"], 105)

    @unittest.skipIf(run_greedy is None, "greedy.py not merged yet")
    def test_tight_capacity_greedy_trade_off(self):
        donations, recipients, volunteers, _ = load_folder(TIGHT_DIR)

        results = compare_strategies(donations, recipients, volunteers, {"FIFO": run_fifo, "Greedy": run_greedy})
        fifo = results["FIFO"]["metrics"]
        greedy = results["Greedy"]["metrics"]
        greedy_status = {a.donation_id: a.status for a in results["Greedy"]["assignments"]}

        # Greedy saves every urgent donation and assigns one more overall
        # but D-2001, the big donation that arrived first, gets starved

        self.assertEqual(greedy["urgent_rescue_rate"], 100.0)
        self.assertEqual(greedy["donations_assigned"], fifo["donations_assigned"] + 1)
        self.assertNotEqual(greedy_status["D-2001"], "assigned")
        self.assertEqual(greedy["food_rescued"], 100)
        self.assertLess(greedy["food_rescued"], fifo["food_rescued"])


if __name__ == "__main__":
    unittest.main()
