import sys
import os
import csv
import time

def parse_time(t_str):
    parts = t_str.strip().split(':')
    return int(parts[0]) * 60 + int(parts[1])

def format_time(mins):
    return f"{mins // 60:02d}:{mins % 60:02d}"

def read_trains(filepath):
    trains = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            arr = parse_time(row['arrival'])
            dep = parse_time(row['departure'])
            trains.append({
                'id': row['train_id'],
                'arrival': arr,
                'departure': dep,
                'dwell': dep - arr,
                'direction': row['direction'],
                'priority': row['priority'],
                'passengers': int(row['passengers']),
                'platforms': [int(p) for p in row['platforms'].split('|')],
                'delay': int(row.get('delay', 0))
            })
    return trains

def is_valid(train_id, platform, start, end, schedule):
    if platform is None:
        return True
    for tid, alloc in schedule.items():
        if tid != train_id and alloc['platform'] == platform:
            if start < alloc['end'] and alloc['start'] < end:
                return False
    return True

def get_valid_platforms(train, start, end, schedule, open_platforms):
    valid = []
    for p in train['platforms']:
        if p in open_platforms and is_valid(train['id'], p, start, end, schedule):
            valid.append(p)
    return valid

def check_conflicts(schedule):
    conflicts = 0
    items = list(schedule.items())
    for i in range(len(items)):
        t1, a1 = items[i]
        if a1['platform'] is None:
            continue
        for j in range(i + 1, len(items)):
            t2, a2 = items[j]
            if a2['platform'] is None:
                continue
            if a1['platform'] == a2['platform']:
                if a1['start'] < a2['end'] and a2['start'] < a1['end']:
                    conflicts += 1
    return conflicts

def priority_score(priority):
    if priority == 'Emergency':
        return 3
    if priority == 'High':
        return 2
    return 1

def fcfs(trains, open_platforms):
    sorted_trains = sorted(trains, key=lambda t: t['arrival'] + t['delay'])
    schedule = {}
    for t in sorted_trains:
        start = t['arrival'] + t['delay']
        end = start + t['dwell']
        compatible = [p for p in t['platforms'] if p in open_platforms]
        assigned_plat = None
        for p in compatible:
            if is_valid(t['id'], p, start, end, schedule):
                assigned_plat = p
                break
        if assigned_plat is not None:
            schedule[t['id']] = {'platform': assigned_plat, 'start': start, 'end': end, 'wait': 0, 'action': 'ASSIGN'}
        elif compatible:
            schedule[t['id']] = {'platform': compatible[0], 'start': start, 'end': end, 'wait': 0, 'action': 'ASSIGN'}
        else:
            schedule[t['id']] = {'platform': None, 'start': start, 'end': end, 'wait': 0, 'action': 'HOLD'}
    return schedule

def find_earliest_slot(train_id, platform, target_start, dwell, schedule):
    s = target_start
    while True:
        conflict = False
        next_s = s
        for tid, alloc in schedule.items():
            if tid != train_id and alloc['platform'] == platform:
                if s < alloc['end'] and alloc['start'] < s + dwell:
                    conflict = True
                    if alloc['end'] > next_s:
                        next_s = alloc['end']
        if not conflict:
            return s
        s = next_s

def greedy(trains, open_platforms):
    sorted_trains = sorted(trains, key=lambda t: t['arrival'] + t['delay'])
    schedule = {}
    for t in sorted_trains:
        base_start = t['arrival'] + t['delay']
        comp = [p for p in t['platforms'] if p in open_platforms]
        if not comp:
            schedule[t['id']] = {'platform': None, 'start': base_start, 'end': base_start + t['dwell'], 'wait': 0, 'action': 'HOLD'}
            continue
        best_w = 999999
        best_p = comp[0]
        for p in comp:
            w = find_earliest_slot(t['id'], p, base_start, t['dwell'], schedule) - base_start
            if w < best_w:
                best_w = w
                best_p = p
        s = base_start + best_w
        act = 'ASSIGN' if best_w == 0 else 'HOLD'
        schedule[t['id']] = {'platform': best_p, 'start': s, 'end': s + t['dwell'], 'wait': best_w, 'action': act}
    return schedule

def basic_csp(trains, open_platforms):
    nodes = [0]
    backtracks = [0]
    sorted_trains = sorted(trains, key=lambda t: t['arrival'] + t['delay'])
    best_sched = {}

    def backtrack(idx, current_sched):
        if len(current_sched) > len(best_sched):
            best_sched.clear()
            best_sched.update(current_sched)
        if idx == len(sorted_trains):
            return current_sched
        t = sorted_trains[idx]
        start = t['arrival'] + t['delay']
        end = start + t['dwell']
        for p in [plat for plat in t['platforms'] if plat in open_platforms]:
            nodes[0] += 1
            if is_valid(t['id'], p, start, end, current_sched):
                current_sched[t['id']] = {'platform': p, 'start': start, 'end': end, 'wait': 0, 'action': 'ASSIGN'}
                res = backtrack(idx + 1, current_sched)
                if res is not None:
                    return res
                del current_sched[t['id']]
                backtracks[0] += 1
        return None

    res = backtrack(0, {})
    final_sched = res if res is not None else dict(best_sched)
    for t in sorted_trains:
        if t['id'] not in final_sched:
            start = t['arrival'] + t['delay']
            final_sched[t['id']] = {'platform': None, 'start': start, 'end': start + t['dwell'], 'wait': 0, 'action': 'HOLD'}
    return final_sched, nodes[0], backtracks[0]

def proposed_agent(trains, open_platforms, base_schedule=None):
    nodes = [0]
    backtracks = [0]
    train_map = {t['id']: t for t in trains}
    current_sched = {tid: dict(alloc) for tid, alloc in base_schedule.items()} if base_schedule else {}
    unassigned_ids = [t['id'] for t in trains if t['id'] not in current_sched]
    
    def solve(rem_ids, sched):
        if not rem_ids:
            return sched
        cand = []
        for tid in rem_ids:
            t = train_map[tid]
            st = t['arrival'] + t['delay']
            val = get_valid_platforms(t, st, st + t['dwell'], sched, open_platforms)
            cand.append((len(val), -priority_score(t['priority']), -t['passengers'], tid, val))
        cand.sort()
        mrv_train_id = cand[0][3]
        min_domains = cand[0][4]
        if not min_domains:
            return None
        chosen = train_map[mrv_train_id]
        st = chosen['arrival'] + chosen['delay']
        en = st + chosen['dwell']
        for p in min_domains:
            nodes[0] += 1
            sched[mrv_train_id] = {'platform': p, 'start': st, 'end': en, 'wait': 0, 'action': 'ASSIGN'}
            fc_ok = True
            for other_id in rem_ids:
                if other_id != mrv_train_id:
                    ot = train_map[other_id]
                    ost = ot['arrival'] + ot['delay']
                    if not get_valid_platforms(ot, ost, ost + ot['dwell'], sched, open_platforms):
                        fc_ok = False
                        break
            if fc_ok:
                next_rem = [tid for tid in rem_ids if tid != mrv_train_id]
                res = solve(next_rem, sched)
                if res is not None:
                    return res
            del sched[mrv_train_id]
            backtracks[0] += 1
        return None

    solution = solve(list(unassigned_ids), current_sched)
    if solution is None:
        rem_trains = [train_map[tid] for tid in unassigned_ids if tid not in current_sched]
        rem_trains.sort(key=lambda t: (-priority_score(t['priority']), -t['passengers']))
        for t in rem_trains:
            base_start = t['arrival'] + t['delay']
            comp = [p for p in t['platforms'] if p in open_platforms]
            if not comp:
                current_sched[t['id']] = {'platform': None, 'start': base_start, 'end': base_start + t['dwell'], 'wait': 0, 'action': 'HOLD'}
                continue
            best_w = 999999
            best_p = comp[0]
            for p in comp:
                w = find_earliest_slot(t['id'], p, base_start, t['dwell'], current_sched) - base_start
                if w < best_w:
                    best_w = w
                    best_p = p
            s = base_start + best_w
            act = 'ASSIGN' if best_w == 0 else 'HOLD'
            current_sched[t['id']] = {'platform': best_p, 'start': s, 'end': s + t['dwell'], 'wait': best_w, 'action': act}
        solution = current_sched
    return solution, nodes[0], backtracks[0]

def replan(prev_sched, trains, open_platforms, event_time):
    fixed = {}
    for tid, alloc in prev_sched.items():
        if alloc['start'] < event_time:
            fixed[tid] = dict(alloc)
            if alloc['end'] <= event_time:
                fixed[tid]['action'] = 'DEPART'
    t_start = time.perf_counter()
    new_sched, nodes, btracks = proposed_agent(trains, open_platforms, fixed)
    exec_time = (time.perf_counter() - t_start) * 1000
    reassignments = 0
    for tid, alloc in new_sched.items():
        if tid in prev_sched and prev_sched[tid]['platform'] is not None:
            if alloc['platform'] != prev_sched[tid]['platform']:
                alloc['action'] = 'REASSIGN'
                reassignments += 1
    return new_sched, reassignments, nodes, btracks, exec_time

def calculate_metrics(trains, schedule, num_platforms, exec_time, nodes, backtracks, reassignments):
    train_map = {t['id']: t for t in trains}
    total_wait = sum(alloc['wait'] for alloc in schedule.values())
    avg_delay = total_wait / len(trains) if trains else 0.0
    pax_wait = sum(train_map[tid]['passengers'] * alloc['wait'] for tid, alloc in schedule.items())
    conflicts = check_conflicts(schedule)
    assigned = sum(1 for alloc in schedule.values() if alloc['platform'] is not None)
    assigned_times = [(alloc['start'], alloc['end']) for alloc in schedule.values() if alloc['platform'] is not None]
    if assigned_times:
        span = max(x[1] for x in assigned_times) - min(x[0] for x in assigned_times)
        total_dwell = sum(train_map[tid]['dwell'] for tid, alloc in schedule.items() if alloc['platform'] is not None)
        util = (total_dwell / (num_platforms * span) * 100) if span > 0 else 0.0
    else:
        util = 0.0
    return {
        'avg_delay': avg_delay,
        'pax_wait': pax_wait,
        'conflicts': conflicts,
        'assigned': f"{assigned}/{len(trains)}",
        'util': util,
        'reassignments': reassignments,
        'exec_time': exec_time,
        'nodes': nodes,
        'backtracks': backtracks
    }

def print_schedule(schedule):
    for tid in sorted(schedule.keys()):
        alloc = schedule[tid]
        if alloc['platform'] is not None:
            print(f"{tid} -> Platform {alloc['platform']}")
        else:
            print(f"{tid} -> HOLD")

def print_replan_changes(prev_sched, new_sched):
    for tid in sorted(new_sched.keys()):
        new_alloc = new_sched[tid]
        prev_alloc = prev_sched.get(tid)
        if prev_alloc is None or new_alloc['platform'] != prev_alloc['platform']:
            if new_alloc['platform'] is not None:
                print(f"{tid} -> Platform {new_alloc['platform']}")
            else:
                print(f"{tid} -> HOLD")

def print_comparison_table(metrics_dict):
    print("\nALGORITHM COMPARISON\n")
    print(f"{'Algorithm':<16} {'Delay':<10} {'Conflicts':<11} {'Assignments':<13} {'Reassignments':<13}")
    print("-" * 65)
    for name, m in metrics_dict.items():
        delay_str = f"{m['avg_delay']:.2f}m"
        print(f"{name:<16} {delay_str:<10} {m['conflicts']:<11} {m['assigned']:<13} {m['reassignments']:<13}")
    print("\nDetailed Metrics:")
    for name, m in metrics_dict.items():
        nodes_str = f" (Nodes: {m['nodes']}, Backtracks: {m['backtracks']})" if m['nodes'] > 0 else ""
        print(f"  {name}: Pax-Wait: {m['pax_wait']} pax-min, Util: {m['util']:.1f}%, Time: {m['exec_time']:.3f} ms{nodes_str}")

def run_scenario(name, trains, open_platforms, events=None):
    print("========================================")
    print("INTELLIGENT METRO PLATSOURCE ALLOCATION".replace("PLATSOURCE", "PLATFORM"))
    print("========================================")
    print(f"\nScenario: {name}\n")
    t0 = time.perf_counter()
    init_sched, p_nodes, p_back = proposed_agent(trains, open_platforms)
    init_time = (time.perf_counter() - t0) * 1000
    print("Initial Schedule")
    print_schedule(init_sched)
    current_trains = [dict(t) for t in trains]
    current_platforms = list(open_platforms)
    reassign_total = 0
    final_sched = init_sched
    final_time = init_time
    if events:
        for ev in events:
            ev_time = parse_time(ev['time'])
            print(f"\nEvent: {ev['description']}\n")
            if 'delay_train' in ev:
                for t in current_trains:
                    if t['id'] == ev['delay_train']:
                        t['delay'] += ev['delay_mins']
            if 'close_platform' in ev:
                if ev['close_platform'] in current_platforms:
                    current_platforms.remove(ev['close_platform'])
            print("Replanning...\n")
            revised_sched, r_count, p_nodes, p_back, final_time = replan(
                final_sched, current_trains, current_platforms, ev_time
            )
            print_replan_changes(final_sched, revised_sched)
            final_sched = revised_sched
            reassign_total += r_count
    num_p = len(current_platforms)
    t0 = time.perf_counter()
    f_sched = fcfs(current_trains, current_platforms)
    t_fcfs = (time.perf_counter() - t0) * 1000
    m_fcfs = calculate_metrics(current_trains, f_sched, num_p, t_fcfs, 0, 0, 0)
    t0 = time.perf_counter()
    g_sched = greedy(current_trains, current_platforms)
    t_greedy = (time.perf_counter() - t0) * 1000
    m_greedy = calculate_metrics(current_trains, g_sched, num_p, t_greedy, 0, 0, 0)
    t0 = time.perf_counter()
    b_sched, b_nodes, b_back = basic_csp(current_trains, current_platforms)
    t_bcsp = (time.perf_counter() - t0) * 1000
    m_bcsp = calculate_metrics(current_trains, b_sched, num_p, t_bcsp, b_nodes, b_back, 0)
    m_prop = calculate_metrics(current_trains, final_sched, num_p, final_time, p_nodes, p_back, reassign_total)
    metrics_all = {
        'FCFS': m_fcfs,
        'Greedy': m_greedy,
        'Basic CSP': m_bcsp,
        'Proposed': m_prop
    }
    print_comparison_table(metrics_all)
    conflict_check = "PASS" if check_conflicts(final_sched) == 0 else "FAIL"
    print(f"\nProposed Agent Conflict Check: {conflict_check}\n")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    trains = read_trains(os.path.join(script_dir, 'trains.csv'))
    target = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    scenarios = [
        (1, "Normal", trains, [1, 2, 3, 4], None),
        (2, "Delayed Train", trains, [1, 2, 3, 4], [
            {'time': '09:05', 'description': 'Train T3 delayed by 5 mins', 'delay_train': 'T3', 'delay_mins': 5}
        ]),
        (3, "Platform Closure", trains, [1, 2, 3, 4], [
            {'time': '09:05', 'description': 'Platform 2 closed', 'close_platform': 2}
        ]),
        (4, "Platform Competition", [dict(t, platforms=[1, 2] if t['id'] in ['T1', 'T2', 'T3', 'T5'] else t['platforms']) for t in trains], [1, 2, 3, 4], None),
        (5, "Combined", trains, [1, 2, 3, 4], [
            {'time': '09:05', 'description': 'Train T3 delayed by 4 mins', 'delay_train': 'T3', 'delay_mins': 4},
            {'time': '09:07', 'description': 'Platform 2 closed', 'close_platform': 2}
        ])
    ]
    for num, name, s_trains, s_plats, s_events in scenarios:
        if target is None or target == num:
            run_scenario(name, s_trains, s_plats, s_events)

if __name__ == '__main__':
    main()
