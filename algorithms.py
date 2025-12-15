import statistics
from collections import deque

# --- BASE CLASS ---
class Scheduler:
    def __init__(self, name, processes):
        self.name = name
        self.processes = processes 
        self.completed_processes = []

    def run(self):
        pass 

# ---------------------------------------------------------
# 1. FIRST COME FIRST SERVED (FCFS)
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
            # Arrival
            while p_idx < len(procs) and procs[p_idx].arrival_time <= time:
                queue.append(procs[p_idx])
                p_idx += 1
            
            if not queue:
                time += 1
                continue

            # Execute Head of Queue (Non-Preemptive)
            p = queue.pop(0)
            if p.start_time == -1: p.start_time = time
            
            # Run entire burst
            burst = p.remaining_time
            time += burst
            p.remaining_time = 0
            
            # Completion
            p.current_burst_index += 1
            if p.current_burst_index < len(p.bursts):
                p.remaining_time = p.bursts[p.current_burst_index]
                # In FCFS, if it returns from I/O, it goes to back of line
                # (Simulating immediate I/O return for this test)
                queue.append(p) 
            else:
                p.completion_time = time
                self.completed_processes.append(p)

# ---------------------------------------------------------
# 2. SHORTEST JOB FIRST (SJF - Non-Preemptive)
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

            # Sort by Burst Time (Smallest First)
            queue.sort(key=lambda x: x.remaining_time)
            
            p = queue.pop(0)
            if p.start_time == -1: p.start_time = time
            
            burst = p.remaining_time
            time += burst
            p.remaining_time = 0
            
            p.current_burst_index += 1
            if p.current_burst_index < len(p.bursts):
                p.remaining_time = p.bursts[p.current_burst_index]
                # Note: In real OS, I/O happens in background. 
                # Here we re-add to queue for next burst.
                # New burst length might be different, so it will be re-sorted next loop.
                # We don't add to queue immediately to simulate I/O wait, 
                # but for CPU scheduling logic testing, we add it back.
                # However, strictly, it should only be available after I/O. 
                # For this burst-only sim, we add it back.
                queue.append(p) 
            else:
                p.completion_time = time
                self.completed_processes.append(p)

# ---------------------------------------------------------
# 3. SHORTEST REMAINING TIME FIRST (SRTF - Preemptive)
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
            # Check Arrivals
            while p_idx < len(procs) and procs[p_idx].arrival_time <= time:
                queue.append(procs[p_idx])
                p_idx += 1
            
            # Return current process to queue to re-evaluate
            if current_p and current_p.remaining_time > 0:
                queue.append(current_p)
                current_p = None
                
            if not queue:
                time += 1
                continue

            # Pick process with smallest remaining time
            queue.sort(key=lambda x: x.remaining_time)
            current_p = queue.pop(0)
            
            if current_p.start_time == -1: current_p.start_time = time
            
            # Run for 1 tick
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
# 4. PRIORITY + ROUND ROBIN (Preemptive)
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
        
        # Track runtime for RR logic within priority levels
        current_p_runtime = 0 
        
        while len(self.completed_processes) < len(self.processes):
            while p_idx < len(procs) and procs[p_idx].arrival_time <= time:
                queue.append(procs[p_idx])
                p_idx += 1
            
            if not queue:
                time += 1
                continue

            # Sort: Primary = Priority (1 is high), Secondary = Arrival (FCFS stability)
            # In Python sort is stable, so we just sort by priority
            queue.sort(key=lambda x: x.priority) 
            
            # Pick highest priority (lowest number)
            # To implement RR for SAME priority, we need to be careful not to 
            # just pick index 0 every time if we didn't rotate.
            # Simple approach: Pick index 0. If it hits Quantum, move to back of 
            # its priority group.
            
            # We will use a standard tick-based loop for preemption
            p = queue.pop(0) 
            
            if p.start_time == -1: p.start_time = time
            
            # Run 1 tick
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
                    # Re-add. Will be sorted by priority next loop.
                    # effectively putting it at tail of its priority class
                    queue.append(p)
                else:
                    p.completion_time = time
                    self.completed_processes.append(p)
            
            if not finished:
                # Check Quantum
                if current_p_runtime >= self.quantum:
                    current_p_runtime = 0
                    queue.append(p) # Rotate to back (RR)
                else:
                    # Check for higher priority arrival?
                    # In this loop logic, we re-sort next tick anyway.
                    # So we just put it back at the HEAD if we want to continue,
                    # or TAIL if we want to yield. 
                    # For strict Preemptive: Put back in queue. Sort will decide.
                    # But to maintain RR state, we must ensure it stays ahead of 
                    # others of same priority UNLESS quantum expired.
                    # Simpler: Insert at index 0
                    queue.insert(0, p)
                    
                    # BUT, if a NEW process arrived with BETTER priority, 
                    # the sort at top of loop will displace p. That is correct preemption.
                    # If new process has SAME priority, stable sort keeps p at 0. Correct.

# ---------------------------------------------------------
# 5. ROUND ROBIN (Existing)
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
# 6. FEMTO-WINDOW (Your Algorithm)
# ---------------------------------------------------------
class FemtoScheduler(Scheduler):
    def __init__(self, processes):
        super().__init__("Femto-Window AI", processes)
        self.WINDOW_SIZE = 5

    def femto_predict(self, p):
        if len(p.burst_history) < self.WINDOW_SIZE:
            return statistics.mean(p.burst_history) if p.burst_history else 5
        window = p.burst_history[-self.WINDOW_SIZE:]
        avg = statistics.mean(window)
        min_v, max_v = min(window), max(window)
        is_increasing = all(x < y for x, y in zip(window, window[1:]))
        range_var = max_v - min_v
        
        if range_var < (avg * 0.20): return avg
        elif is_increasing: return window[-1] * 1.2
        else: return max_v

    def calculate_system_quantum(self, ready_queue):
        if not ready_queue: return 5
        predictions = [self.femto_predict(p) for p in ready_queue]
        if not predictions: return 5
        median = statistics.median(predictions)
        return max(2, min(int(median), 25))

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

            tq = self.calculate_system_quantum(queue)
            p = queue.pop(0)
            if p.start_time == -1: p.start_time = time
            
            run_time = min(p.remaining_time, tq)
            time += run_time
            p.remaining_time -= run_time
            p.burst_history.append(run_time)
            
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