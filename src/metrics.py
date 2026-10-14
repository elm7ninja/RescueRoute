"""
Calculates the 8 metrics from the brief for one strategy's results, so FIFO
and greedy can be compared side by side. Returned as a dict.

"Urgent" means a shelf life (expiry_time - ready_time) of URGENT_SHELF_LIFE
minutes or less. Volunteer capacity counts every trip a volunteer can make
(vehicle_capacity * max_pickups).

Complexity: O(D + R + V), one pass over each list.
"""

from typing import Dict, List, Optional

from models import Donation, Recipient, Volunteer, Assignment


URGENT_SHELF_LIFE = 60  # minutes

# Metric keys in the order they are printed, with their labels.
METRIC_LABELS = {
    "donations_received": "Donations received",
    "donations_assigned": "Donations assigned",
    "donations_unassigned": "Donations unassigned",
    "food_rescued": "Food quantity rescued",
    "food_at_risk": "Food quantity at risk",
    "urgent_rescue_rate": "Urgent rescue rate",
    "recipient_utilization": "Recipient capacity utilization",
    "volunteer_utilization": "Volunteer capacity utilization",
}

PERCENT_METRICS = {"urgent_rescue_rate", "recipient_utilization", "volunteer_utilization"}


def shelf_life(donation: Donation) -> int:
    return donation.expiry_time - donation.ready_time


def compute_metrics(
    donations: List[Donation],
    recipients: Dict[str, Recipient],
    volunteers: Dict[str, Volunteer],
    assignments: List[Assignment],
) -> Dict[str, Optional[float]]:
    status_by_id = {a.donation_id: a.status for a in assignments}

    assigned = 0
    rescued = 0
    at_risk = 0
    urgent = 0
    urgent_assigned = 0

    for donation in donations:
        is_assigned = status_by_id.get(donation.donation_id) == "assigned"
        if is_assigned:
            assigned += 1
            rescued += donation.quantity
        else:
            # Unassigned and expired donations both count as at risk.
            at_risk += donation.quantity

        if shelf_life(donation) <= URGENT_SHELF_LIFE:
            urgent += 1
            if is_assigned:
                urgent_assigned += 1

    # Use the original capacity, not remaining_capacity, so the result is the
    # same whether or not the strategy changed these objects.
    recipient_capacity = sum(r.capacity for r in recipients.values())
    volunteer_capacity = sum(v.vehicle_capacity * v.max_pickups for v in volunteers.values())

    return {
        "donations_received": len(donations),
        "donations_assigned": assigned,
        "donations_unassigned": len(donations) - assigned,
        "food_rescued": rescued,
        "food_at_risk": at_risk,
        "urgent_rescue_rate": _percent(urgent_assigned, urgent),
        "recipient_utilization": _percent(rescued, recipient_capacity),
        "volunteer_utilization": _percent(rescued, volunteer_capacity),
    }


def _percent(part: int, whole: int) -> Optional[float]:
    if whole == 0:
        return None
    return round(100 * part / whole, 1)
