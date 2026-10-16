# FIFO vs Greedy Comparison Report

CPSC 335, Group 6 (John, Ian, Andrew)

# What we compared

For this report we ran both of our strategies on the same data and compared
the 8 metrics from the project brief. FIFO goes through the donations in the
order they come in and gives each one the first recipient and volunteer that
work. Greedy matches donations the exact same way & it just changes the order.
It goes by shelf life (expiry_time to ready_time) and handles the shortest one
first. If two donations are tied, then the larger quantity goes first, then the
earlier ready time, then whichever one is first in the file.

Each strategy gets its own copy of the data, so both of them start with full
capacity. We counted a donation as urgent if it had 60 minutes of shelf life or
less. All of the numbers below are from running main.py and what_changed.py on
each scenario.

# Scenario 1: the original sample data (data/)

| Metric | FIFO | Greedy | Greedy - FIFO |
|---|---|---|---|
| Donations received | 8 | 8 | 0 |
| Donations assigned | 7 | 7 | 0 |
| Donations unassigned | 1 | 1 | 0 |
| Food quantity rescued | 170 | 170 | 0 |
| Food quantity at risk | 100 | 100 | 0 |
| Urgent rescue rate | 100.0% (2 of 2) | 100.0% (2 of 2) | 0 |
| Recipient capacity utilization | 68.0% | 68.0% | 0 |
| Volunter capacity utilization | 27.4% | 27.4% | 0 |

Both strategies ended up saving the exact same donations here & the only thing
that changed was where some of them went. Greedy handles D-1008 first since it
only has 15 minutes of shelf life, so it gets Community Shelter instead of
Neighbors Pantry. This pushes D-1004 and D-1006 over to Neighbors Pantry.
D-1002 and D-1003 still go to the same pantry so they just get picked up by
V-302 instead of V-301. D-1005 doesn't get placed by either one because it's
100 meals and the biggest recipient only holds 90, so the order doesn't matter
for it.

When there's enough room for everything urgent, the order doesn't change
much.

# Scenario 2: tight capacity (data/tight_capacity/)

This scenario was intentional so the two strategies would actually give
different results. There are four prepared meal donations (95 meals total) but
theres only one recipient that takes prepared meals, Eastside Shelter, and it 
can only hold 60.

| Metric | FIFO | Greedy | Greedy - FIFO |
|---|---|---|---|
| Donations received | 6 | 6 | 0 |
| Donations assigned | 4 | 5 | +1 |
| Donations unassigned | 2 | 1 | -1 |
| Food quantity rescued | 105 | 100 | -5 |
| Food quantity at risk | 35 | 40 | +5 |
| Urgent rescue rate | 33.3% (1 of 3) | 100.0% (3 of 3) | +66.7 pts |
| Recipient capacity utilization | 65.6% | 62.5% | -3.1 pts |
| Volunteer capacity utilization | 35.0% | 33.3% | -1.7 pts |

With FIFO, D-2001 shows up first and takes 40 of the 60 spots, then D-2002
takes the last 20. This means D-2003 and D-2006 dont fit even though they're
both urgent (45 and 40 minutes of shelf life). This means FIFO only saves 1 
of the 3 urgent donations.

Greedy does D-2002, D-2006 and D-2003 first since they have the least shelf
life so all 3 urgent ones get in. That uses 55 of the 60 spots though, so by
the time greedy gets to D-2001 (40 meals) there's only room for 5. D-2001 came
in first and had 4 hours of shelf life left, and it still got left out. This is
our starvation example. This is what greedy prints for it:

D-2005 shows up in that list because greedy did handle it first but since it's 
bread it went to Southside Pantry and didn't take any of the shelter's space.

Greedy assigns one more donation overall because it basically traded one big
donation (D-2001 - 40 meals) for two smaller urgent ones (D-2003 and D-2006 - 35
meals together). This is also why it rescues 5 fewer meals. Both utilization
numbers just follow the food rescued since the total capacity stays the same
(160 for recipients & 300 for volunteers). The final difference is D-2004
which goes to the same pantry either way but gets a different volunteer.

# Trade-offs

Greedy's local choice is simple in the sense that very time it picks the next donation,
it takes the one with the least shelf life and gives it first pick of whatever
space and volunteers are left. It never goes back and changes an earlier choice.

We feel like this is reasonable for food since something that expires in 30
minutes & needs to be refrigerated can't wait but something with a longer shelf
life at room temperature could still get picked up later or go somewhere else. 
In the tight scenario it took the urgent rescue rate from 33.3% to 100%.

It's unfortunately not better at everything though. It can rescue less food overall 
such as where it saved D-2003 and D-2006 (35 meals) but lost D-2001 (40 meals). 
It also doesn't look ahead as well as we'd hoped. For example, Once D-2002 and D-2006 
are placed there's only room for 30 more meals, so D-2001 can't fit anymore and greedy 
never reconsiders. FIFO actually filled the shelter all the way (60 of 60) while greedy 
only gotto 55. Quantity only matters as a tie-breaker too, so greedy doesn't care that
D-2001 is the biggest donation.

We believe the biggest fairness problem is starvation. For example, D-2001 arrived first 
and still got left out. A donation with a long shelf life will always lose to more urgent
ones & since shelf life is only calculated once from the CSV, waiting longer
doesn't move it up. If urgent donations kept coming in then a donation like that
could pretty much never get placed. FIFO has the opposite problem since it
ignores urgency completely & early donations can take space that something
about to expire needed (D-2003 and D-2006 here).

Some ways we could fix this would be raising a donations' priority the longer
it waits, saving some space for urgent donations, or comparing against an
optimization solver. We didn't add these initially since the brief lists them 
more as stretch features.

# Limitations

- We only tested two small artificial scenarios so this shows how the rules
  behave but not how they'd do with real actual data.
- There's no travel time so every pickup is scheduled at the donation's ready
  time and pickup areas aren't enforced.
- The utilization numbers don't consider things likeclosing times or volunteer
  time windows/shifts.
- Both strategies use first-feasible matching so neither one looks for the
  best recipient but instead does just the first one that works.
- We picked the 60 minute urgent cutoff ourselves but it's not an actual food
  safety rule.
