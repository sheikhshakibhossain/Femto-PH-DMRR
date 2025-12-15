import statistics
from collections import deque

# --- BASE CLASS ---
class Scheduler:
    def __init__(self, name, processes):
        self.name = name
        self.processes = processes 
        self.completed_processes = []
        self.context_switches = 0 # NEW METRIC

    def run(self):
        pass 

# ---------------------------------------------------------
# 1. FCFS
# ---------------------------------------------------------
class FCFS(Scheduler):
    def __init__(self, processes):
        super().__init__("FCFS", processes)

    def run(self):
        time = 0
        queue = []
        procs = sorted(self.processes, key=lambda x: x.arrival_time)
        p_idx = 0
        
        while len(self.completed_processes) < len(self.processes):
            while p_idx < len(procs) and procs[p_idx].arrival_time <= time:
                queue.append(procs[p_idx])
                p_idx += 1
            
            if not queue:
                time += 1
                continue

            self.context_switches += 1 # Count Switch
            p = queue.pop(0)
            if p.start_time == -1: p.start_time = time
            
            burst = p.remaining_time
            time += burst
            p.remaining_time = 0
            
            p.current_burst_index += 1
            if p.current_burst_index < len(p.bursts):
                p.remaining_time = p.bursts[p.current_burst_index]
                queue.append(p) 
            else:
                p.completion_time = time
                self.completed_processes.append(p)

# ---------------------------------------------------------
# 2. SJF (Non-Pre)
# ---------------------------------------------------------
class SJF(Scheduler):
    def __init__(self, processes):
        super().__init__("SJF (Non-Pre)", processes)

    def run(self):
        time = 0
        queue = []
        procs = sorted(self.processes, key=lambda x: x.arrival_time)
        p_idx = 0
        
        while len(self.completed_processes) < len(self.processes):
            while p_idx < len(procs) and procs[p_idx].arrival_time <= time:
                queue.append(procs[p_idx])
                p_idx += 1
            
            if not queue:
                time += 1
                continue

            queue.sort(key=lambda x: x.remaining_time)
            
            self.context_switches += 1
            p = queue.pop(0)
            if p.start_time == -1: p.start_time = time
            
            burst = p.remaining_time
            time += burst
            p.remaining_time = 0
            
            p.current_burst_index += 1
            if p.current_burst_index < len(p.bursts):
                p.remaining_time = p.bursts[p.current_burst_index]
                queue.append(p) 
            else:
                p.completion_time = time
                self.completed_processes.append(p)

# ---------------------------------------------------------
# 3. SRTF (Preemptive)
# ---------------------------------------------------------
class SRTF(Scheduler):
    def __init__(self, processes):
        super().__init__("SRTF (Preemptive)", processes)

    def run(self):
        time = 0
        queue = []
        procs = sorted(self.processes, key=lambda x: x.arrival_time)
        p_idx = 0
        current_p = None
        
        while len(self.completed_processes) < len(self.processes):
            while p_idx < len(procs) and procs[p_idx].arrival_time <= time:
                queue.append(procs[p_idx])
                p_idx += 1
            
            if current_p and current_p.remaining_time > 0:
                queue.append(current_p)
                current_p = None
                
            if not queue:
                time += 1
                continue

            queue.sort(key=lambda x: x.remaining_time)
            
            # Check if we are switching to a DIFFERENT process
            if not current_p or current_p != queue[0]:
                 self.context_switches += 1
            
            current_p = queue.pop(0)
            
            if current_p.start_time == -1: current_p.start_time = time
            
            time += 1
            current_p.remaining_time -= 1
            
            if current_p.remaining_time == 0:
                current_p.current_burst_index += 1
                if current_p.current_burst_index < len(current_p.bursts):
                    current_p.remaining_time = current_p.bursts[current_p.current_burst_index]
                    queue.append(current_p)
                else:
                    current_p.completion_time = time
                    self.completed_processes.append(current_p)
                current_p = None

# ---------------------------------------------------------
# 4. Priority + RR
# ---------------------------------------------------------
class PriorityRR(Scheduler):
    def __init__(self, processes, quantum=4):
        super().__init__(f"Priority+RR (Q={quantum})", processes)
        self.quantum = quantum

    def run(self):
        time = 0
        queue = []
        procs = sorted(self.processes, key=lambda x: x.arrival_time)
        p_idx = 0
        current_p_runtime = 0 
        
        while len(self.completed_processes) < len(self.processes):
            while p_idx < len(procs) and procs[p_idx].arrival_time <= time:
                queue.append(procs[p_idx])
                p_idx += 1
            
            if not queue:
                time += 1
                continue

            queue.sort(key=lambda x: x.priority) 
            
            # Simplified Switch Counting: Increment on every pop
            self.context_switches += 1
            
            p = queue.pop(0) 
            if p.start_time == -1: p.start_time = time
            
            time += 1
            p.remaining_time -= 1
            current_p_runtime += 1
            
            finished = False
            if p.remaining_time == 0:
                finished = True
                current_p_runtime = 0
                p.current_burst_index += 1
                if p.current_burst_index < len(p.bursts):
                    p.remaining_time = p.bursts[p.current_burst_index]
                    queue.append(p)
                else:
                    p.completion_time = time
                    self.completed_processes.append(p)
            
            if not finished:
                if current_p_runtime >= self.quantum:
                    current_p_runtime = 0
                    queue.append(p)
                else:
                    queue.insert(0, p) # Stay at head (no switch cost theoretically, but simplified here)

# ---------------------------------------------------------
# 5. Round Robin
# ---------------------------------------------------------
class RoundRobin(Scheduler):
    def __init__(self, processes, quantum):
        super().__init__(f"Round Robin (Q={quantum})", processes)
        self.quantum = quantum

    def run(self):
        time = 0
        queue = []
        procs = sorted(self.processes, key=lambda x: x.arrival_time)
        p_idx = 0
        
        while len(self.completed_processes) < len(self.processes):
            while p_idx < len(procs) and procs[p_idx].arrival_time <= time:
                queue.append(procs[p_idx])
                p_idx += 1
            
            if not queue:
                time += 1
                continue

            self.context_switches += 1
            p = queue.pop(0)
            if p.start_time == -1: p.start_time = time
            
            run_time = min(p.remaining_time, self.quantum)
            time += run_time
            p.remaining_time -= run_time
            
            if p.remaining_time == 0:
                p.current_burst_index += 1
                if p.current_burst_index < len(p.bursts):
                    p.remaining_time = p.bursts[p.current_burst_index]
                    queue.append(p)
                else:
                    p.completion_time = time
                    self.completed_processes.append(p)
            else:
                queue.append(p)

# ---------------------------------------------------------
# 6. FEMTO-WINDOW (FIXED LOGIC)
# ---------------------------------------------------------
class FemtoScheduler(Scheduler):
    def __init__(self, processes):
        super().__init__("Femto-Window AI", processes)
        self.WINDOW_SIZE = 5
        # Ensure accumulator is reset
        for p in self.processes:
            p.current_burst_accumulated = 0

    def femto_predict(self, p):
        # FIX: Prediction must account for accumulated time
        if not p.burst_history:
            return max(5, p.current_burst_accumulated + 5)
        
        window = p.burst_history[-self.WINDOW_SIZE:]
        avg = statistics.mean(window)
        min_v, max_v = min(window), max(window)
        
        is_increasing = all(x < y for x, y in zip(window, window[1:]))
        range_var = max_v - min_v
        
        prediction = avg
        if range_var < (avg * 0.20): 
            prediction = avg
        elif is_increasing: 
            prediction = window[-1] * 1.2
        else: 
            prediction = max_v
            
        # FIX: Never predict less than what has already happened in this burst
        return max(prediction, p.current_burst_accumulated + 2)

    def calculate_system_quantum(self, ready_queue):
        if not ready_queue: return 5
        predictions = [self.femto_predict(p) for p in ready_queue]
        if not predictions: return 5
        median = statistics.median(predictions)
        # FIX: Increased Max Limit to 40 to accommodate heavy workload
        return max(5, min(int(median), 40))

    def run(self):
        time = 0
        queue = []
        procs = sorted(self.processes, key=lambda x: x.arrival_time)
        p_idx = 0
        
        while len(self.completed_processes) < len(self.processes):
            while p_idx < len(procs) and procs[p_idx].arrival_time <= time:
                # Reset accumulator on arrival
                procs[p_idx].current_burst_accumulated = 0
                queue.append(procs[p_idx])
                p_idx += 1
                
            if not queue:
                time += 1
                continue

            tq = self.calculate_system_quantum(queue)
            
            self.context_switches += 1
            p = queue.pop(0)
            if p.start_time == -1: p.start_time = time
            
            run_time = min(p.remaining_time, tq)
            time += run_time
            p.remaining_time -= run_time
            
            # FIX: Accumulate runtime
            p.current_burst_accumulated += run_time
            
            if p.remaining_time == 0:
                # FIX: Only update history when burst finishes
                p.burst_history.append(p.current_burst_accumulated)
                p.current_burst_accumulated = 0 
                
                p.current_burst_index += 1
                if p.current_burst_index < len(p.bursts):
                    p.remaining_time = p.bursts[p.current_burst_index]
                    queue.append(p)
                else:
                    p.completion_time = time
                    self.completed_processes.append(p)
            else:
                queue.append(p)