# Intelligent Metro Platform Allocation and Dynamic Scheduling Agent

> **Important Notice:** This project uses classical AI techniques and does not use machine learning, deep learning, or reinforcement learning. It is an educational and academic demonstration of Constraint Satisfaction Problems (CSP), heuristic search, and dynamic replanning. It does not claim real-world railway deployment capability.

---

## 1. Project Title
**Intelligent Metro Platform Allocation and Dynamic Scheduling Agent**

---

## 2. Problem Statement
In high-density urban metro terminals and stations, assigning incoming trains to suitable passenger platforms is a complex combinatorial scheduling challenge. Disruptions—such as unexpected train arrival delays, emergency platform closures (maintenance, power outages), and simultaneous arrivals of competing trains—threaten station throughput, cause platform occupancy overlaps, and increase passenger wait times.

A static schedule breaks down when disruptions occur. The scheduling agent must dynamically resolve platform conflicts in real time, respect train-platform physical compatibility, prioritize critical trains (Emergency > High > Normal), and gracefully hold and reassign trains when the station is temporarily overconstrained.

---

## 3. Objective
To build an educational, transparent, and provably conflict-free Python scheduling agent using **classical AI**:
- Formalize platform allocation as a **Constraint Satisfaction Problem (CSP)**.
- Implement **Backtracking search** with **Minimum Remaining Values (MRV)** heuristic, **Forward Checking (FC)** constraint propagation, and **Least Constraining Value (LCV)** ordering.
- Provide explicit **Rule-Based Reasoning** and **Dynamic Replanning** to recover from disruptions.
- Quantitatively benchmark the Proposed Agent against three classic baselines:
  1. **FCFS** (First-Come, First-Served)
  2. **Greedy** (Immediate Best-Fit)
  3. **Basic CSP** (Plain Backtracking without MRV, FC, or priority ordering)
- Guarantee **0 unresolved conflicts** under all operating conditions and disruptions.

---

## 4. Environment
The environment models a centralized metro station dispatch system:
- **Platforms**: A set of terminal tracks/platforms $\{P_1, P_2, P_3, P_4\}$. Platforms have operational status (open/available or closed).
- **Time Representation**: Discrete integer minutes from midnight ($10:00 = 600$, $10:15 = 615$).
- **State Dynamism**: Timestamped disruption events occurring chronologically during station execution.

---

## 5. Input Information
The system accepts train schedules via CSV (`trains.csv`) or programmatic definitions:
- `train_id`: Unique train identifier (e.g. `T1`, `T2`).
- `arrival_time`: Scheduled station arrival in `HH:MM` or integer minutes.
- `departure_time`: Scheduled station departure in `HH:MM` or integer minutes.
- `priority`: Service tier (`Emergency`, `High`, `Normal`).
- `compatible_platforms`: Pipe-delimited list of physical platforms the train can safely berth at (e.g. `P1|P2|P3`).
- `delay`: Injected disruption delay (minutes).
- `passenger_load`: Passenger count (e.g. $200 - 900$).
- `direction`: Heading direction (`North`, `South`).

---

## 6. Agent Decisions & Actions
The agent perceives station state, reasons over constraints, and outputs clear, discrete actions:
- `ASSIGN(train, platform)`: Directs an incoming train to berth at a specific open platform.
- `HOLD(train)`: Holds an incoming train outside the berthing area when no compatible platform is currently free.
- `REASSIGN(train, platform)`: Modifies a previously planned assignment for an unfrozen train when its assigned platform is compromised.

---

## 7. Classical AI Techniques
The agent relies exclusively on core principles of classical Artificial Intelligence:
1. **Constraint Satisfaction Problem (CSP)** formulation.
2. **Systematic Backtracking Search** with state restoration upon failure.
3. **Minimum Remaining Values (MRV)** variable ordering heuristic ("Fail-First" principle).
4. **Forward Checking (FC)** constraint propagation to prune future conflicting platform domains.
5. **Least Constraining Value (LCV)** value ordering to maximize remaining flexibility.
6. **Rule-Based Domain Logic** for disruption triggers and frozen train protection.
7. **Chronological Event-Driven Replanning**.

---

## 8. CSP Formulation
- **Variables**: Trains requiring platform allocation $X = \{T_1, T_2, \dots, T_n\}$.
- **Domains**: For each variable $T_i$, $D(T_i) = \{ P_k \in \text{compatible\_platforms}(T_i) \mid P_k \text{ is not closed} \}$.
- **Constraints**:
  1. **Availability**: $P_k$ must not be closed during $[T_i.\text{effective\_arrival}, T_i.\text{effective\_departure})$.
  2. **Compatibility**: $P_k \in T_i.\text{compatible\_platforms}$.
  3. **Non-Overlapping Occupancy**: No two trains $T_A$ and $T_B$ assigned to the same platform $P_k$ may overlap in time:
     $$\text{Overlap}(T_A, T_B) \iff (T_A.\text{effective\_arrival} < T_B.\text{effective\_departure}) \land (T_B.\text{effective\_arrival} < T_A.\text{effective\_departure})$$

---

## 9. Constraints & Infeasibility Handling (HOLD Semantics)
When competition for platforms exceeds physical station capacity (overconstrained state):
- **Proposed Agent**: Sorts candidates by **Priority (Emergency > High > Normal)**, breaking ties by earliest arrival. Higher-priority trains are guaranteed platform reservations; if a train cannot be berthed without causing conflicts, it is assigned `HOLD`.
- **Basic CSP**: Resolves infeasibility strictly in **Arrival Order** without priority awareness.
- **Held Train Recovery**: As trains depart and platforms open, held trains are retried chronologically. The dwell duration is strictly preserved:
  $$\text{effective\_departure} = \text{effective\_arrival} + \text{original\_dwell}$$
  The delay between scheduled arrival and berthing is measured as scheduling-caused delay.

---

## 10. Algorithm Flow
```text
Perceive Train Schedule & Initial Station State
                 ↓
Compute Domains for all Trains (Compatibility & Open Platforms)
                 ↓
Apply Heuristic CSP Solver:
  ├─ Select Variable: MRV (Smallest Domain; tie-break Priority → Arrival)
  ├─ Select Value: LCV (Platform causing least domain pruning)
  ├─ Check Overlap Constraints
  ├─ Forward Checking (Prune conflicting platform from overlapping trains)
  └─ Backtrack on Empty Domain
                 ↓
Generate Initial Conflict-Free Schedule
                 ↓
Timeline Event Loop:
  ├─ Event Occurs (PLATFORM_CLOSURE / TRAIN_DELAY)
  ├─ Freeze Past / Dwelling Trains (effective_arrival ≤ event_time)
  ├─ Trigger Rules (Closed Platform Rule, Delay Update Rule)
  ├─ Dynamically Replan Unfrozen Trains via Heuristic CSP
  └─ Accommodate Held Trains as Platforms Clear
                 ↓
Output Verified Schedule (0 Conflicts) & Evaluation Metrics
```

---

## 11. Dynamic Replanning Rules
The agent incorporates explicit rule-based reasoning:
- **Rule 1: Closed Platform**: If platform $P$ closes at time $t$, identify all unfrozen trains assigned to $P$, unassign them to `HOLD`, and re-solve CSP across remaining platforms.
- **Rule 2: Train Delay**: If train $T$ is delayed by $\Delta t$, update its effective window. Check for newly introduced overlaps and replan unfrozen trains.
- **Rule 3: Priority Berthing**: Emergency trains take precedence over High and Normal trains when reassigning berths.
- **Rule 4: Frozen Commitment**: Trains that have already arrived at or are dwelling at a platform ($\text{effective\_arrival} \le t$) are **frozen** and cannot be retroactively modified.

---

## 12. Baseline Algorithms
To provide rigorous evaluation, four algorithms are compared:
1. **FCFS (First-Come, First-Served)**: Sorts trains by arrival time. Greedily assigns the first available valid platform. Does not backtrack; does not replan when disruptions occur.
2. **Greedy**: Sorts trains by arrival time. Evaluates compatible platforms and picks the first valid fit. Does not backtrack; does not replan.
3. **Basic CSP**: Classical recursive Backtracking solver. MRV = OFF, Forward Checking = OFF, Priority ordering = OFF, Dynamic replanning = OFF. Stale assignments after disruptions are retained.
4. **Proposed Agent**: Heuristic CSP. Backtracking = ON, MRV = ON, Forward Checking = ON, Priority ordering = ON, Dynamic replanning = ON.

> **Crucial Rule on Interpreting Baseline Delay and Conflicts:**
> Baseline delay and conflicts must be interpreted together. FCFS and Greedy do not replan after disruptions; their stale or overlapping assignments produce misleadingly low scheduling-caused delay while producing **invalid schedules**. The penalty of those invalid schedules is captured by the **unresolved conflicts metric**.

---

## 13. Evaluation Metrics
1. **Average Scheduling-Caused Delay (min)**: Average waiting time caused by `HOLD`. Injected event delay is excluded per specification.
2. **Passenger Waiting Time (passenger-min)**: $\sum (\text{passenger\_load} \times \text{scheduling\_caused\_wait\_minutes})$.
3. **Immediate Assignment Rate (%)**: Percentage of trains berthed at initial schedule generation without `HOLD`.
4. **Final Assignment Rate (%)**: Percentage of trains successfully assigned to a platform by the end of simulation.
5. **Unresolved Platform Conflicts**: Count of overlapping trains, assignments to closed platforms, or incompatible assignments. Target for Proposed Agent is strictly **0**.
6. **Platform Utilization (%)**: $\frac{\text{occupied platform time}}{\text{available platform time}} \times 100$, where available time excludes platform closure periods.
7. **Reassignments**: Count of trains whose berthing platform was altered after initial assignment.
8. **Nodes Expanded**: Total search states explored in CSP (0 for FCFS/Greedy).
9. **Backtracks**: Total recursive search reversals upon encountering a dead-end (0 for FCFS/Greedy).
10. **Execution Time (seconds)**: Total CPU execution time measured via `time.perf_counter()`.

---

## 14. Programmatic Evaluation Benchmark Results
Below are the actual measured results programmatically generated by executing `python metro_agent.py` on all 6 test scenarios:

### Scenario 1: Normal Operation (4 platforms, 10 trains, 0 disruptions)
| Metric | FCFS | Greedy | Basic CSP | Proposed Agent |
| :--- | :--- | :--- | :--- | :--- |
| **Average Sched-Caused Delay (m)** | 0.0 | 0.0 | 0.0 | 0.0 |
| **Passenger Waiting (pass-min)** | 0 | 0 | 0 | 0 |
| **Immediate Assign Rate (%)** | 100.0% | 100.0% | 100.0% | 100.0% |
| **Final Assign Rate (%)** | 100.0% | 100.0% | 100.0% | 100.0% |
| **Conflicts (unresolved)** | 0 | 0 | 0 | **0** |
| **Platform Utilization (%)** | 15.18% | 15.18% | 15.18% | 15.18% |
| **Reassignments** | 0 | 0 | 0 | 0 |
| **Nodes Expanded** | 0 | 0 | 14 | 14 |
| **Backtracks** | 0 | 0 | 0 | 0 |
| **Execution Time (s)** | 0.00006s | 0.00007s | 0.00008s | 0.00021s |

### Scenario 2: Train Delays (Delays injected into T2 and T5)
| Metric | FCFS | Greedy | Basic CSP | Proposed Agent |
| :--- | :--- | :--- | :--- | :--- |
| **Average Sched-Caused Delay (m)** | 0.0 | 0.0 | 0.0 | 0.0 |
| **Passenger Waiting (pass-min)** | 0 | 0 | 0 | 0 |
| **Immediate Assign Rate (%)** | 100.0% | 100.0% | 100.0% | 100.0% |
| **Final Assign Rate (%)** | 100.0% | 100.0% | 100.0% | 100.0% |
| **Conflicts (unresolved)** | 1 | 1 | 1 | **0** |
| **Platform Utilization (%)** | 15.18% | 15.18% | 15.18% | 15.18% |
| **Reassignments** | 0 | 0 | 0 | 7 |
| **Nodes Expanded** | 0 | 0 | 14 | 27 |
| **Backtracks** | 0 | 0 | 0 | 0 |
| **Execution Time (s)** | 0.00006s | 0.00007s | 0.00008s | 0.00037s |

### Scenario 3: Platform Closure (Platform P2 closes at 10:04)
| Metric | FCFS | Greedy | Basic CSP | Proposed Agent |
| :--- | :--- | :--- | :--- | :--- |
| **Average Sched-Caused Delay (m)** | 0.0 | 0.0 | 0.0 | 5.10 |
| **Passenger Waiting (pass-min)** | 0 | 0 | 0 | 16,970 |
| **Immediate Assign Rate (%)** | 100.0% | 100.0% | 100.0% | 100.0% |
| **Final Assign Rate (%)** | 100.0% | 100.0% | 100.0% | 100.0% |
| **Conflicts (unresolved)** | 3 | 3 | 3 | **0** |
| **Platform Utilization (%)** | 20.08% | 20.08% | 20.08% | 20.08% |
| **Reassignments** | 0 | 0 | 0 | 2 |
| **Nodes Expanded** | 0 | 0 | 14 | 25 |
| **Backtracks** | 0 | 0 | 0 | 4 |
| **Execution Time (s)** | 0.00005s | 0.00006s | 0.00008s | 0.00051s |

### Scenario 4: Platform Conflict (Multiple trains competing for P1)
| Metric | FCFS | Greedy | Basic CSP | Proposed Agent |
| :--- | :--- | :--- | :--- | :--- |
| **Average Sched-Caused Delay (m)** | 0.0 | 0.0 | 0.0 | 10.12 |
| **Passenger Waiting (pass-min)** | 0 | 0 | 0 | 45,100 |
| **Immediate Assign Rate (%)** | 62.5% | 62.5% | 62.5% | 62.5% |
| **Final Assign Rate (%)** | 62.5% | 62.5% | 62.5% | **100.0%** |
| **Conflicts (unresolved)** | 1 | 1 | 1 | **0** |
| **Platform Utilization (%)** | 10.62% | 10.62% | 10.62% | **17.19%** |
| **Reassignments** | 0 | 0 | 0 | 0 |
| **Nodes Expanded** | 0 | 0 | 15 | 18 |
| **Backtracks** | 0 | 0 | 6 | 8 |
| **Execution Time (s)** | 0.00010s | 0.00009s | 0.00014s | 0.00048s |

### Scenario 5: Combined Disruption (Closure of P2 + Delays on T4 and T8)
| Metric | FCFS | Greedy | Basic CSP | Proposed Agent |
| :--- | :--- | :--- | :--- | :--- |
| **Average Sched-Caused Delay (m)** | 0.0 | 0.0 | 0.0 | 6.10 |
| **Passenger Waiting (pass-min)** | 0 | 0 | 0 | 21,870 |
| **Immediate Assign Rate (%)** | 100.0% | 100.0% | 100.0% | 100.0% |
| **Final Assign Rate (%)** | 100.0% | 100.0% | 100.0% | 100.0% |
| **Conflicts (unresolved)** | 4 | 4 | 4 | **0** |
| **Platform Utilization (%)** | 20.08% | 20.08% | 20.08% | 20.08% |
| **Reassignments** | 0 | 0 | 0 | 4 |
| **Nodes Expanded** | 0 | 0 | 14 | 50 |
| **Backtracks** | 0 | 0 | 0 | 10 |
| **Execution Time (s)** | 0.00006s | 0.00006s | 0.00009s | 0.00067s |

### Scenario 6: Tight CSP Search-Stress (3 platforms, restricted domains)
| Metric | FCFS | Greedy | Basic CSP | Proposed Agent |
| :--- | :--- | :--- | :--- | :--- |
| **Average Sched-Caused Delay (m)** | 0.0 | 0.0 | 0.0 | 4.44 |
| **Passenger Waiting (pass-min)** | 0 | 0 | 0 | 16,800 |
| **Immediate Assign Rate (%)** | 77.78% | 77.78% | 100.0% | **100.0%** |
| **Final Assign Rate (%)** | 77.78% | 77.78% | 100.0% | **100.0%** |
| **Conflicts (unresolved)** | 1 | 1 | 1 | **0** |
| **Platform Utilization (%)** | 25.93% | 25.93% | 33.33% | **33.33%** |
| **Reassignments** | 0 | 0 | 0 | 0 |
| **Nodes Expanded** | 0 | 0 | 22 | 28 |
| **Backtracks** | 0 | 0 | 5 | 9 |
| **Execution Time (s)** | 0.00005s | 0.00005s | 0.00011s | 0.00059s |

---

## 15. Limitations
For scope and educational focus, this implementation deliberately adopts the following simplifications:
1. **Tracks and Switches**: Detailed track circuits, interlocking, track fouling points, and block signaling are not simulated.
2. **Track Closures**: Disruption events cover platform berth closures only; approach track closures are not modeled.
3. **Train Direction**: `direction` is maintained in train metadata for compatibility filtering, but full directional turnout routing is not simulated.
4. **Non-Production Demonstration**: This codebase is an academic AI assignment and not intended for production railway dispatch.

---

## 16. How to Run

### Requirements
- Python 3.10+ (Standard Library: `csv`, `dataclasses`, `typing`, `copy`, `time`)
- Optional (for Streamlit UI): `pandas`, `streamlit`

Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the CLI Benchmark Suite
Execute all 6 scenarios, benchmark tables, and zero-conflict assertions:
```bash
python metro_agent.py
```
*(Or on Windows with python launcher: `py -3.14 metro_agent.py`)*

### Running the Interactive Streamlit UI
Launch the interactive web dashboard:
```bash
streamlit run app.py
```
*(Or: `py -3.14 -m streamlit run app.py`)*

---

## 17. Viva-Oriented Q&A Reference

### Q1: What is the CSP formulation here?
- **Variables**: Trains needing platform assignment.
- **Domains**: Compatible platforms that are currently open.
- **Constraints**: Train-platform physical compatibility, platform availability, and non-overlapping interval occupancy.

### Q2: Why use Backtracking search?
Systematic backtracking allows the scheduler to explore feasible platform combinations, assign compatible berths, and undo (backtrack) decisions when downstream assignments become impossible.

### Q3: Why is the MRV heuristic important?
**Minimum Remaining Values (MRV)** ("fail-first" heuristic) selects the unassigned train with the smallest number of valid platform options. Assigning highly constrained trains first prevents wasted search in doomed subtrees.

### Q4: What role does Forward Checking play?
After tentatively assigning train $T$ to platform $P$, Forward Checking immediately removes $P$ from the domains of all unassigned trains whose arrival/departure intervals overlap with $T$. If any train's domain becomes empty, the solver immediately backtracks without expanding further dead-end nodes.

### Q5: What happens when a platform closes?
The agent triggers **Rule 1 (Closed Platform)**: It unassigns any unfrozen train berthed on that platform to `HOLD` and immediately triggers dynamic replanning with the remaining open platforms.

### Q6: What happens when no platform is available?
The train is marked `HOLD`. It waits outside the berthing area until an occupying train departs or a platform opens. Its waiting time is recorded as scheduling-caused delay.

### Q7: Why do FCFS and Greedy show 0 delay during disruptions?
Because FCFS and Greedy **do not replan**. They leave their stale assignments untouched. They don't introduce delay because they ignore the disruption, but this causes **unresolved conflicts** (trains assigned to closed platforms or colliding on the same platform).

### Q8: What makes this system an "Agent"?
It follows the classic intelligent agent loop:
$$\text{Perceive} \longrightarrow \text{Reason} \longrightarrow \text{Decide} \longrightarrow \text{Act} \longrightarrow \text{Re-perceive} \longrightarrow \text{Replan}$$
