
import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_loader import (
    load_donations,
    load_recipients,
    load_volunteers,
)


class TestDataValidation(unittest.TestCase):

    def load_test_csv(self, loader, row):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.csv"

            with path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=list(row.keys()))
                writer.writeheader()
                writer.writerow(row)

            return loader(str(path))

    def test_missing_donor_name(self):
        row = {
            "donation_id": "D1",
            "donor_name": "",
            "food_type": "produce",
            "quantity": "10",
            "ready_time": "10",
            "expiry_time": "50",
            "pickup_area": "North",
        }

        records, issues = self.load_test_csv(load_donations, row)
        self.assertEqual(len(records), 0)
        self.assertTrue(issues)

    def test_negative_donation_time(self):
        row = {
            "donation_id": "D2",
            "donor_name": "Restaurant",
            "food_type": "produce",
            "quantity": "10",
            "ready_time": "-5",
            "expiry_time": "50",
            "pickup_area": "North",
        }

        records, issues = self.load_test_csv(load_donations, row)
        self.assertEqual(len(records), 0)
        self.assertTrue(issues)

    def test_empty_recipient_food_types(self):
        row = {
            "recipient_id": "R1",
            "org_name": "Shelter",
            "accepted_food_types": "",
            "capacity": "100",
            "area": "North",
            "closing_time": "200",
        }

        records, issues = self.load_test_csv(load_recipients, row)
        self.assertEqual(len(records), 0)
        self.assertTrue(issues)

    def test_missing_volunteer_area(self):
        row = {
            "volunteer_id": "V1",
            "vehicle_capacity": "50",
            "area": "",
            "available_start": "0",
            "available_end": "100",
            "max_pickups": "3",
        }

        records, issues = self.load_test_csv(load_volunteers, row)
        self.assertEqual(len(records), 0)
        self.assertTrue(issues)

    def test_valid_donation(self):
        row = {
            "donation_id": "D3",
            "donor_name": "Restaurant",
            "food_type": "produce",
            "quantity": "10",
            "ready_time": "10",
            "expiry_time": "50",
            "pickup_area": "North",
        }

        records, issues = self.load_test_csv(load_donations, row)
        self.assertIn("D3", records)
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
