"""
Loads donation, recipient, and volunteer records from CSV files and
validates them (duplicate IDs, missing fields, bad numeric/time values).

Design choice: donations/recipients/volunteers are returned as dicts keyed
by ID for O(1) lookup, matching the "Example design choice" in the brief.
Duplicate-ID detection uses a set for O(1) membership testing.
"""

import csv
from typing import Dict, List, Tuple

from models import Donation, Recipient, Volunteer


class ValidationError(Exception):
    """Raised when an input row fails validation."""


def _read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_donations(path: str) -> Tuple[Dict[str, Donation], List[str]]:
    """Returns (donations_by_id, issues). Issues are human-readable strings
    describing rows that were rejected (e.g. duplicate ID, bad quantity)."""
    donations: Dict[str, Donation] = {}
    seen_ids = set()
    issues: List[str] = []

    for row in _read_csv(path):
        did = row.get("donation_id", "").strip()
        if not did:
            issues.append("Skipped row with missing donation_id.")
            continue
        if did in seen_ids:
            issues.append(f"Duplicate donation_id '{did}' skipped.")
            continue
        try:
            quantity = int(row["quantity"])
            ready_time = int(row["ready_time"])
            expiry_time = int(row["expiry_time"])
            if quantity <= 0:
                raise ValueError("quantity must be positive")
            if expiry_time < ready_time:
                raise ValueError("expiry_time is before ready_time")
        except (KeyError, ValueError) as exc:
            issues.append(f"Donation '{did}' rejected: {exc}")
            continue

        seen_ids.add(did)
        donations[did] = Donation(
            donation_id=did,
            donor_name=row.get("donor_name", "").strip(),
            food_type=row.get("food_type", "").strip(),
            quantity=quantity,
            ready_time=ready_time,
            expiry_time=expiry_time,
            pickup_area=row.get("pickup_area", "").strip(),
        )

    return donations, issues


def load_recipients(path: str) -> Tuple[Dict[str, Recipient], List[str]]:
    recipients: Dict[str, Recipient] = {}
    seen_ids = set()
    issues: List[str] = []

    for row in _read_csv(path):
        rid = row.get("recipient_id", "").strip()
        if not rid:
            issues.append("Skipped row with missing recipient_id.")
            continue
        if rid in seen_ids:
            issues.append(f"Duplicate recipient_id '{rid}' skipped.")
            continue
        try:
            capacity = int(row["capacity"])
            closing_time = int(row["closing_time"])
            if capacity <= 0:
                raise ValueError("capacity must be positive")
        except (KeyError, ValueError) as exc:
            issues.append(f"Recipient '{rid}' rejected: {exc}")
            continue

        accepted = {
            t.strip() for t in row.get("accepted_food_types", "").split("|") if t.strip()
        }
        seen_ids.add(rid)
        recipients[rid] = Recipient(
            recipient_id=rid,
            org_name=row.get("org_name", "").strip(),
            accepted_food_types=accepted,
            capacity=capacity,
            area=row.get("area", "").strip(),
            closing_time=closing_time,
        )

    return recipients, issues


def load_volunteers(path: str) -> Tuple[Dict[str, Volunteer], List[str]]:
    volunteers: Dict[str, Volunteer] = {}
    seen_ids = set()
    issues: List[str] = []

    for row in _read_csv(path):
        vid = row.get("volunteer_id", "").strip()
        if not vid:
            issues.append("Skipped row with missing volunteer_id.")
            continue
        if vid in seen_ids:
            issues.append(f"Duplicate volunteer_id '{vid}' skipped.")
            continue
        try:
            vehicle_capacity = int(row["vehicle_capacity"])
            available_start = int(row["available_start"])
            available_end = int(row["available_end"])
            max_pickups = int(row["max_pickups"])
            if vehicle_capacity <= 0 or max_pickups <= 0:
                raise ValueError("capacity/max_pickups must be positive")
            if available_end < available_start:
                raise ValueError("available_end is before available_start")
        except (KeyError, ValueError) as exc:
            issues.append(f"Volunteer '{vid}' rejected: {exc}")
            continue

        seen_ids.add(vid)
        volunteers[vid] = Volunteer(
            volunteer_id=vid,
            vehicle_capacity=vehicle_capacity,
            area=row.get("area", "").strip(),
            available_start=available_start,
            available_end=available_end,
            max_pickups=max_pickups,
        )

    return volunteers, issues
