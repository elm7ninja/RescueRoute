"""
FIFO baseline strategy.

Process donations in arrival order (the order they appear in the input,
which we treat as arrival order). For each donation, assign the FIRST
feasible recipient (in dict/insertion order) and the FIRST feasible
volunteer. Every donation gets an Assignment record, whether matched
or not, each with a human-readable decision_reason.

Complexity: let D = number of donations, R = number of recipients,
V = number of volunteers. For each donation we scan up to R recipients
and, for a feasible recipient, up to V volunteers, so this baseline is
O(D * (R + V)) in the worst case. No sorting is needed since arrival
order is just input order, so there is no extra O(D log D) term here
(that appears in the greedy strategy instead).
"""

from typing import Dict, List

from models import Donation, Recipient, Volunteer, Assignment


def run_fifo(
    donations: List[Donation],
    recipients: Dict[str, Recipient],
    volunteers: Dict[str, Volunteer],
) -> List[Assignment]:
    assignments: List[Assignment] = []

    for donation in donations:
        recipient = _first_feasible_recipient(donation, recipients)
        if recipient is None:
            assignments.append(
                Assignment(
                    donation_id=donation.donation_id,
                    recipient_id="",
                    volunteer_id="",
                    scheduled_time=-1,
                    decision_reason=(
                        f"Donation {donation.donation_id} could not be assigned because "
                        f"no compatible recipient had remaining capacity before it expires "
                        f"at minute {donation.expiry_time}."
                    ),
                    status="unassigned",
                )
            )
            continue

        volunteer = _first_feasible_volunteer(donation, recipient, volunteers)
        if volunteer is None:
            assignments.append(
                Assignment(
                    donation_id=donation.donation_id,
                    recipient_id="",
                    volunteer_id="",
                    scheduled_time=-1,
                    decision_reason=(
                        f"Donation {donation.donation_id} could not be assigned because "
                        f"no available volunteer had enough vehicle capacity or was free "
                        f"at minute {donation.ready_time}."
                    ),
                    status="unassigned",
                )
            )
            continue

        # Commit the match: consume capacity/pickup slots.
        recipient.remaining_capacity -= donation.quantity
        volunteer.pickups_made += 1

        assignments.append(
            Assignment(
                donation_id=donation.donation_id,
                recipient_id=recipient.recipient_id,
                volunteer_id=volunteer.volunteer_id,
                scheduled_time=donation.ready_time,
                decision_reason=(
                    f"Donation {donation.donation_id} was assigned to {recipient.org_name} "
                    f"with volunteer {volunteer.volunteer_id} because it accepts "
                    f"{donation.food_type}, has capacity available, and the volunteer "
                    f"can carry the quantity at minute {donation.ready_time}."
                ),
                status="assigned",
            )
        )

    return assignments


def _first_feasible_recipient(donation: Donation, recipients: Dict[str, Recipient]):
    for recipient in recipients.values():
        if (
            recipient.accepts(donation.food_type)
            and recipient.can_take(donation.quantity, donation.ready_time)
            and donation.ready_time <= donation.expiry_time
        ):
            return recipient
    return None


def _first_feasible_volunteer(donation: Donation, recipient: Recipient, volunteers: Dict[str, Volunteer]):
    for volunteer in volunteers.values():
        if volunteer.can_carry(donation.quantity, donation.ready_time):
            return volunteer
    return None
