"""
Compares FIFO and greedy on the same data.

We run each strategy on its own copy of the input because running one uses up
recipient capacity and volunteer pickups so the second one would start with
less room.

Copying the data and getting the metrics is O(D + R + V) per
strategy. explain_changes() is O(D + R) per changed
donation so O(D * (D + R)) is the worst case.
"""

import copy
from typing import Callable, Dict, List

from models import Donation, Recipient, Volunteer, Assignment
from metrics import METRIC_LABELS, PERCENT_METRICS, URGENT_SHELF_LIFE, compute_metrics, shelf_life


def load_greedy():
    # Returns run_greedy or None if greedy.py isn't there.
    try:
        from greedy import run_greedy
    except ModuleNotFoundError as exc:
        if exc.name == "greedy":
            return None
        raise  # greedy.py is there but something it imports is missing
    return run_greedy


def compare_strategies(
    donations: List[Donation],
    recipients: Dict[str, Recipient],
    volunteers: Dict[str, Volunteer],
    strategies: Dict[str, Callable],
) -> Dict[str, dict]:
    """Returns {name: {"assignments": [...], "metrics": {...}}} for each strategy."""
    results = {}
    for name, strategy in strategies.items():
        # deepcopy so every strategy starts with full capacity and no pickups used
        assignments = strategy(
            copy.deepcopy(donations), copy.deepcopy(recipients), copy.deepcopy(volunteers)
        )
        metrics = compute_metrics(donations, recipients, volunteers, assignments)
        results[name] = {"assignments": assignments, "metrics": metrics}
    return results


def format_metrics_table(results: Dict[str, dict]) -> str:
    names = list(results)  # ["FIFO"] or ["FIFO", "Greedy"]

    header = f"{'Metric':<32}"
    for name in names:
        header += f"{name:>10}"
    if len(names) == 2:
        header += f"{names[1] + ' - ' + names[0]:>17}"
    lines = [header, "-" * len(header)]

    for key, label in METRIC_LABELS.items():
        row = f"{label:<32}"
        for name in names:
            row += f"{format_value(key, results[name]['metrics'][key]):>10}"
        if len(names) == 2:
            first = results[names[0]]["metrics"][key]
            second = results[names[1]]["metrics"][key]
            row += f"{format_difference(key, first, second):>17}"
        lines.append(row)

    return "\n".join(lines)


def format_value(key: str, value) -> str:
    if value is None:
        return "n/a"
    if key in PERCENT_METRICS:
        return f"{value:.1f}%"
    return str(value)


def format_difference(key: str, first, second) -> str:
    # second - first: "+1", "-5" or "+66.7 pts" for percentages
    if first is None or second is None:
        return "n/a"
    difference = round(second - first, 1)
    if difference == 0:
        return "0"
    if key in PERCENT_METRICS:
        return f"{difference:+.1f} pts"
    return f"{difference:+d}"


def summarize_changes(fifo: dict, greedy: dict) -> List[str]:
    total = fifo["donations_received"]
    lines = []

    if fifo["donations_assigned"] == greedy["donations_assigned"]:
        lines.append(f"Both strategies assigned {fifo['donations_assigned']} of {total} donations.")
    else:
        diff = greedy["donations_assigned"] - fifo["donations_assigned"]
        lines.append(
            f"Greedy assigned {greedy['donations_assigned']} of {total} donations and FIFO "
            f"assigned {fifo['donations_assigned']} ({diff:+d} for greedy)."
        )

    if fifo["food_rescued"] == greedy["food_rescued"]:
        lines.append(f"Both strategies rescued {fifo['food_rescued']} units of food.")
    else:
        diff = greedy["food_rescued"] - fifo["food_rescued"]
        lines.append(
            f"Greedy rescued {greedy['food_rescued']} units of food and FIFO rescued "
            f"{fifo['food_rescued']} ({diff:+d} for greedy)."
        )

    fifo_rate = fifo["urgent_rescue_rate"]
    greedy_rate = greedy["urgent_rescue_rate"]
    if fifo_rate is None:
        lines.append(
            f"There were no urgent donations (shelf life of {URGENT_SHELF_LIFE} minutes or less)."
        )
    elif fifo_rate == greedy_rate:
        lines.append(f"Both strategies rescued {fifo_rate:.1f}% of urgent donations.")
    else:
        lines.append(
            f"Greedy rescued {greedy_rate:.1f}% of urgent donations and FIFO rescued "
            f"{fifo_rate:.1f}% ({greedy_rate - fifo_rate:+.1f} points for greedy)."
        )

    return lines


def explain_changes(
    donations: List[Donation],
    recipients: Dict[str, Recipient],
    fifo_assignments: List[Assignment],
    greedy_assignments: List[Assignment],
) -> List[str]:
    """Returns a sentence for every donation that ended up different under greedy."""
    by_id = {d.donation_id: d for d in donations}
    fifo = {a.donation_id: a for a in fifo_assignments}
    greedy = {a.donation_id: a for a in greedy_assignments}
    fifo_order = [a.donation_id for a in fifo_assignments]
    greedy_order = [a.donation_id for a in greedy_assignments]

    # Position each strategy handled each donation at 1 = first
    fifo_pos = {}
    for i, did in enumerate(fifo_order):
        fifo_pos[did] = i + 1
    greedy_pos = {}
    for i, did in enumerate(greedy_order):
        greedy_pos[did] = i + 1

    lines = []
    for donation in donations:
        did = donation.donation_id
        if did not in fifo or did not in greedy:
            continue
        f = fifo[did]
        g = greedy[did]
        f_ok = f.status == "assigned"
        g_ok = g.status == "assigned"

        if not f_ok and not g_ok:
            continue
        if f_ok and g_ok and f.recipient_id == g.recipient_id and f.volunteer_id == g.volunteer_id:
            continue

        intro = f"{did} ({donation.quantity} {donation.food_type}, {shelf_life(donation)} min shelf life)"
        where = f"FIFO handled it at position {fifo_pos[did]} and greedy at position {greedy_pos[did]}."

        if f_ok and not g_ok:
            # If the donations greedy handled before this one that FIFO handled after it
            earlier = greedy_order[:greedy_pos[did] - 1]
            moved_ahead = [x for x in earlier if x in by_id and fifo_pos.get(x, 0) > fifo_pos[did]]
            why = _why_lost(donation, moved_ahead, earlier, greedy, by_id, recipients)
            lines.append(
                f"{intro} was assigned under FIFO (to {_org_name(recipients, f.recipient_id)}) "
                f"but not under greedy. {where} {why}"
            )

        elif g_ok and not f_ok:
            # If the donations FIFO handled before this one that greedy handled after it
            earlier = fifo_order[:fifo_pos[did] - 1]
            moved_behind = [x for x in earlier if x in by_id and greedy_pos.get(x, 0) > greedy_pos[did]]
            why = _why_gained(donation, moved_behind, earlier, fifo, by_id, recipients)
            lines.append(
                f"{intro} was not assigned under FIFO but was assigned under greedy "
                f"(to {_org_name(recipients, g.recipient_id)}). {where} {why}"
            )

        elif f.recipient_id != g.recipient_id:
            lines.append(
                f"{intro} was assigned under both strategies, but FIFO sent it to "
                f"{_org_name(recipients, f.recipient_id)} and greedy sent it to "
                f"{_org_name(recipients, g.recipient_id)}. {where} Greedy's different order "
                f"changed which recipients still had room when its turn came."
            )

        else:
            lines.append(
                f"{did} went to the same recipient under both strategies but was picked up by "
                f"{f.volunteer_id} under FIFO and {g.volunteer_id} under greedy, because greedy "
                f"used up the volunteers' pickups in a different order."
            )

    return lines


def _why_lost(donation, moved_ahead, earlier, decisions, by_id, recipients):
    did = donation.donation_id

    if _had_room(donation, earlier, decisions, by_id, recipients):
        # If a recipient still had room so it was the volunteers that ran out
        if moved_ahead:
            reason = _reason([by_id[x] for x in moved_ahead], [donation])
            return (
                f"Greedy handled {', '.join(moved_ahead)} first ({reason}), and by then no "
                f"volunteer was free to take {did}."
            )
        return f"By the time greedy reached it, no volunteer was free to take {did}."

    # If there's no room left & only blame the donations that went somewhere that takes this food
    took_room = [x for x in moved_ahead if _went_to_match(decisions[x], donation, recipients)]
    if not took_room:
        return f"By the time greedy reached it, every recipient that takes {donation.food_type} was full."
    places = ", ".join(sorted({_org_name(recipients, decisions[x].recipient_id) for x in took_room}))
    reason = _reason([by_id[x] for x in took_room], [donation])
    return (
        f"Greedy handled {', '.join(took_room)} first ({reason}), which used up the room at "
        f"{places} that {did} needed."
    )


def _why_gained(donation, moved_behind, earlier, decisions, by_id, recipients):
    if _had_room(donation, earlier, decisions, by_id, recipients):
        # If a recipient had room under FIFO too so it was the volunteers that ran out
        if moved_behind:
            reason = _reason([donation], [by_id[x] for x in moved_behind])
            return (
                f"Under FIFO no volunteer was free by its turn. Greedy moved it ahead of "
                f"{', '.join(moved_behind)} ({reason}), so a volunteer was still free."
            )
        return "Under FIFO no volunteer was free by its turn, and greedy's order left one free."

    # If under FIFO there was no room left then this names the donations that took it
    took_room = [x for x in moved_behind if _went_to_match(decisions[x], donation, recipients)]
    if not took_room:
        return (
            f"Under FIFO every recipient that takes {donation.food_type} was full by its turn, "
            f"and greedy's order left room."
        )
    places = ", ".join(sorted({_org_name(recipients, decisions[x].recipient_id) for x in took_room}))
    reason = _reason([donation], [by_id[x] for x in took_room])
    return (
        f"Under FIFO it came after {', '.join(took_room)}, which used up the room at {places}. "
        f"Greedy moved it ahead ({reason}), so there was still room."
    )


def _reason(first, later):
    # Only says "less shelf life" if that's actually true for all of them
    if max(shelf_life(d) for d in first) < min(shelf_life(d) for d in later):
        return "less shelf life"
    return "higher greedy priority"


def _had_room(donation, earlier, decisions, by_id, recipients):
    # Adds up how much each recipient had already taken before this donation's turn
    used = {}
    for x in earlier:
        a = decisions[x]
        if a.status == "assigned" and x in by_id:
            used[a.recipient_id] = used.get(a.recipient_id, 0) + by_id[x].quantity

    # Checks if any recipient that takes this food still had room for it
    for r in recipients.values():
        if r.accepts(donation.food_type) and donation.ready_time <= r.closing_time:
            if r.capacity - used.get(r.recipient_id, 0) >= donation.quantity:
                return True
    return False


def _went_to_match(decision, donation, recipients):
    # True if `decision` sent its donation to a recipient that also takes this food
    if decision.status != "assigned" or decision.recipient_id not in recipients:
        return False
    return recipients[decision.recipient_id].accepts(donation.food_type)


def _org_name(recipients, recipient_id):
    if recipient_id in recipients:
        return recipients[recipient_id].org_name
    return str(recipient_id)
