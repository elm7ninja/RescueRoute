# RescueRoute

Surplus Food Matching & Pickup Planner — CPSC 335 Group Project

An explainable prototype that matches time-sensitive food donations to
compatible recipient organizations and volunteer drivers, comparing a FIFO
baseline against a greedy urgency-first strategy.

> This is an educational prototype. It is not approved for real food-safety,
> medical, or emergency operations. All sample data is simulated.

## Status: Week 1 (baseline)

- [x] Repository structure
- [x] Data model (`src/models.py`)
- [x] Validation + CSV loading (`src/data_loader.py`)
- [x] FIFO baseline (`src/fifo.py`)
- [x] Sample input files (`data/`)
- [x] 5 initial tests (`tests/test_fifo.py`)
- [ ] Greedy urgency-first strategy — **Week 2**
- [ ] Metrics + FIFO-vs-greedy comparison report — **Week 2**
- [ ] 10 total tests, fairness/starvation case — **Week 2**
- [ ] Demo video, final report, contribution statements — **Week 3**

## Setup

Requires Python 3.9+, standard library only (no external dependencies for
the baseline).

```bash
git clone <your-repo-url>
cd rescueroute
python3 -m venv venv && source venv/bin/activate   # optional
python3 src/main.py
```

Run the tests:

```bash
python3 -m unittest discover -s tests -v
# or, if pytest is installed:
python3 -m pytest tests/ -v
```

## Data Schema

All time fields are integer **minutes since simulation start** (e.g. `0` =
start of the day, `90` = 90 minutes later). This keeps the baseline
deterministic and easy to test without real-clock parsing.

### `data/donations.csv`
| Field | Type | Notes |
|---|---|---|
| donation_id | str | must be unique |
| donor_name | str | |
| food_type | str | e.g. `prepared_meals`, `produce`, `bread`, `dairy` |
| quantity | int | must be > 0 |
| ready_time | int | when the donation becomes available for pickup |
| expiry_time | int | last minute pickup is still valid; must be ≥ ready_time |
| pickup_area | str | e.g. `north`, `south` |

### `data/recipients.csv`
| Field | Type | Notes |
|---|---|---|
| recipient_id | str | must be unique |
| org_name | str | |
| accepted_food_types | str | `\|`-separated, e.g. `prepared_meals\|bread` |
| capacity | int | must be > 0 |
| area | str | |
| closing_time | int | latest minute a pickup can arrive |

### `data/volunteers.csv`
| Field | Type | Notes |
|---|---|---|
| volunteer_id | str | must be unique |
| vehicle_capacity | int | must be > 0 |
| area | str | |
| available_start | int | |
| available_end | int | must be ≥ available_start |
| max_pickups | int | must be > 0 |

### Assignment (in-memory only for now)
`donation_id, recipient_id, volunteer_id, scheduled_time, decision_reason, status`

## Algorithms

### A. FIFO baseline (implemented)
Processes donations in arrival order (input file order). For each donation,
assigns the **first feasible** recipient (accepts the food type, has enough
remaining capacity, and can be reached before both the donation's expiry and
the recipient's closing time) and the **first feasible** volunteer (enough
vehicle capacity, available at the donation's ready time, under its max
pickups). Every donation — matched or not — produces a human-readable
`decision_reason`.

### B. Greedy urgency-first strategy (Week 2)
Planned rule (to be finalized in Week 2): **schedule donations with the
least remaining shelf life first** (`expiry_time - ready_time`); ties broken
by larger quantity first, then by earlier `ready_time`. Will use a `heapq`
priority queue keyed on `(remaining_shelf_life, -quantity, ready_time)`.

## Complexity (baseline)

Let `D` = number of donations, `R` = number of recipients, `V` = number of
volunteers.

- Loading/validation: `O(D + R + V)` — one pass per file, set lookups for
  duplicate-ID detection.
- FIFO matching: for each of the `D` donations we scan up to `R` recipients,
  and for a feasible recipient, up to `V` volunteers → **`O(D · (R + V))`**
  worst case. No sorting step is needed since arrival order is just input
  order.
- Space: `O(D + R + V)` for the dictionaries plus `O(D)` for the assignment
  list.

A full complexity write-up (including the greedy strategy's `O(D log D)`
heap operations) will be added in Week 2.

## Data structures used

| Need | Structure | Reason |
|---|---|---|
| Lookup by ID | `dict` | O(1) direct retrieval |
| Duplicate-ID detection | `set` | O(1) membership testing |
| Food-type compatibility | `set` | natural set-membership check |
| FIFO baseline order | `list` | preserves arrival/input order |
| Assignment history | `list` | ordered audit output |

## Team

| Role | Member | Responsibilities |
|---|---|---|
| Algorithm & Optimization Lead | John  | FIFO scheduler, greedy rule, priority selection, complexity analysis, strategy comparison |
| Data & Matching Lead | _TBD_ | Input files, validation, compatibility checks, capacity rules, data structures, test data |
| Product & Quality Lead | _TBD_ | Explainable output, metrics, tests, README, demo materials, CLI polish |

All members participate in design discussion, code review, debugging,
testing, and documentation review.

## Limitations (Week 1)

- Pickup area is stored but not yet enforced as a hard matching constraint.
- Only the FIFO baseline exists; no strategy comparison yet.
- No fairness/starvation analysis yet (planned for Week 2 testing).
