"""
Greedy urgency-first strategy.

Handles the donation with the least remaining shelf life first
(expiry_time - ready_time). If two are tied, the larger quantity goes first,
then the earlier ready_time, followed by whichever came first in the file.

Each donation still gets the first feasible recipient and volunteer so the 
only thing greedy changes is the order. We use a heapq priority queue 
keyed on (shelf_life, -quantity, ready_time, index).

If a donation gets handled after one that arrived later, then its decision_reason
says it was deferred and which donations went ahead of it.

Complexity: D pushes and D pops on the heap is O(D log D), matching is
O(D * (R + V)) like FIFO & the deferred notes are O(D^2) worst case.
"""

import heapq
from typing import Dict, List

from models import Donation, Recipient, Volunteer, Assignment
from fifo import _first_feasible_recipient, _first_feasible_volunteer


def run_greedy(
    donations: List[Donation],
    recipients: Dict[str, Recipient],
    volunteers: Dict[str, Volunteer],
) -> List[Assignment]:
    heap = []
    for index, donation in enumerate(donations):
        shelf_life = donation.expiry_time - donation.ready_time
        # index is the last file order so heapq never compares two Donations
        heapq.heappush(heap, (shelf_life, -donation.quantity, donation.ready_time, index))

    assignments: List[Assignment] = []
    handled = []  # indexes in the order greedy handled them

    while heap:
        shelf_life, _, _, index = heapq.heappop(heap)
        donation = donations[index]

        # Donations that arrived after this one but got handled before it
        went_ahead = [donations[i] for i in handled if i > index]
        handled.append(index)
        note = _deferred_note(donation, went_ahead)

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
                        f"at minute {donation.expiry_time}.{note}"
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
                        f"at minute {donation.ready_time}.{note}"
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
                    f"with volunteer {volunteer.volunteer_id} because it expires in "
                    f"{shelf_life} minutes, {recipient.org_name} accepts {donation.food_type}, "
                    f"capacity is available, and the volunteer can carry the quantity.{note}"
                ),
                status="assigned",
            )
        )

    return assignments


def _deferred_note(donation: Donation, went_ahead: List[Donation]) -> str:
    if not went_ahead:
        return ""
    ids = ", ".join(d.donation_id for d in went_ahead)
    my_shelf_life = donation.expiry_time - donation.ready_time
    who = "it" if len(went_ahead) == 1 else "they"
    if all(d.expiry_time - d.ready_time < my_shelf_life for d in went_ahead):
        reason = f"{who} had less remaining shelf life"
    else:
        reason = f"{who} ranked higher (less shelf life, or a tie broken by quantity)"
    return (
        f" It was deferred: considered after {ids} because {reason} "
        f"under the urgency-first greedy rule."
    )
