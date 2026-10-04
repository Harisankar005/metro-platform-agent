# Intelligent Metro Platform Allocation and Dynamic Scheduling Agent

## 1. Title
Intelligent Metro Platform Allocation and Dynamic Scheduling Agent using Classical AI and Constraint Satisfaction.

This project uses classical AI techniques and does not use machine learning, deep learning, or reinforcement learning. The proposed agent uses CSP, backtracking, MRV, forward checking, rule-based reasoning, and dynamic replanning.

---

## 2. Problem
In high-density urban transit systems, metro stations handle multiple arriving and departing trains across a limited number of platforms. The primary challenge is allocating trains to platforms while:
- Avoiding platform conflicts (two trains occupying the same platform simultaneously).
- Minimizing train delays and passenger waiting times.
- Respecting platform compatibility constraints (length, power, direction).
- Managing real-world operational disruptions such as train delays and emergency platform closures through dynamic replanning.

---

## 3. Environment
The environment models a busy terminal/junction metro station:
- **Platforms**: 4 platforms with specific compatibility rules and dynamic availability.
- **Trains**: 8 scheduled metro trains with varying arrival times, dwell durations, directions, and passenger loads.
- **Disruptions**: Train delays and unplanned platform closures occurring chronologically during station operation.

---

## 4. Inputs
The scheduling agent processes operational inputs loaded from `trains.csv` and dynamic station status:
- **arrival / departure**: Scheduled arrival and departure times (hh:mm).
- **delay**: Injected external operational delay in minutes.
- **direction**: Travel direction (e.g., North, South).
- **priority**: Operational priority category (Emergency, High, Normal).
- **passengers**: Passenger volume on board the train.
- **platforms**: Allowed platform compatibility list for each train (e.g., `1|2`, `2|3`, `2|4`).
- **platform availability**: Current open/closed status of each station platform.
- **existing assignments**: Active platform occupancy by trains already inside the station.

---

## 5. Decisions
Internally, the agent takes four explicit decisions:
- **ASSIGN**: Allocate an arriving train to a valid, conflict-free platform.
- **HOLD**: Temporarily hold a train outside the platform when all compatible platforms are occupied.
- **REASSIGN**: Shift a previously scheduled train to an alternate platform following a disruption.
- **DEPART**: Mark a train as departed after its dwell time is completed.

---

## 6. Classical AI Techniques
The proposed agent is designed around classical AI principles:
- **Constraint Satisfaction Problem (CSP)**:
  - **Variables**: Trains requiring platform allocation.
  - **Domains**: Compatible open platforms.
  - **Constraints**: No two trains may overlap on the same platform (`arrival1 < departure2 AND arrival2 < departure1`).
- **Backtracking Search**: Recursive depth-first search exploring valid platform assignments.
- **Minimum Remaining Values (MRV)**: Selects the most constrained unassigned train (fewest remaining valid platforms) first. Ties are broken using train priority (Emergency > High > Normal) and passenger count.
- **Forward Checking**: After each assignment, removes incompatible slots from the domains of remaining unassigned trains. If any train has zero valid platforms remaining, the branch is immediately pruned.
- **Rule-Based Reasoning**:
  - Closed platform $\rightarrow$ immediately pruned from all domains.
  - No valid platform at arrival $\rightarrow$ mark as `HOLD`.
  - Platform becomes available $\rightarrow$ retry held train at earliest free slot.
  - Priority rule $\rightarrow$ `Emergency > High > Normal` for resource allocation.
- **Dynamic Replanning**: When a disruption occurs, fixes past/departed trains, updates station state, and re-runs CSP search on future affected trains.

---

## 7. Four Algorithms
The project implements and compares four distinct algorithms:
1. **FCFS (First-Come, First-Served)**:
   - Sorts trains strictly by arrival time.
   - Assigns the first compatible platform without backtracking, MRV, forward checking, or dynamic replanning.
   - Causes platform conflicts when platforms are congested.
2. **Greedy**:
   - Evaluates compatible platforms and picks the one offering the smallest immediate waiting delay.
   - Eliminates conflicts by shifting arrival times, but incurs high cumulative passenger delay and lacks dynamic replanning.
3. **Basic CSP**:
   - Standard recursive backtracking solver in fixed arrival order.
   - No MRV variable ordering, no forward checking, no priority tie-breaking, and no dynamic replanning.
   - Explores more nodes and backtracks heavily compared to the proposed agent.
4. **Proposed Agent**:
   - Integrates CSP backtracking with MRV, forward checking, priority rules, and dynamic replanning.
   - Guarantees 0 platform conflicts, minimizes passenger waiting time, and dynamically resolves real-time disruptions.

---

## 8. Performance Measures
The system measures seven quantitative metrics directly derived from program execution:
1. **Average train delay**: Mean scheduling-caused waiting time per train (minutes).
2. **Passenger waiting time**: Total passenger-minutes incurred ($\sum \text{passenger load} \times \text{scheduler wait}$).
3. **Number of platform conflicts**: Count of overlapping train intervals on identical platforms.
4. **Successful train assignments**: Number of trains successfully allocated to platforms.
5. **Platform utilization**: Percentage of station capacity utilized over the active schedule span.
6. **Number of reassignments**: Count of trains moved to alternate platforms during dynamic replanning.
7. **Algorithm execution time**: Real execution duration in milliseconds measured with `time.perf_counter()`.
8. **Nodes expanded & Backtracks**: Search tree effort tracked for CSP algorithms.

---

## 9. Scenarios
The CLI evaluates five test scenarios:
1. **Normal**: Standard station operations with 4 open platforms and 0 injected delay.
2. **Delayed Train**: Train T3 is delayed by 5 minutes at 09:05, triggering dynamic schedule adjustment.
3. **Platform Closure**: Platform 2 closes unexpectedly at 09:05, requiring re-allocation of affected trains.
4. **Platform Competition**: Multiple trains arrive concurrently requiring platforms 1 and 2.
5. **Combined**: Train T3 is delayed by 4 minutes at 09:05, followed by emergency closure of Platform 2 at 09:07.

---

## 10. Run Instructions

### Prerequisites
Python 3.8+ (Standard Library only; no external dependencies required).

### Execution
From the project folder:
```bash
python metro_agent.py
```

To run a specific scenario (1 to 5):
```bash
python metro_agent.py 1    # Normal
python metro_agent.py 2    # Delayed Train
python metro_agent.py 3    # Platform Closure
python metro_agent.py 4    # Platform Competition
python metro_agent.py 5    # Combined
```

---

## 11. Limitations
This project is a simplified academic simulation and deliberately does not model:
- Real railway signalling logic (interlocking, aspect signals).
- Detailed track switches, turnouts, and physical headway distances.
- Real-time hardware telemetry and IoT track sensors.
- Individual passenger walking speeds or dwell time extensions based on crowding.
- Complete station infrastructure constraints (overhead catenary, maintenance yard feeds).

---

## 12. Viva Explanation (Two-Minute Summary)
> "We simulate a metro station where multiple trains need to be assigned to a limited number of platforms. The main problem is that trains cannot use the same platform at overlapping times.
>
> We model the problem as a Constraint Satisfaction Problem (CSP). The trains are the variables and their compatible platforms are the domains. Backtracking searches for a valid assignment. MRV chooses the train with the fewest available platforms, and forward checking removes choices that are no longer possible.
>
> We also use simple rules for train priority and platform closures. If a disruption occurs, the proposed agent replans the affected trains.
>
> Finally, we compare the proposed agent with FCFS, Greedy, and Basic CSP using delay, passenger waiting time, conflicts, successful assignments, platform utilization, reassignments, and execution time."

---

## 13. Compliance with Project Abstract
- **Problem**: Solves dynamic platform allocation, conflict avoidance, delay minimization, and disruption management.
- **Environment**: Simulated metro station with 4 platforms, 8 trains, occupancy tracking, and disruptions.
- **Information**: Uses arrival/departure times, delays, directions, priorities, passenger loads, compatibility, and closures.
- **Decisions**: Employs ASSIGN, HOLD, REASSIGN, and DEPART actions.
- **Classical AI**: Employs CSP, recursive backtracking, MRV, forward checking, rule-based reasoning, and dynamic replanning.
- **Performance Evaluation**: Measures average delay, passenger waiting, platform conflicts, successful assignments, platform utilization, reassignments, execution time, and CSP search tree statistics.
- **Algorithm Comparison**: Benchmarks FCFS, Greedy, Basic CSP, and Proposed Agent across all scenarios with automated conflict verification (`Proposed Agent Conflict Check: PASS`).
