# Intelligent Metro Platform Allocation and Dynamic Scheduling Agent

A lightweight, classical Artificial Intelligence (AI) project that assigns incoming and departing metro trains to compatible station platforms while avoiding conflicts, managing train priorities, handling disruptions (delays and platform closures), and dynamically replanning schedules.

> **Classical AI Note:**  
> This project uses classical AI techniques (Constraint Satisfaction Problems, recursive Backtracking search, Minimum Remaining Values heuristic, Forward Checking, and rule-based dynamic replanning). It does **NOT** use machine learning, deep learning, reinforcement learning, predictive models, or LLMs.

---

## 1. Project Title
**Intelligent Metro Platform Allocation and Dynamic Scheduling Agent**

---

## 2. Problem Statement
In a busy urban metro station, incoming and departing trains must be allocated to suitable platforms. The allocation problem requires:
- Matching trains to structurally and directionally compatible platforms.
- Ensuring no two trains occupy the same platform during overlapping time intervals.
- Prioritizing high-importance and emergency trains when capacity bottlenecks arise.
- Gracefully handling real-time disruptions such as platform closures and incoming train delays.
- Re-solving affected assignments dynamically while safeguarding trains that are already docked or departed.

---

## 3. Environment
The simulated metro station environment consists of:
- **Platforms:** 3–4 platforms (`P1`, `P2`, `P3`, `P4`). Platforms can experience dynamic emergency closures.
- **Trains:** 5–10 trains per scenario, each characterized by arrival time, departure time, direction, compatible platforms, passenger load, priority, and injected delay.
- **Time Representation:** Clock time (`HH:MM`) converted to integer minutes from midnight (e.g., `10:00` $\to$ `600`, `10:15` $\to$ `615`).

---

## 4. Input Information
The scheduling agent processes:
1. **Train Information:**
   - `train_id`: Unique identifier (e.g., `T1`, `T2`)
   - `arrival_time`: Scheduled arrival (minutes)
   - `departure_time`: Scheduled departure (minutes)
   - `direction`: Heading (`North` / `South`)
   - `priority`: Service tier (`Emergency`, `High`, `Normal`)
   - `compatible_platforms`: Subset of allowable platforms (e.g., `['P1', 'P2']`)
   - `passenger_load`: Passenger count aboard the train
   - `delay`: Real-time external delay in minutes
2. **Platform Information:**
   - Platform identifier and operational status (`Open` or timestamped `Closed`).
3. **Environment Events:**
   - Timestamped disruption events (`PLATFORM_CLOSURE` or `TRAIN_DELAY`).

---

## 5. Agent Decisions
The agent can execute four discrete actions:
- `ASSIGN`: Assign a train to a compatible, conflict-free platform at its requested time.
- `HOLD`: Place a train on temporary wait if no compatible platform is currently available without conflicts.
- `REASSIGN`: Allocate a new compatible platform to an unassigned or disrupted train during replanning.
- `DEPART`: Clear the platform when a train completes its scheduled dwell duration.

---

## 6. CSP Formulation
Platform allocation is formally modeled as a **Constraint Satisfaction Problem (CSP)**:
- **Variables:** Each train $T_i \in \{T_1, T_2, \dots, T_n\}$.
- **Domains:** The set of compatible platforms for train $T_i$, excluding permanently closed platforms:
  $$\text{Domain}(T_i) = \{ P \in \text{compatible}(T_i) \mid P \text{ is open}\} \cup \{\text{HOLD}\}$$
- **Constraints:**
  1. **Platform Closure Constraint:** No train can be assigned to a platform that is closed during its dwell window.
  2. **Platform Compatibility Constraint:** For assigned platform $P$, $P \in \text{compatible}(T_i)$.
  3. **No-Overlap Constraint:** Two trains $A$ and $B$ assigned to the same platform $P$ must not overlap in time:
     $$\text{Conflict if } (\text{arrival}_A < \text{departure}_B) \land (\text{arrival}_B < \text{departure}_A)$$

---

## 7. Backtracking Search
The solver implements a recursive depth-first backtracking search:
1. Base case: If all trains are assigned, return success.
2. Select an unassigned train variable.
3. For each candidate platform in the train's domain:
   - Check if assignment satisfies all constraints.
   - If valid, bind platform, update state, and recursively solve remaining variables.
   - If a dead end is reached, undo assignment (**backtrack**) and try the next platform.
4. If no candidate platforms yield a valid complete assignment, backtrack to the previous decision point.
5. Search effort is measured via `nodes_expanded` (attempted assignments) and `backtracks` (retracted assignments).

---

## 8. Minimum Remaining Values (MRV) Heuristic
The **MRV heuristic** (most-constrained variable first) selects the unassigned train that currently has the fewest valid platform choices remaining:
$$\text{Train}^* = \arg\min_{T \in \text{Unassigned}} |\text{ValidPlatforms}(T)|$$
- **Effect:** Fails early on difficult variables before committing to decisions on flexible variables, dramatically reducing the branching factor.
- **Tie-Breaking:** Broken first by **Priority** (`Emergency` > `High` > `Normal`), then by earliest arrival time.
- Enabled for the Proposed Agent; disabled for Basic CSP.

---

## 9. Forward Checking (FC)
After each tentative variable assignment:
1. The solver looks ahead at all remaining unassigned trains.
2. For each remaining train, it verifies whether at least one valid platform choice remains.
3. If any train has its remaining domain wiped out ($|\text{Domain}(T')| = 0$), the solver prunes the search tree immediately without descending further into an inevitable failure.
- Enabled for the Proposed Agent; disabled for Basic CSP.

---

## 10. Rule-Based Reasoning
Simple, transparent logical rules complement the CSP solver:
- **Rule 1 (Platform Closure):** `IF` a platform is closed at time $t$, `THEN` any future train ($t_{\text{arrival}} \ge t$) assigned to it has its assignment invalidated and is flagged for immediate reassignment.
- **Rule 2 (No Platform Available):** `IF` no compatible platform can accommodate train $T$ without conflict, `THEN` mark train as `HOLD`.
- **Rule 3 (Priority Dispatch):** Higher-priority trains (`Emergency` > `High` > `Normal`) are evaluated first during bottleneck contention and retain precedence when scheduling platforms.

---

## 11. Dynamic Replanning
The Proposed Agent listens to chronological disruption events:
1. **Event Occurs:** e.g., `10:12 : P2 CLOSED` or `10:05 : T2 delayed by 10 min`.
2. **Update Station State:** Mark platform closed or update train's arrival/departure.
3. **Protect Frozen Trains:** Trains that have already departed or are currently docked at a platform are **never retroactively altered**:
   $$\text{Frozen if } t_{\text{current}} > t_{\text{sched\_arrival}}$$
4. **Invalidate Affected Future Assignments:** Trains arriving at or after $t_{\text{current}}$ on affected platforms are cleared.
5. **Re-Solve:** The CSP solver re-runs with MRV and Forward Checking over future unassigned trains.
6. **Retry Held Trains:** As platforms are vacated by departing trains, held trains are retried in priority order, preserving original dwell durations ($t_{\text{new\_departure}} = t_{\text{new\_arrival}} + \text{dwell}$).

---

## 12. Four Algorithms Compared
| Algorithm | Backtracking | MRV | Forward Checking | Priority Rules | Dynamic Replanning |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. FCFS** | NO | NO | NO | NO | NO |
| **2. Greedy** | NO | NO | NO | NO | NO |
| **3. Basic CSP** | YES | NO | NO | NO | NO |
| **4. Proposed Agent** | **YES** | **YES** | **YES** | **YES** | **YES** |

> **Crucial Interpretation Rule:**  
> **Baseline delay and conflicts must be interpreted together.**  
> FCFS and Greedy may exhibit artificially low scheduling-caused delay because they never replan and leave trains in stale slots; those failures appear as **unresolved conflicts**. The Proposed Agent actively resolves every conflict, shifting trains or placing them on temporary HOLD, resulting in **0 conflicts**.

---

## 13. Evaluation Metrics
1. **Scheduling-Caused Delay (min):** Total and average delay introduced by scheduling decisions (HOLD waits or slot shifts). Injected disruption delays from events are excluded.
2. **Passenger Waiting (passenger-minutes):** $\sum (\text{passenger\_load} \times \text{scheduling\_delay})$.
3. **Immediate Assignment Rate (%):** Percentage of trains assigned immediately at their intended arrival time without entering HOLD.
4. **Final Assignment Rate (%):** Percentage of trains eventually assigned to a platform before simulation close.
5. **Unresolved Conflicts:** Total overlapping intervals, assignments to closed platforms, or incompatible platform assignments. **Must be 0 for the Proposed Agent.**
6. **Search Effort:** `nodes_expanded` and `backtracks` measured during search.
7. **Execution Time (ms):** Runtime measured with `time.perf_counter()`.

---

## 14. Test Scenarios
1. **Scenario 1 — Normal Operation:** 4 platforms, 8 trains, conflict-free baseline.
2. **Scenario 2 — Train Delay:** Train $T_2$ delayed by 10 minutes at 10:05, causing overlap with $T_4$ on platform $P_2$.
3. **Scenario 3 — Platform Closure:** Platform $P_2$ closes at 10:12 due to track maintenance, invalidating future assignments of $T_4$ and $T_6$.
4. **Scenario 4 — Platform Competition:** 3 trains ($T_1$ Normal, $T_2$ High, $T_3$ Emergency) arrive simultaneously and all require platform $P_1$. Demonstrates priority ordering and dwell preservation.
5. **Scenario 5 — Combined Disruption:** Multiple simultaneous disruptions ($T_1$ delayed by 12 min at 10:05 and platform $P_3$ closes at 10:15).
6. **Scenario 6 — Tight CSP:** 3 platforms, 9 trains, tightly constrained compatibilities and overlapping intervals. Designed to test combinatorial search efficiency (Basic CSP vs. Proposed Agent).

---

## 15. Limitations
- **Station Infrastructure:** Only platform tracks are modeled; turnout switches, crossovers, and approach blocks are simplified.
- **Track Conflict Detection:** Detailed block-level track circuit conflicts and interlocking routes outside the station platforms are excluded.
- **Signalling:** Real-world railway block signalling (e.g., ETCS, CBTC) is abstracted away.
- **Single Station:** Focus is placed on single-station platform allocation rather than network-wide line scheduling.

---

## 16. How to Run
Ensure Python 3.8+ is installed. No third-party packages or external libraries are required (Python Standard Library only).

```bash
cd metro-platform-agent
python metro_agent.py
```

---

## 17. Example Terminal Output and Evaluation Results

```text
========================================================================
      INTELLIGENT METRO PLATFORM ALLOCATION & SCHEDULING AGENT      
                   Classical AI Demonstration                       
========================================================================

[1] Loading train data from: C:\Users\...\metro-platform-agent\trains.csv
    Loaded 8 base trains.
[2] Prepared 6 test scenarios.

Scenario 1 --- Normal Operation
Description: 4 platforms, 8 trains, regular schedule, no disruptions.
------------------------------------------------------------------------
Algorithm        | Avg Delay | Pass-Min  | Immed%  | Final%  | Conflicts | Nodes | Backtracks
------------------------------------------------------------------------
FCFS             |    0.00m |         0 |  100.0% |  100.0% |         0 |     0 |          0
Greedy           |    0.00m |         0 |  100.0% |  100.0% |         0 |     0 |          0
Basic CSP        |    0.00m |         0 |  100.0% |  100.0% |         0 |     8 |          0
Proposed Agent   |    0.00m |         0 |  100.0% |  100.0% |         0 |     8 |          0
------------------------------------------------------------------------

Scenario 2 --- Train Delay
Description: T2 delayed by 10 minutes at 10:05, causing overlap on P2.
------------------------------------------------------------------------
Algorithm        | Avg Delay | Pass-Min  | Immed%  | Final%  | Conflicts | Nodes | Backtracks
------------------------------------------------------------------------
FCFS             |    0.00m |         0 |  100.0% |  100.0% |         1 |     0 |          0
Greedy           |    0.00m |         0 |  100.0% |  100.0% |         1 |     0 |          0
Basic CSP        |    0.00m |         0 |  100.0% |  100.0% |         1 |     8 |          0
Proposed Agent   |    0.00m |         0 |  100.0% |  100.0% |         0 |     8 |          0
------------------------------------------------------------------------

========================================
DEMONSTRATION: DYNAMIC PLATFORM CLOSURE
========================================
Initial Schedule
----------------
T1   -> P2   (10:00 - 10:10)
T2   -> P3   (10:05 - 10:15)
T3   -> P1   (10:08 - 10:20)
T4   -> P2   (10:12 - 10:22)
T5   -> P4   (10:15 - 10:25)
T6   -> P2   (10:22 - 10:32)
T7   -> P1   (10:25 - 10:38)
T8   -> P3   (10:30 - 10:40)

Event
-----
10:12 : P2 CLOSED

Replanning
----------
Affected train(s): T4, T6

Revised Schedule
----------------
T1   -> P2   (10:00 - 10:10) [Prio: Normal]
T2   -> P3   (10:05 - 10:15) [Prio: High]
T3   -> P1   (10:08 - 10:20) [Prio: Normal]
T4   -> HOLD (10:12 - 10:22) [Prio: Emergency]
T5   -> P4   (10:15 - 10:25) [Prio: Normal]
T6   -> HOLD (10:22 - 10:32) [Prio: Normal]
T7   -> P1   (10:25 - 10:38) [Prio: High]
T8   -> P3   (10:30 - 10:40) [Prio: Normal]
========================================

Scenario 6 --- Tight CSP
Description: 3 platforms, 9 trains, restrictive compatibilities, overlapping intervals.
------------------------------------------------------------------------
Algorithm        | Avg Delay | Pass-Min  | Immed%  | Final%  | Conflicts | Nodes | Backtracks
------------------------------------------------------------------------
FCFS             |    0.00m |         0 |   66.7% |   66.7% |         0 |     0 |          0
Greedy           |    4.33m |      5070 |   66.7% |  100.0% |         0 |     0 |          0
Basic CSP        |    0.00m |         0 |  100.0% |  100.0% |         0 |    17 |          8
Proposed Agent   |    0.00m |         0 |  100.0% |  100.0% |         0 |     9 |          0
------------------------------------------------------------------------

========================================================================
                   OVERALL ALGORITHM COMPARISON SUMMARY             
========================================================================
Algorithm        | Avg Delay | Pass-Min  | Final%  | Conflicts | Nodes  | Backtracks | Time(ms)
------------------------------------------------------------------------
FCFS             |    0.00m |         0 |   88.9% |         6 |      0 |          0 |     0.21
Greedy           |    1.78m |     10890 |  100.0% |         6 |      0 |          0 |     0.18
Basic CSP        |    0.00m |         0 |   91.7% |         6 |     61 |         17 |     0.23
Proposed Agent   |    1.98m |      9410 |   97.2% |         0 |     48 |          4 |     0.76
========================================================================

[Proposed Agent Verification Check]
Total Proposed Agent Conflicts across all scenarios: 0
Proposed Agent Conflict Check: PASS
```

---

## 18. Impact of MRV and Forward Checking
In **Scenario 6 (Tight CSP)**:
- **Basic CSP:** Processes trains chronologically by arrival time. It assigns early choices that seem valid locally but lead to deep dead-ends downstream when heavily constrained single-choice trains arrive. Basic CSP must undo multiple assignments, expanding **17 nodes** and requiring **8 backtracks**.
- **Proposed Agent:** With **MRV**, the agent identifies and schedules the most tightly constrained trains first (domain size 1). Simultaneously, **Forward Checking** looks ahead and eliminates conflicting platform options from remaining trains. If any train loses all viable choices, the solver detects this at depth 1 instead of exploring futile sub-trees. Consequently, the Proposed Agent finds the optimal conflict-free solution in **9 nodes with 0 backtracks** (a 47% reduction in search states and 100% elimination of backtracks).
