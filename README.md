# RescueRoute

Surplus Food Matching & Pickup Planner — CPSC 335 Group Project

RescueRoute is an explainable Python application that matches time-sensitive food donations
to compatible recipient organizations and volunteer drivers. It compares a FIFO baseline against 
a greedy urgency-first scheduling strategy.

> This is an educational prototype. It is not approved for real food-safety,
> medical, or emergency operations. All sample data is simulated.

## Project Status

Core application implemented and tested.

- [x] Project structure and data models
- [x] CSV loading and initial data validation
- [x] FIFO scheduling algorithm
- [x] Greedy urgency-first algorithm
- [x] Explainable assignment and rejection messages
- [x] FIFO vs. Greedy metrics comparison
- [x] Automated tests (29 passed)
- [x] Sample input data
- [x] Food Type and area validation
- [x] Final validation and matching review
- [x] PowerPoint presentation and demo video
- [x] Final report and contribution statements

## Setup

RescueRoute is a collaborative CPSC 335 group project developed in Python.

### Requirements

- Python 3.9 or newer
- No additional Python libraries required

### Running the Application 

Download the project from our team's GitHub repository:

https://github.com/elm7ninja/RescueRoute

Open the RescueRoute folder in VS Code or another development environment

From the project's root directory, run: 

```bash
python src/main.py
```

The application will display:
- FIFO scheduling results
- Greedy urgency-first scheduling results
- Assignment and rejection explanations
- FIFO vs. Greedy performance metrics

### Running Automated Tests

RescueRoute uses Python's unittest framework to verify the application's functionality.
To run the automated tests, open a terminal in the project's root directory and enter:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v
```

The tests cover:
- Data validation
- FIFO and Greedy scheduling
- Recipient and volunteer matching
- Capacity and availability constraints
- Performance metrics
- Edge cases and assignment explanations

All 29 automated tests passed during the latest reported test run.



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

RescueRoute uses two scheduling algorithms to assign food donations to 
compatible recipient organizations and volunteer drivers.
Our application compares FIFO and Greedy urgency-first scheduling 
to evaluate how different priorities affect assignment decisions. 


### A. FIFO baseline (implemented)

The First-In, First-Out (FIFO) algorithm processes donations in arrival order,
based on their order in the input file.

For each donation, FIFO selects the first feasible recipient and volunteer.

The matching process checks:
- Whether the recipient accepts the donation's food type
- Whether the recipient has enough remaining capacity
- Whether the donation can be scheduled before expiration and recipient closing time
- Whether a volunteer is available at the scheduled time
- Whether the volunteer has enough vehicle capacity
- Whether the volunteer has remaining pickup slots

Every donation produces a human-readable explanation describing why it was assigned or left unassigned.

**Advantages**
- Simple and predictable scheduling
- Preserves donation arrival order
- Easy to implement and explain 

** Limitations**
- Does not consider donation urgency when determining order
- Earlier donations may use resources needed by more urgent donations

### B. Greedy Urgency-First Strategy (Implemented)

The Greedy algorithm prioritizes donations based on their remaining shelf life instead of their arrival order.

Remaining shelf life is calculated as:

`expiry_time - ready_time`

Our Greedy algorithm follows these priority rules:

1. Donations with the shortest remaining shelf life are processed first.
2. If two donations have equal shelf life, the larger quantity is prioritized.
3. If still tied, the donation with the earlier ready time is prioritized.
4. Original input order is used as the final tie-breaker.

The algorithm uses Python's `heapq` priority queue to organize donations according to urgency.

For each donation, it selects the first feasible recipient and volunteer while checking compatibility, capacity, and time constraints.

The algorithm also generates human-readable explanations describing why donations were assigned, rejected, or deferred.

**Advantages:**
- Prioritizes time-sensitive donations.
- Uses an explainable scheduling rule.
- May help urgent donations receive resources first.

**Limitations:**
- Does not guarantee a globally optimal schedule.
- Less urgent donations may be deferred.
- May produce the same overall results as FIFO.

## Time Complexity

Let:
- D = Number of donations
- R = Number of recipients
- V = Number of volunteers

### Data Loading and Validation 

Time Complexity: `O(D + R + V)`

The application processes donation, recipient, and volunteer records. 
Dictionaries and sets provide efficient lookups and duplicate detection.

### FIFO Algorithm

Time Complexity: `O(D * (R + V))`

FIFO processes donations in arrival order. For each donation, 
it searches for the first compatible recipient and volunteer.

In the worst case, the algorithm may examine all recipients and volunteers
before finding a feasible assignment. 

### Greedy Algorithm

Time Complexity: `O(D log D + D * (R + V) + D^2)`

The Greedy algorithm uses a priority queue to prioritize donations based on remaining shelf life.

- Heap operations require `O(D log D)` total.
- Recipient and volunteer matching requires `O(D * (R + V))`.
- Generating deferred-donation explanations can require `O(D^2)` work in the worst case.

### Space Complexity 

The core data structures use `O(D + R + V)` space for donations, recipients, volunteers,
assignments, and the priority queue.

The Greedy algorithm may additionally produce `O(D^2)` total explanation text in the worst case.

## Data structures Used

| Need | Structure | Reason |
|---|---|---|
| Lookup by ID | `dict` | Fast direct retrieval |
| Duplicate-ID detection | `set` | Fast membership testing |
| Food-type compatibility | `set` | Checks accepted food categories |
| FIFO processing | `list` | Preserves arrival order |
| Greedy priority selection | `heapq` | Prioritizes donations based on urgency |
| Assignment history | `list` | Records scheduling decisions |
| Performance metrics | `dict` | Stores calculated metrics |

## Performance Metrics

RescueRoute calculates eight performance metrics to evaluate and compare FIFO and Greedy scheduling.

The metrics include:

1. Donations received
2. Donations assigned
3. Donations unassigned
4. Food quantity rescued
5. Food quantity at risk
6. Urgent rescue rate
7. Recipient capacity utilization
8. Volunteer capacity utilization

Urgent donations are defined as having 60 minutes or less of remaining shelf life.

### FIFO vs. Greedy Results

The following results were obtained using our sample dataset:

| Metric | FIFO | Greedy |
|---|---:|---:|
| Donations received | 8 | 8 |
| Donations assigned | 7 | 7 |
| Donations unassigned | 1 | 1 |
| Food quantity rescued | 170 | 170 |
| Food quantity at risk | 100 | 100 |
| Urgent rescue rate | 100% | 100% |
| Recipient capacity utilization | 68.0% | 68.0% |
| Volunteer capacity utilization | 27.4% | 27.4% |

Both strategies produced identical overall metrics using the sample dataset, even though donations were processed in different orders.

Additional test scenarios demonstrate that FIFO and Greedy can produce different assignment outcomes when resources are limited.

Our team's comparison tool, `src/what_changed.py`, provides further explanations of how and why scheduling decisions differ.

To run the comparison tool:

    python src/what_changed.py

To run the tight-capacity scenario:

    python src/what_changed.py data/tight_capacity

## Automated Testing

RescueRoute uses Python's `unittest` framework to verify the application's behavior.

The automated tests cover:

- Successful donation matching
- Duplicate donation IDs
- Expired donations
- Food type and area validation
- Insufficient recipient capacity
- Volunteer availability and vehicle capacity
- Donations competing for limited resources
- Empty input datasets
- FIFO and Greedy producing different results
- Fairness and deferred donations
- Performance metrics
- Human-readable assignment explanations

Ian reported that all 29 automated tests passed after adding five validation tests. 
The final merged version should be tested again before submission.


## Team Contributions

| Role | Member | Contributions |
|---|---|---|
| Algorithm & Optimization Lead | John | Integrated FIFO and Greedy into main.py, added the metrics comparison display, ran automated tests, and updated the README documentation |
| Data & Matching Lead | Ian | Added food type and area validation, reviewed matching logic, and expanded automated testing with five additional tests |
| Product & Quality Lead | Andrew | Developed the FIFO vs. Greedy comparison tool, added explanations for scheduling differences, and completed the comparison report |

All three team members contributed to developing, reviewing, and testing the RescueRoute application.

## Limitations

RescueRoute is an educational prototype with several limitations:

- All project data is simulated.
- The application does not calculate actual driving distances or travel times.
- Greedy scheduling does not guarantee a globally optimal solution.
- Less urgent donations may be deferred when resources are limited.
- The application currently uses a command-line interface instead of a graphical dashboard.
- RescueRoute is not approved for real-world food-safety or emergency operations.

## Future Improvements

Possible future improvements include:

- Real-time route planning and distance calculations
- An interactive web dashboard
- Additional fairness rules
- Improved scheduling optimization
- Real-time volunteer availability tracking
- More realistic scheduling constraints

## Conclusion

RescueRoute demonstrates how FIFO and Greedy scheduling algorithms can help 
coordinate time-sensitive surplus food donations. 

By comparing both algorithms, our team explored how scheduling priorities, resource constraints,
and data structures influence donation assignments. 

The project highlights the importance of algorithm efficiency, explainable decisions, and automated testing. 

## Final Presentation and Demo
- [Final Presentation](docs/RescueRoute_Final_Presentation.pdf)
- [Demo Video](https://drive.google.com/file/d/1mtZrqXZrCWwmMGQYyZC-5z6JlUxK1cXE/view?usp=sharing)
- [Individual Contribution Statements](docs/comparison_report.md)
