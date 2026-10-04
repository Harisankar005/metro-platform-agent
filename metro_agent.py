"""
Intelligent Metro Platform Allocation and Dynamic Scheduling Agent
==================================================================
Classical AI Constraint Satisfaction Problem (CSP) Solver demonstrating:
- Backtracking Search
- Minimum Remaining Values (MRV) Heuristic
- Forward Checking (FC)
- Priority Rules & Dynamic Disruption Replanning
"""

import copy
import csv
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------
# Data Structures and Time Helpers
# ---------------------------------------------------------

def str_to_time(t_str: str) -> int:
    """Convert 'HH:MM' string to minutes from midnight."""
    h, m = map(int, t_str.strip().split(":"))
    return h * 60 + m


def time_to_str(mins: int) -> str:
    """Convert minutes from midnight to 'HH:MM' string."""
    return f"{mins // 60:02d}:{mins % 60:02d}"


@dataclass
class Train:
    train_id: str
    arrival_time: int
    departure_time: int
    direction: str
    priority: str
    compatible_platforms: List[str]
    passenger_load: int
    delay: int = 0
    sched_arrival: int = 0
    sched_departure: int = 0
    assigned_platform: Optional[str] = None
    is_held: bool = False
    sched_delay: int = 0

    def __post_init__(self):
        if self.sched_arrival == 0:
            self.sched_arrival = self.arrival_time + self.delay
        if self.sched_departure == 0:
            dwell = self.departure_time - self.arrival_time
            self.sched_departure = self.sched_arrival + dwell


@dataclass
class Event:
    time: int
    event_type: str  # "PLATFORM_CLOSURE" or "TRAIN_DELAY"
    target: str      # platform_id or train_id
    value: int = 0   # delay minutes if TRAIN_DELAY


def load_trains_from_csv(filepath: str) -> List[Train]:
    """Load train definitions from CSV or fallback to defaults."""
    if not os.path.exists(filepath):
        return get_default_trains()
    trains = []
    with open(filepath, mode="r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            trains.append(Train(
                train_id=row["train_id"].strip(),
                arrival_time=str_to_time(row["arrival_time"]),
                departure_time=str_to_time(row["departure_time"]),
                direction=row["direction"].strip(),
                priority=row["priority"].strip(),
                compatible_platforms=[p.strip() for p in row["compatible_platforms"].split("|")],
                passenger_load=int(row["passenger_load"]),
                delay=int(row.get("delay", 0)),
            ))
    return trains


def get_default_trains() -> List[Train]:
    return [
        Train("T1", 600, 610, "North", "Normal", ["P1", "P2"], 100),
        Train("T2", 605, 615, "South", "High", ["P2", "P3"], 150),
        Train("T3", 608, 620, "North", "Normal", ["P1", "P3"], 80),
        Train("T4", 612, 622, "South", "Emergency", ["P2", "P4"], 120),
        Train("T5", 615, 625, "North", "Normal", ["P1", "P4"], 90),
        Train("T6", 622, 632, "South", "Normal", ["P2", "P3"], 110),
        Train("T7", 625, 638, "North", "High", ["P1", "P3", "P4"], 130),
        Train("T8", 630, 640, "South", "Normal", ["P3", "P4"], 95),
    ]


# ---------------------------------------------------------
# Core CSP & Rule Functions
# ---------------------------------------------------------

def is_valid_assignment(
    train: Train, platform: str, schedule: Dict[str, Train],
    closed_platforms: Dict[str, int], arr: Optional[int] = None, dep: Optional[int] = None,
) -> bool:
    """Constraints: open platform, compatibility, and no overlapping time intervals."""
    t_arr = arr if arr is not None else train.sched_arrival
    t_dep = dep if dep is not None else train.sched_departure
    if platform in closed_platforms and t_dep > closed_platforms[platform]:
        return False
    if platform not in train.compatible_platforms:
        return False
    for other in schedule.values():
        if other.train_id != train.train_id and other.assigned_platform == platform:
            if other.assigned_platform not in (None, "HOLD"):
                # Overlap: arrival_A < departure_B AND arrival_B < departure_A
                if t_arr < other.sched_departure and other.sched_arrival < t_dep:
                    return False
    return True


def get_domain(train: Train, closed_platforms: Dict[str, int]) -> List[str]:
    """Return compatible platforms that are not closed during train occupancy."""
    return [p for p in train.compatible_platforms if p not in closed_platforms or train.sched_departure <= closed_platforms[p]]


def select_mrv(
    unassigned: List[Train], schedule: Dict[str, Train],
    closed_platforms: Dict[str, int], use_priority: bool = True,
) -> Train:
    """MRV heuristic: choose unassigned train with minimum remaining valid platforms."""
    prio_map = {"Emergency": 3, "High": 2, "Normal": 1}
    key_fn = lambda t: (
        sum(1 for p in get_domain(t, closed_platforms) if is_valid_assignment(t, p, schedule, closed_platforms)),
        -prio_map.get(t.priority, 1) if use_priority else 0,
        t.sched_arrival,
    )
    return min(unassigned, key=key_fn)


def forward_check(remaining: List[Train], schedule: Dict[str, Train], closed_platforms: Dict[str, int]) -> bool:
    """Forward Checking: verify every unassigned train still has at least one valid platform."""
    return all(any(is_valid_assignment(t, p, schedule, closed_platforms) for p in get_domain(t, closed_platforms)) for t in remaining)


def backtrack(
    unassigned: List[Train], schedule: Dict[str, Train], closed_platforms: Dict[str, int],
    use_mrv: bool, use_fc: bool, use_priority: bool, stats: Dict[str, int],
) -> bool:
    """Recursive backtracking search with optional MRV and Forward Checking."""
    if not unassigned:
        return True
    var = select_mrv(unassigned, schedule, closed_platforms, use_priority) if use_mrv else sorted(unassigned, key=lambda t: t.sched_arrival)[0]
    valid_platforms = [p for p in get_domain(var, closed_platforms) if is_valid_assignment(var, p, schedule, closed_platforms)]

    for p in valid_platforms:
        stats["nodes"] += 1
        var.assigned_platform = p
        schedule[var.train_id] = var
        rest = [t for t in unassigned if t.train_id != var.train_id]

        if (not use_fc or forward_check(rest, schedule, closed_platforms)) and backtrack(rest, schedule, closed_platforms, use_mrv, use_fc, use_priority, stats):
            return True

        stats["backtracks"] += 1
        var.assigned_platform = None
        schedule.pop(var.train_id, None)
    return False


def apply_rules(trains: List[Train], closed_platforms: Dict[str, int], current_time: int) -> Tuple[List[Train], List[str]]:
    """Rule 1 (Closure unassign), Rule 2 (HOLD), Rule 3 (Priority: Emergency > High > Normal)."""
    affected_ids = []
    for t in trains:
        if t.assigned_platform in closed_platforms and t.sched_departure > closed_platforms[t.assigned_platform]:
            if t.sched_arrival >= current_time:  # Non-frozen future train
                t.assigned_platform = None
                t.is_held = True
                affected_ids.append(t.train_id)
    prio_order = {"Emergency": 3, "High": 2, "Normal": 1}
    return sorted(trains, key=lambda x: (-prio_order.get(x.priority, 1), x.sched_arrival)), affected_ids


def solve_csp(
    trains: List[Train], schedule: Dict[str, Train], closed_platforms: Dict[str, int],
    use_mrv: bool, use_fc: bool, use_priority: bool, stats: Dict[str, int],
) -> None:
    """CSP solver wrapper. On overconstrained bottlenecks, iteratively HOLD lowest priority."""
    unassigned = [t for t in trains if t.assigned_platform in (None, "HOLD")]
    if not unassigned:
        return
    sched_copy = dict(schedule)
    if backtrack(unassigned, sched_copy, closed_platforms, use_mrv, use_fc, use_priority, stats):
        schedule.update(sched_copy)
        for t in unassigned: t.is_held = False
        return

    # Infeasible: HOLD lowest priority train iteratively
    prio_map = {"Emergency": 3, "High": 2, "Normal": 1}
    order_key = (lambda t: (prio_map.get(t.priority, 1), -t.sched_arrival)) if use_priority else (lambda t: -t.sched_arrival)
    subset = sorted(unassigned, key=order_key)
    active = list(unassigned)
    while active:
        dropped = subset.pop(0)
        active.remove(dropped)
        dropped.assigned_platform = "HOLD"
        dropped.is_held = True
        sched_copy = dict(schedule)
        for t in active: t.assigned_platform = None
        if backtrack(active, sched_copy, closed_platforms, use_mrv, use_fc, use_priority, stats):
            schedule.update(sched_copy)
            for t in active: t.is_held = False
            break


def retry_held_trains(trains: List[Train], schedule: Dict[str, Train], closed_platforms: Dict[str, int], current_time: int) -> None:
    """Retry held trains in priority order when platform capacity frees up."""
    prio_map = {"Emergency": 3, "High": 2, "Normal": 1}
    held = sorted([t for t in trains if t.is_held or t.assigned_platform == "HOLD"], key=lambda t: (-prio_map.get(t.priority, 1), t.arrival_time))
    for t in held:
        dwell = t.departure_time - t.arrival_time
        earliest_arr = max(current_time, t.arrival_time + t.delay)
        for p in get_domain(t, closed_platforms):
            if is_valid_assignment(t, p, schedule, closed_platforms, arr=earliest_arr, dep=earliest_arr + dwell):
                t.assigned_platform = p
                t.sched_arrival = earliest_arr
                t.sched_departure = earliest_arr + dwell
                t.sched_delay = max(0, earliest_arr - (t.arrival_time + t.delay))
                t.is_held = False
                schedule[t.train_id] = t
                break


def replan(trains: List[Train], schedule: Dict[str, Train], closed_platforms: Dict[str, int], event: Event, stats: Dict[str, int]) -> List[str]:
    """Dynamic replanning upon disruption: update station state, unassign affected, re-solve CSP."""
    curr, affected = event.time, []
    if event.event_type == "PLATFORM_CLOSURE":
        closed_platforms[event.target] = curr
        for t in trains:
            if t.assigned_platform == event.target and t.sched_departure > curr:
                if t.sched_arrival >= curr:  # Frozen trains (docked/departed) untouched
                    t.assigned_platform = None
                    t.is_held = True
                    schedule.pop(t.train_id, None)
                    affected.append(t.train_id)
    elif event.event_type == "TRAIN_DELAY":
        for t in trains:
            if t.train_id == event.target and curr < t.sched_departure:
                t.delay += event.value
                dwell = t.departure_time - t.arrival_time
                t.sched_arrival = t.arrival_time + t.delay
                t.sched_departure = t.sched_arrival + dwell
                affected.append(t.train_id)
                if t.assigned_platform and not is_valid_assignment(t, t.assigned_platform, schedule, closed_platforms):
                    schedule.pop(t.train_id, None)
                    t.assigned_platform = None
                    t.is_held = True

    future_unassigned = [t for t in trains if t.assigned_platform in (None, "HOLD") and t.sched_arrival >= curr]
    if future_unassigned:
        solve_csp(future_unassigned, schedule, closed_platforms, True, True, True, stats)
    retry_held_trains(trains, schedule, closed_platforms, curr)
    return affected


# ---------------------------------------------------------
# Evaluation Metrics
# ---------------------------------------------------------

def count_conflicts(trains: List[Train], closed_platforms: Dict[str, int]) -> int:
    """Count unresolved conflicts: closed platform use, incompatibility, or platform overlaps."""
    conflicts = 0
    assigned = [t for t in trains if t.assigned_platform not in (None, "HOLD")]
    for t in assigned:
        if t.assigned_platform in closed_platforms and t.sched_departure > closed_platforms[t.assigned_platform]:
            conflicts += 1
        if t.assigned_platform not in t.compatible_platforms:
            conflicts += 1
    for i in range(len(assigned)):
        for j in range(i + 1, len(assigned)):
            ti, tj = assigned[i], assigned[j]
            if ti.assigned_platform == tj.assigned_platform and ti.sched_arrival < tj.sched_departure and tj.sched_arrival < ti.sched_departure:
                conflicts += 1
    return conflicts


def calculate_metrics(trains: List[Train], closed_platforms: Dict[str, int], stats: Dict[str, int], elapsed: float) -> Dict[str, Any]:
    n = len(trains)
    total_delay = sum(t.sched_delay for t in trains)
    pass_wait = sum(t.passenger_load * t.sched_delay for t in trains)
    immed = sum(1 for t in trains if not t.is_held and t.sched_delay == 0 and t.assigned_platform not in (None, "HOLD"))
    final = sum(1 for t in trains if t.assigned_platform not in (None, "HOLD"))
    return {
        "avg_delay": total_delay / n if n else 0.0,
        "passenger_waiting": pass_wait,
        "immediate_rate": (immed / n) * 100.0 if n else 0.0,
        "final_rate": (final / n) * 100.0 if n else 0.0,
        "conflicts": count_conflicts(trains, closed_platforms),
        "nodes": stats["nodes"],
        "backtracks": stats["backtracks"],
        "time_ms": elapsed * 1000.0,
    }


# ---------------------------------------------------------
# The Four Algorithms
# ---------------------------------------------------------

def run_fcfs(input_trains: List[Train], platforms: List[str], events: List[Event]) -> Tuple[List[Train], Dict[str, Any]]:
    """15.1 FCFS: Assign trains in arrival order to first valid platform. No replanning."""
    t0 = time.perf_counter()
    trains, schedule, closed = copy.deepcopy(input_trains), {}, {}
    for t in sorted(trains, key=lambda x: x.arrival_time):
        t.assigned_platform = next((p for p in t.compatible_platforms if is_valid_assignment(t, p, schedule, closed)), "HOLD")
        if t.assigned_platform != "HOLD": schedule[t.train_id] = t
        else: t.is_held = True
    # Stale assignments remain during disruptions
    for ev in events:
        if ev.event_type == "PLATFORM_CLOSURE": closed[ev.target] = ev.time
        elif ev.event_type == "TRAIN_DELAY":
            tgt = next((t for t in trains if t.train_id == ev.target), None)
            if tgt:
                tgt.delay += ev.value
                dwell = tgt.departure_time - tgt.arrival_time
                tgt.sched_arrival = tgt.arrival_time + tgt.delay
                tgt.sched_departure = tgt.sched_arrival + dwell
    return trains, calculate_metrics(trains, closed, {"nodes": 0, "backtracks": 0}, time.perf_counter() - t0)


def run_greedy(input_trains: List[Train], platforms: List[str], events: List[Event]) -> Tuple[List[Train], Dict[str, Any]]:
    """15.2 Greedy: Choose currently valid platform with smallest immediate delay. No replanning."""
    t0 = time.perf_counter()
    trains, schedule, closed = copy.deepcopy(input_trains), {}, {}
    for t in sorted(trains, key=lambda x: x.arrival_time):
        dwell, best_p, best_delay = t.departure_time - t.arrival_time, None, 999999
        for p in t.compatible_platforms:
            if is_valid_assignment(t, p, schedule, closed):
                best_p, best_delay = p, 0; break
        if best_p is None:
            for p in t.compatible_platforms:
                deps = [o.sched_departure for o in schedule.values() if o.assigned_platform == p and o.sched_departure >= t.sched_arrival]
                free_t = max(deps) if deps else t.sched_arrival
                d = free_t - t.sched_arrival
                if d < best_delay and is_valid_assignment(t, p, schedule, closed, arr=free_t, dep=free_t + dwell):
                    best_delay, best_p = d, p
        if best_p and best_delay <= 60:
            t.assigned_platform = best_p; t.sched_arrival += best_delay; t.sched_departure = t.sched_arrival + dwell
            t.sched_delay = best_delay; schedule[t.train_id] = t
        else:
            t.assigned_platform = "HOLD"; t.is_held = True
    for ev in events:
        if ev.event_type == "PLATFORM_CLOSURE": closed[ev.target] = ev.time
        elif ev.event_type == "TRAIN_DELAY":
            tgt = next((t for t in trains if t.train_id == ev.target), None)
            if tgt:
                tgt.delay += ev.value
                dwell = tgt.departure_time - tgt.arrival_time
                tgt.sched_arrival = tgt.arrival_time + tgt.delay
                tgt.sched_departure = tgt.sched_arrival + dwell
    return trains, calculate_metrics(trains, closed, {"nodes": 0, "backtracks": 0}, time.perf_counter() - t0)


def run_basic_csp(input_trains: List[Train], platforms: List[str], events: List[Event]) -> Tuple[List[Train], Dict[str, Any]]:
    """15.3 Basic CSP: Backtracking in arrival order without MRV, FC, or priority. No replanning."""
    t0 = time.perf_counter()
    trains, schedule, closed, stats = copy.deepcopy(input_trains), {}, {}, {"nodes": 0, "backtracks": 0}
    solve_csp(trains, schedule, closed, False, False, False, stats)
    for ev in events:
        if ev.event_type == "PLATFORM_CLOSURE": closed[ev.target] = ev.time
        elif ev.event_type == "TRAIN_DELAY":
            tgt = next((t for t in trains if t.train_id == ev.target), None)
            if tgt:
                tgt.delay += ev.value
                dwell = tgt.departure_time - tgt.arrival_time
                tgt.sched_arrival = tgt.arrival_time + tgt.delay
                tgt.sched_departure = tgt.sched_arrival + dwell
    return trains, calculate_metrics(trains, closed, stats, time.perf_counter() - t0)


def run_proposed_agent(
    input_trains: List[Train], platforms: List[str], events: List[Event], demo_closure: bool = False,
) -> Tuple[List[Train], Dict[str, Any]]:
    """15.4 Proposed Agent: Backtracking + MRV + FC + Priority Rules + Dynamic Replanning."""
    t0 = time.perf_counter()
    trains, schedule, closed, stats = copy.deepcopy(input_trains), {}, {}, {"nodes": 0, "backtracks": 0}
    solve_csp(trains, schedule, closed, True, True, True, stats)

    if demo_closure:
        print("\n" + "=" * 40)
        print("DEMONSTRATION: DYNAMIC PLATFORM CLOSURE")
        print("=" * 40)
        print("Initial Schedule")
        print("-" * 16)
        for t in sorted(trains, key=lambda x: x.sched_arrival):
            p_disp = t.assigned_platform if t.assigned_platform else "HOLD"
            print(f"{t.train_id:4s} -> {p_disp:4s} ({time_to_str(t.sched_arrival)} - {time_to_str(t.sched_departure)})")

    for ev in sorted(events, key=lambda e: e.time):
        affected = replan(trains, schedule, closed, ev, stats)
        if demo_closure and ev.event_type == "PLATFORM_CLOSURE":
            print(f"\nEvent\n-----\n{time_to_str(ev.time)} : {ev.target} CLOSED")
            print(f"\nReplanning\n----------\nAffected train(s): {', '.join(affected) if affected else 'None'}")
            print("\nRevised Schedule\n----------------")
            for t in sorted(trains, key=lambda x: x.sched_arrival):
                p_disp = t.assigned_platform if t.assigned_platform else "HOLD"
                print(f"{t.train_id:4s} -> {p_disp:4s} ({time_to_str(t.sched_arrival)} - {time_to_str(t.sched_departure)}) [Prio: {t.priority}]")
            print("=" * 40 + "\n")

    checkpoints = sorted(set([e.time for e in events] + [t.sched_departure for t in trains if t.assigned_platform not in (None, "HOLD")]))
    for ck in checkpoints:
        retry_held_trains(trains, schedule, closed, ck)
    return trains, calculate_metrics(trains, closed, stats, time.perf_counter() - t0)


# ---------------------------------------------------------
# Test Scenarios
# ---------------------------------------------------------

def build_scenarios(base_trains: List[Train]) -> List[Dict[str, Any]]:
    """Define the 6 required scenarios."""
    return [
        {
            "name": "Scenario 1 --- Normal Operation",
            "desc": "4 platforms, 8 trains, regular schedule, no disruptions.",
            "platforms": ["P1", "P2", "P3", "P4"], "trains": copy.deepcopy(base_trains[:8]), "events": [],
        },
        {
            "name": "Scenario 2 --- Train Delay",
            "desc": "T2 delayed by 10 minutes at 10:05, causing overlap on P2.",
            "platforms": ["P1", "P2", "P3", "P4"], "trains": copy.deepcopy(base_trains[:8]),
            "events": [Event(time=str_to_time("10:05"), event_type="TRAIN_DELAY", target="T2", value=10)],
        },
        {
            "name": "Scenario 3 --- Platform Closure",
            "desc": "Platform P2 closes at 10:12 due to emergency track maintenance.",
            "platforms": ["P1", "P2", "P3", "P4"], "trains": copy.deepcopy(base_trains[:8]),
            "events": [Event(time=str_to_time("10:12"), event_type="PLATFORM_CLOSURE", target="P2")],
        },
        {
            "name": "Scenario 4 --- Platform Competition",
            "desc": "3 competing trains (T1 Normal, T2 High, T3 Emergency) bottlenecked on P1.",
            "platforms": ["P1", "P2", "P3"],
            "trains": [
                Train("T1", 600, 615, "North", "Normal", ["P1"], 100),
                Train("T2", 602, 617, "South", "High", ["P1"], 140),
                Train("T3", 605, 620, "North", "Emergency", ["P1"], 160),
                Train("T4", 600, 615, "South", "Normal", ["P2"], 90),
                Train("T5", 600, 615, "North", "High", ["P3"], 110),
                Train("T6", 616, 630, "South", "Normal", ["P2", "P3"], 95),
            ],
            "events": [],
        },
        {
            "name": "Scenario 5 --- Combined Disruption",
            "desc": "T1 delayed by 12 mins at 10:05 + P3 closed at 10:15.",
            "platforms": ["P1", "P2", "P3", "P4"], "trains": copy.deepcopy(base_trains[:8]),
            "events": [
                Event(time=str_to_time("10:05"), event_type="TRAIN_DELAY", target="T1", value=12),
                Event(time=str_to_time("10:15"), event_type="PLATFORM_CLOSURE", target="P3"),
            ],
        },
        {
            "name": "Scenario 6 --- Tight CSP",
            "desc": "3 platforms, 9 trains, restrictive compatibilities, overlapping intervals.",
            "platforms": ["P1", "P2", "P3"],
            "trains": [
                Train("T1", 600, 615, "North", "Normal", ["P1", "P2", "P3"], 100),
                Train("T2", 601, 615, "South", "Normal", ["P1", "P2"], 90),
                Train("T3", 602, 615, "North", "Emergency", ["P1"], 110),
                Train("T4", 620, 635, "South", "Normal", ["P1", "P2", "P3"], 120),
                Train("T5", 621, 635, "North", "Normal", ["P2", "P3"], 100),
                Train("T6", 622, 635, "South", "High", ["P2"], 130),
                Train("T7", 640, 655, "North", "Normal", ["P1", "P2", "P3"], 140),
                Train("T8", 641, 655, "South", "Normal", ["P1", "P3"], 95),
                Train("T9", 642, 655, "North", "Emergency", ["P3"], 150),
            ],
            "events": [],
        },
    ]


# ---------------------------------------------------------
# Formatting and CLI Output
# ---------------------------------------------------------

def display_scenario(name: str, desc: str, res: Dict[str, Dict[str, Any]]):
    print(f"\n{name}\nDescription: {desc}\n" + "-" * 72)
    print(f"{'Algorithm':<16} | {'Avg Delay':<9} | {'Pass-Min':<9} | {'Immed%':<7} | {'Final%':<7} | {'Conflicts':<9} | {'Nodes':<5} | {'Backtracks':<10}")
    print("-" * 72)
    for algo, m in res.items():
        print(f"{algo:<16} | {m['avg_delay']:>7.2f}m | {m['passenger_waiting']:>9.0f} | {m['immediate_rate']:>6.1f}% | {m['final_rate']:>6.1f}% | {m['conflicts']:>9d} | {m['nodes']:>5d} | {m['backtracks']:>10d}")
    print("-" * 72)


def display_aggregate(agg: Dict[str, Dict[str, float]]):
    print("\n" + "=" * 72 + "\n                   OVERALL ALGORITHM COMPARISON SUMMARY             \n" + "=" * 72)
    print(f"{'Algorithm':<16} | {'Avg Delay':<9} | {'Pass-Min':<9} | {'Final%':<7} | {'Conflicts':<9} | {'Nodes':<6} | {'Backtracks':<10} | {'Time(ms)':<8}\n" + "-" * 72)
    for algo, v in agg.items():
        print(f"{algo:<16} | {v['avg_delay']:>7.2f}m | {v['passenger_waiting']:>9.0f} | {v['final_rate']:>6.1f}% | {int(v['conflicts']):>9d} | {int(v['nodes']):>6d} | {int(v['backtracks']):>10d} | {v['time_ms']:>8.2f}")
    print("=" * 72)


def main():
    print("=" * 72 + "\n      INTELLIGENT METRO PLATFORM ALLOCATION & SCHEDULING AGENT      \n                   Classical AI Demonstration                       \n" + "=" * 72)
    csv_file = os.path.join(os.path.dirname(__file__), "trains.csv")
    print(f"\n[1] Loading train data from: {csv_file}")
    base_trains = load_trains_from_csv(csv_file)
    print(f"    Loaded {len(base_trains)} base trains.")

    scenarios = build_scenarios(base_trains)
    print(f"[2] Prepared {len(scenarios)} test scenarios.")

    all_prop_conflicts = []
    agg = {a: {"avg_delay": 0.0, "passenger_waiting": 0.0, "final_rate": 0.0, "conflicts": 0.0, "nodes": 0.0, "backtracks": 0.0, "time_ms": 0.0} for a in ["FCFS", "Greedy", "Basic CSP", "Proposed Agent"]}

    for idx, sc in enumerate(scenarios):
        _, m_fcfs = run_fcfs(sc["trains"], sc["platforms"], sc["events"])
        _, m_greedy = run_greedy(sc["trains"], sc["platforms"], sc["events"])
        _, m_basic = run_basic_csp(sc["trains"], sc["platforms"], sc["events"])
        _, m_prop = run_proposed_agent(sc["trains"], sc["platforms"], sc["events"], demo_closure=(idx == 2))

        sc_res = {"FCFS": m_fcfs, "Greedy": m_greedy, "Basic CSP": m_basic, "Proposed Agent": m_prop}
        all_prop_conflicts.append(m_prop["conflicts"])
        display_scenario(sc["name"], sc["desc"], sc_res)

        for k in agg:
            for met in ["avg_delay", "passenger_waiting", "final_rate", "conflicts", "nodes", "backtracks", "time_ms"]:
                agg[k][met] += sc_res[k][met]

    num_sc = len(scenarios)
    for k in agg:
        agg[k]["avg_delay"] /= num_sc
        agg[k]["final_rate"] /= num_sc
        agg[k]["time_ms"] /= num_sc

    display_aggregate(agg)

    print("\n[Proposed Agent Verification Check]")
    total_prop_conflicts = sum(all_prop_conflicts)
    print(f"Total Proposed Agent Conflicts across all scenarios: {total_prop_conflicts}")
    if total_prop_conflicts == 0:
        print("Proposed Agent Conflict Check: PASS\n")
    else:
        print("Proposed Agent Conflict Check: FAIL (Unresolved conflicts detected!)\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
