"""
RescueRoute data model.

All time fields (ready_time, expiry_time, closing_time, available_start,
available_end, scheduled_time) are simple integer "minutes since simulation
start". This keeps comparisons and tie-breaking deterministic and easy to
test, without pulling in real datetime parsing during Week 1.
"""

from dataclasses import dataclass, field
from typing import Set


@dataclass
class Donation:
    donation_id: str
    donor_name: str
    food_type: str
    quantity: int
    ready_time: int        # when the donation becomes available for pickup
    expiry_time: int       # last minute at which pickup is still valid
    pickup_area: str


@dataclass
class Recipient:
    recipient_id: str
    org_name: str
    accepted_food_types: Set[str]
    capacity: int
    area: str
    closing_time: int
    remaining_capacity: int = field(init=False)

    def __post_init__(self) -> None:
        self.remaining_capacity = self.capacity

    def accepts(self, food_type: str) -> bool:
        return food_type in self.accepted_food_types

    def can_take(self, quantity: int, arrival_time: int) -> bool:
        return quantity <= self.remaining_capacity and arrival_time <= self.closing_time


@dataclass
class Volunteer:
    volunteer_id: str
    vehicle_capacity: int
    area: str
    available_start: int
    available_end: int
    max_pickups: int
    pickups_made: int = field(default=0, init=False)

    def is_available(self, when: int) -> bool:
        return self.available_start <= when <= self.available_end

    def can_carry(self, quantity: int, when: int) -> bool:
        return (
            quantity <= self.vehicle_capacity
            and self.pickups_made < self.max_pickups
            and self.is_available(when)
        )


@dataclass
class Assignment:
    donation_id: str
    recipient_id: str
    volunteer_id: str
    scheduled_time: int
    decision_reason: str
    status: str  # "assigned" or "unassigned"
