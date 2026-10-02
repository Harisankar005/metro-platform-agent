# Intelligent Metro Platform Allocation and Dynamic Scheduling Agent

> **Classical AI Implementation**: This project strictly uses classical Artificial Intelligence techniques:
> - **Constraint Satisfaction Problem (CSP)** formulation
> - **Backtracking search**
> - **Minimum Remaining Values (MRV)** heuristic ("Fail-First")
> - **Forward Checking (FC)** constraint propagation
> - **Least Constraining Value (LCV)** value ordering
> - **Rule-Based Dynamic Replanning** under disruptions
>
> It does **NOT** use Machine Learning, Deep Learning, Reinforcement Learning, LLMs, or external optimization solvers.
> It is an educational and academic demonstration and does not claim real-world railway dispatch capability.

---

## Table of Contents
1. [Project Overview & Problem Statement](#1-project-overview--problem-statement)
2. [Classical AI Formulation (CSP)](#2-classical-ai-formulation-csp)
3. [Core Search & Heuristics](#3-core-search--heuristics)
4. [Rule-Based Reasoning & Dynamic Replanning](#4-rule-based-reasoning--dynamic-replanning)
5. [Infeasibility Handling & HOLD Semantics](#5-infeasibility-handling--hold-semantics)
6. [Baseline Algorithms](#6-baseline-algorithms)
7. [Evaluation Metrics](#7-evaluation-metrics)
8. [Comprehensive Benchmark Results](#8-comprehensive-benchmark-results)
9. [Demonstration of Dynamic Replanning](#9-demonstration-of-dynamic-replanning)
10. [Limitations](#10-limitations)
11. [How to Run (CLI & Streamlit UI)](#11-how-to-run-cli--streamlit-ui)
12. [Viva-Oriented Q&A Reference](#12-viva-oriented-qa-reference)

---

## 1. Project Overview & Problem Statement

In high-density urban metro terminals, berthing trains onto platforms during normal operations is straightforward. However, unexpected disruptions—such as train arrival delays, sudden emergency platform closures, and simultaneous arrivals of competing trains—quickly invalidate static schedules.

A static dispatcher or naive algorithm causes platform occupancy overlaps, safety violations, and excessive passenger waiting time.

The **Intelligent Metro Platform Allocation Agent** dynamically manages platform assignments by:
- Enforcing physical compatibility between trains and platforms.
- Preventing overlapping occupancies on the same platform.
- Prioritizing service tiers: **Emergency > High > Normal**.
- Gracefully placing trains on **HOLD** when capacity is exceeded and recovering them as berths clear.
- Dynamically perceiving disruption events and replanning future assignments while protecting frozen (already arrived) trains.

---

## 2. Classical AI Formulation (CSP)

The platform allocation problem is modeled strictly as a **Constraint Satisfaction Problem (CSP)**:

### Variables
Each incoming train is a CSP variable:
```text
Variables X = { T1, T2, T3, ..., Tn }
```

### Domains
The domain of train `Ti` consists of all physical platforms that are compatible with the train and not currently closed:
```text
Domain(Ti) = { P in compatible_platforms(Ti) | P is not closed }
```

### Constraints
1. **Platform Availability**: The assigned platform must be open throughout the train's effective occupancy window `[effective_arrival, effective_departure)`.
2. **Train-Platform Compatibility**: The assigned platform must be in `compatible_platforms(Ti)`.
3. **Non-Overlapping Berthing**: No two trains `TA` and `TB` on the same platform may overlap in time:
```text
Two trains overlap if:
arrival_A < departure_B AND arrival_B < departure_A
```

---

## 3. Core Search & Heuristics

The core search engine is implemented in `metro_agent.py` using recursive **Backtracking**:

```text
                  Choose Unassigned Train
                  (MRV Heuristic Selection)
                             |
                             v
                 Order Compatible Platforms
                 (Least Constraining Value)
                             |
                             v
                   Check CSP Constraints
               (Open, Compatible, Non-overlap)
                             |
              +--------------+--------------+
            Valid                         Invalid
              |                             |
              v                             v
       Tentative Assign               Try Next Value
              |
              v
       Forward Checking
   (Prune overlapping domains)
              |
      +-------+-------+
   Domains OK    Domain Empty
      |               |
      v               v
   Recurse        Backtrack (Undo)
```

- **Minimum Remaining Values (MRV)** ("Fail-First" Principle): At each step, the solver selects the unassigned train with the smallest number of valid physical platform options. Ties are broken by Priority (`Emergency > High > Normal`), then earliest arrival.
- **Forward Checking (FC)**: After assigning train `T` to platform `P`, Forward Checking immediately removes `P` from the domains of all unassigned trains whose time windows overlap with `T`. If any unassigned train's domain becomes empty, the solver immediately backtracks without exploring dead-end subtrees.
- **Least Constraining Value (LCV)**: Platforms that rule out the fewest choices for other unassigned trains are evaluated first.

---

## 4. Rule-Based Reasoning & Dynamic Replanning

The system operates across a discrete timeline with timestamped disruption events:

- **Rule 1: Closed Platform**: If platform `P` closes at time `t`, all unfrozen trains assigned to `P` are unassigned to `HOLD`, and the agent dynamically triggers CSP replanning across the remaining open platforms.
- **Rule 2: Train Delay**: If train `T` is delayed by `delta_t`, its effective arrival and departure times are updated. If this creates a downstream conflict, affected unfrozen trains are replanned.
- **Rule 3: Priority Berthing**: Higher-priority trains (`Emergency > High > Normal`) receive berthing precedence during replanning.
- **Rule 4: Frozen Commitment Protection**: Trains that have already arrived or are dwelling at a platform (`effective_arrival <= event_time`) are **frozen** and cannot be retroactively modified.

---

## 5. Infeasibility Handling & HOLD Semantics

When platform demand exceeds physical capacity (overconstrained state):
- **Proposed Agent**: Evaluates candidates by Priority (`Emergency > High > Normal`), then arrival time. Trains that cannot be berthed without causing a conflict receive `HOLD`.
- **Basic CSP**: Evaluates candidates strictly by arrival time without priority ordering.
- **Dwell Time Preservation**: When a held train is later berthed at time `t_assign`:
```text
effective_arrival   = t_assign
effective_departure = t_assign + original_dwell
scheduling_delay    = t_assign - (scheduled_arrival + injected_delay)
```
The time spent waiting in `HOLD` is counted as scheduling-caused delay. Injected disruption delay is not counted toward scheduling-caused delay.

---

## 6. Baseline Algorithms

To evaluate performance, four distinct approaches are benchmarked on the identical scenarios:

| Algorithm | Backtracking | MRV Heuristic | Forward Checking | Priority Ordering | Dynamic Replanning |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **FCFS** | OFF | OFF | OFF | OFF | OFF |
| **Greedy** | OFF | OFF | OFF | OFF | OFF |
| **Basic CSP** | ON | OFF | OFF | OFF | OFF |
| **Proposed Agent** | **ON** | **ON** | **ON** | **ON** | **ON** |

> **Interpreting Baseline Delay and Conflicts Together**:
> FCFS, Greedy, and Basic CSP do not replan after disruptions. Their stale assignments produce misleadingly low scheduling-caused delay while producing **invalid schedules** (trains berthing on closed platforms or colliding on the same platform). The cost of those invalid schedules is captured by the **unresolved conflicts metric**.

---

## 7. Evaluation Metrics

1. **Average Scheduling-Caused Delay (min)**: Average waiting time caused by `HOLD`. (Excludes injected event delay).
2. **Passenger Waiting Time (passenger-min)**: Sum of `passenger_load * hold_delay` across all trains.
3. **Immediate Assignment Rate (%)**: Percentage of trains berthed at initial schedule generation without `HOLD`.
4. **Final Assignment Rate (%)**: Percentage of trains successfully assigned to an open platform by end of simulation.
5. **Unresolved Platform Conflicts**: Count of overlapping trains, assignments to closed platforms, or incompatible assignments (Target for Proposed Agent: **0**).
6. **Platform Utilization (%)**: `(Occupied Platform Minutes / Available Platform Minutes) * 100` (Excludes closed platform durations).
7. **Reassignments**: Count of trains whose assigned platform was modified during replanning.
8. **Nodes Expanded**: Total search states explored in CSP (0 for FCFS/Greedy).
9. **Backtracks**: Total recursive search reversals upon dead-ends (0 for FCFS/Greedy).
10. **Execution Time (seconds)**: Total CPU execution time measured via `time.perf_counter()`.

---

## 8. Comprehensive Benchmark Results

The following tables contain actual measured data programmatically produced by executing `python metro_agent.py`:

### Scenario 1: Normal Operation (4 Platforms, 10 Trains, 0 Disruptions)
| Metric | FCFS | Greedy | Basic CSP | Proposed Agent |
| :--- | :---: | :---: | :---: | :---: |
| Average Scheduling Delay (min) | 0.00 | 0.00 | 0.00 | **0.00** |
| Passenger Waiting Time (pass-min) | 0 | 0 | 0 | **0** |
| Immediate Assignment Rate (%) | 100.0% | 100.0% | 100.0% | **100.0%** |
| Final Assignment Rate (%) | 100.0% | 100.0% | 100.0% | **100.0%** |
| Unresolved Platform Conflicts | 0 | 0 | 0 | **0** |
| Platform Utilization (%) | 15.18% | 15.18% | 15.18% | **15.18%** |
| Reassignments Triggered | 0 | 0 | 0 | **0** |
| Search Nodes Expanded | 0 | 0 | 14 | **14** |
| Search Backtracks | 0 | 0 | 0 | **0** |
| Execution Time (s) | 0.00006s | 0.00007s | 0.00008s | **0.00021s** |

---

### Scenario 2: Train Delays (Delays injected into T2 [+15m] and T5 [+10m])
| Metric | FCFS | Greedy | Basic CSP | Proposed Agent |
| :--- | :---: | :---: | :---: | :---: |
| Average Scheduling Delay (min) | 0.00 | 0.00 | 0.00 | **0.00** |
| Passenger Waiting Time (pass-min) | 0 | 0 | 0 | **0** |
| Immediate Assignment Rate (%) | 100.0% | 100.0% | 100.0% | **100.0%** |
| Final Assignment Rate (%) | 100.0% | 100.0% | 100.0% | **100.0%** |
| Unresolved Platform Conflicts | 1 (Collision) | 1 (Collision) | 1 (Collision) | **0 (Zero Conflicts)** |
| Platform Utilization (%) | 15.18% | 15.18% | 15.18% | **15.18%** |
| Reassignments Triggered | 0 | 0 | 0 | **7** |
| Search Nodes Expanded | 0 | 0 | 14 | **27** |
| Search Backtracks | 0 | 0 | 0 | **0** |
| Execution Time (s) | 0.00006s | 0.00007s | 0.00008s | **0.00037s** |

---

### Scenario 3: Platform Closure (Platform P2 Closes at 10:04)
| Metric | FCFS | Greedy | Basic CSP | Proposed Agent |
| :--- | :---: | :---: | :---: | :---: |
| Average Scheduling Delay (min) | 0.00 | 0.00 | 0.00 | **5.10** |
| Passenger Waiting Time (pass-min) | 0 | 0 | 0 | **16,970** |
| Immediate Assignment Rate (%) | 100.0% | 100.0% | 100.0% | **100.0%** |
| Final Assignment Rate (%) | 100.0% | 100.0% | 100.0% | **100.0%** |
| Unresolved Platform Conflicts | 3 (Closed Plat) | 3 (Closed Plat) | 3 (Closed Plat) | **0 (Zero Conflicts)** |
| Platform Utilization (%) | 20.08% | 20.08% | 20.08% | **20.08%** |
| Reassignments Triggered | 0 | 0 | 0 | **2** |
| Search Nodes Expanded | 0 | 0 | 14 | **25** |
| Search Backtracks | 0 | 0 | 0 | **4** |
| Execution Time (s) | 0.00005s | 0.00006s | 0.00008s | **0.00051s** |

---

### Scenario 4: Platform Conflict (Multiple Trains Competing for P1)
| Metric | FCFS | Greedy | Basic CSP | Proposed Agent |
| :--- | :---: | :---: | :---: | :---: |
| Average Scheduling Delay (min) | 0.00 | 0.00 | 0.00 | **10.12** |
| Passenger Waiting Time (pass-min) | 0 | 0 | 0 | **45,100** |
| Immediate Assignment Rate (%) | 62.5% | 62.5% | 62.5% | **62.5%** |
| Final Assignment Rate (%) | 62.5% | 62.5% | 62.5% | **100.0%** |
| Unresolved Platform Conflicts | 1 (Collision) | 1 (Collision) | 1 (Collision) | **0 (Zero Conflicts)** |
| Platform Utilization (%) | 10.62% | 10.62% | 10.62% | **17.19%** |
| Reassignments Triggered | 0 | 0 | 0 | **0** |
| Search Nodes Expanded | 0 | 0 | 15 | **18** |
| Search Backtracks | 0 | 0 | 6 | **8** |
| Execution Time (s) | 0.00010s | 0.00009s | 0.00014s | **0.00048s** |

---

### Scenario 5: Combined Disruption (Closure of P2 + Delays on T4 and T8)
| Metric | FCFS | Greedy | Basic CSP | Proposed Agent |
| :--- | :---: | :---: | :---: | :---: |
| Average Scheduling Delay (min) | 0.00 | 0.00 | 0.00 | **6.10** |
| Passenger Waiting Time (pass-min) | 0 | 0 | 0 | **21,870** |
| Immediate Assignment Rate (%) | 100.0% | 100.0% | 100.0% | **100.0%** |
| Final Assignment Rate (%) | 100.0% | 100.0% | 100.0% | **100.0%** |
| Unresolved Platform Conflicts | 4 (Mixed) | 4 (Mixed) | 4 (Mixed) | **0 (Zero Conflicts)** |
| Platform Utilization (%) | 20.08% | 20.08% | 20.08% | **20.08%** |
| Reassignments Triggered | 0 | 0 | 0 | **4** |
| Search Nodes Expanded | 0 | 0 | 14 | **50** |
| Search Backtracks | 0 | 0 | 0 | **10** |
| Execution Time (s) | 0.00006s | 0.00006s | 0.00009s | **0.00067s** |

---

### Scenario 6: Tight CSP Search-Stress (3 Platforms, Restricted Compatibility)
| Metric | FCFS | Greedy | Basic CSP | Proposed Agent |
| :--- | :---: | :---: | :---: | :---: |
| Average Scheduling Delay (min) | 0.00 | 0.00 | 0.00 | **4.44** |
| Passenger Waiting Time (pass-min) | 0 | 0 | 0 | **16,800** |
| Immediate Assignment Rate (%) | 77.78% | 77.78% | 100.0% | **100.0%** |
| Final Assignment Rate (%) | 77.78% | 77.78% | 100.0% | **100.0%** |
| Unresolved Platform Conflicts | 1 (Collision) | 1 (Collision) | 1 (Collision) | **0 (Zero Conflicts)** |
| Platform Utilization (%) | 25.93% | 25.93% | 33.33% | **33.33%** |
| Search Nodes Expanded | 0 | 0 | 22 | **28** |
| Search Backtracks | 0 | 0 | 5 | **9** |
| Execution Time (s) | 0.00005s | 0.00005s | 0.00011s | **0.00059s** |

---

## 9. Demonstration of Dynamic Replanning

In **Scenario 3**, Platform `P2` closes at `10:04` while `T3` and `T7` are scheduled on it. The Proposed Agent perceives the event, triggers rule-based replanning, and resolves all conflicts:

```text
[10:00] ASSIGN T1 -> P1 (Initial assignment to P1)
[10:00] ASSIGN T2 -> P3 (Initial assignment to P3)
[10:00] ASSIGN T3 -> P2 (Initial assignment to P2)
[10:00] ASSIGN T4 -> P1 (Initial assignment to P1)
[10:00] ASSIGN T5 -> P3 (Initial assignment to P3)
[10:00] ASSIGN T6 -> P1 (Initial assignment to P1)
[10:00] ASSIGN T7 -> P2 (Initial assignment to P2)
[10:00] ASSIGN T8 -> P3 (Initial assignment to P3)
[10:00] ASSIGN T9 -> P1 (Initial assignment to P1)
[10:00] ASSIGN T10 -> P4 (Initial assignment to P4)
--- EVENT: PLATFORM P2 CLOSED AT 10:04 ---
[10:04] HOLD T3 (Platform P2 closed)
[10:04] HOLD T7 (Platform P2 closed)
[10:04] REASSIGN T10 -> P3 (Reassigned P4 -> P3)
[10:04] REASSIGN T8 -> P1 (Reassigned P3 -> P1)
[10:04] HOLD T6 (Held due to conflict/disruption)
[10:04] ASSIGN T7 -> P4 (Assigned to P4)
[10:04] HOLD T9 (Held due to conflict/disruption)
--- RECOVERY: HELD TRAINS ACCOMMODATED AS BERTHS OPEN ---
[10:28] ASSIGN T6 -> P3 (Held train accommodated at P3 with +6m delay)
[10:40] ASSIGN T9 -> P1 (Held train accommodated at P1 with +5m delay)
[10:48] ASSIGN T3 -> P3 (Held train accommodated at P3 with +40m delay)

Final Result:
- Schedule: {'T1': 'P1', 'T2': 'P3', 'T3': 'P3', 'T4': 'P1', 'T5': 'P3', 'T6': 'P3', 'T7': 'P4', 'T8': 'P1', 'T9': 'P1', 'T10': 'P3'}
- Unresolved Conflicts: 0 (Self-check PASSED)
- Reassignments: 2
```

---

## 10. Limitations

For scope and educational clarity, this project adopts the following deliberate simplifications:
1. **Tracks and Interlocking**: Track block occupancy, switch routing, fouling points, and signaling circuits are not simulated.
2. **Track Closures**: Disruption events cover platform berth closures only; approach track closures are not modeled.
3. **Train Direction**: Direction is maintained as a train attribute for compatibility filtering, but directional switch movements are not simulated.
4. **Academic Prototype**: Not intended for production railway operations.

---

## 11. How to Run (CLI & Streamlit UI)

### Prerequisites
- Python 3.10+
- Optional: `pandas`, `streamlit`

Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the CLI Benchmark Suite
Run all 6 scenarios and execute the automated self-check assertions:
```bash
python metro_agent.py
```
*(Or with Python launcher: `py -3.14 metro_agent.py`)*

### Running the Interactive Streamlit Dashboard
Launch the web UI:
```bash
streamlit run app.py
```
*(Or: `py -3.14 -m streamlit run app.py`)*

---

## 12. Viva-Oriented Q&A Reference

### Q1: What is the CSP formulation?
- **Variables**: Trains requiring a platform.
- **Domains**: Compatible platforms that are currently open.
- **Constraints**: Platform compatibility, platform availability, and non-overlapping berthing intervals.

### Q2: Why use Backtracking search?
Systematic backtracking explores possible platform assignments and reverses decisions when downstream assignments become infeasible, guaranteeing a valid schedule if one exists.

### Q3: Why is the MRV heuristic important?
**Minimum Remaining Values (MRV)** ("fail-first" heuristic) assigns the most constrained train (smallest domain) first. This detects failures early and prunes large swathes of the search space.

### Q4: What does Forward Checking do?
When a train is tentatively assigned to a platform, Forward Checking removes that platform from all overlapping unassigned trains. If any unassigned train's domain becomes empty, the solver immediately backtracks.

### Q5: What happens when a platform closes?
Rule 1 triggers: Any unfrozen train assigned to the closed platform is unassigned to `HOLD`, and the agent replans all unfrozen trains across the remaining open platforms.

### Q6: What happens when no platform is available?
The train is marked `HOLD`. It waits until an occupying train departs and is retried chronologically. Its waiting time is recorded as scheduling-caused delay.

### Q7: Why do FCFS and Greedy show 0 delay during disruptions?
Because they **do not replan**. They retain stale, invalid assignments. The cost of their failure is reflected in the **conflicts metric**, not in scheduling delay.

### Q8: What makes this system an "Agent"?
It follows the classic intelligent agent cycle:
```text
Perceive State ---> Reason (Rules/CSP) ---> Decide ---> Act ---> Re-perceive ---> Replan
```
