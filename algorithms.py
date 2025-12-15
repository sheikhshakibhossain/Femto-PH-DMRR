import statistics
from collections import deque

# --- BASE CLASS ---
class Scheduler:
    def __init__(self, name, processes):
        self.name = name
        # Deep copy needed to simulate distinct runs
        self.processes = processes 
        self.completed_processes = []
        self.log = []

    def run(self):
        pass # To be implemented by children

# --- STANDARD ROUND ROBIN (BASELINE) ---
class RoundRobin(Scheduler):
    def __init__(self, processes, quantum):
        super().__init__(f"Round Robin (Q={quantum})", processes)
        self.quantum = quantum

    def run(self):
        time = 0
        queue = deque()
        procs = sorted(self.processes, key=lambda x: x.arrival_time)
        p_idx = 0
        
        while len(self.completed_processes) < len(self.processes):
            # 1. Arrival Check
            while p_idx < len(procs) and procs[p_idx].arrival_time <= time:
                queue.append(procs[p_idx])
                p_idx += 1
            
            if not queue:
                time += 1
                continue

            # 2. Execute
            p = queue.popleft()
            if p.start_time == -1: p.start_time = time
            
            run_time = min(p.remaining_time, self.quantum)
            time += run_time
            p.remaining_time -= run_time
            
            # 3. Completion or Requeue
            if p.remaining_time == 0:
                # Move to next burst or finish
                p.current_burst_index += 1
                if p.current_burst_index < len(p.bursts):
                    p.remaining_time = p.bursts[p.current_burst_index]
                    queue.append(p) # Simulate I/O instant return for simplicity
                else:
                    p.completion_time = time
                    self.completed_processes.append(p)
            else:
                queue.append(p)

# --- YOUR ALGORITHM: FEMTO-WINDOW ---
class FemtoScheduler(Scheduler):
    def __init__(self, processes):
        super().__init__("Femto-Window AI", processes)
        self.WINDOW_SIZE = 5

    # PHASE 1: FEMTO-AI PREDICTION
    def femto_predict(self, p):
        # 1. Warm-up
        if len(p.burst_history) < self.WINDOW_SIZE:
            return statistics.mean(p.burst_history) if p.burst_history else 5
        
        # 2. Stats
        window = p.burst_history[-self.WINDOW_SIZE:]
        avg = statistics.mean(window)
        min_v, max_v = min(window), max(window)
        
        # Trend Detection
        is_increasing = all(x < y for x, y in zip(window, window[1:]))
        range_var = max_v - min_v
        
        # 3. Decision Tree
        if range_var < (avg * 0.20): # Case A: Stable
            p.is_volatile = False
            return avg
        elif is_increasing:          # Case B: Ramping
            p.is_volatile = False
            return window[-1] * 1.2
        else:                        # Case C: Volatile
            p.is_volatile = True
            return max_v

    # PHASE 2: DYNAMIC QUANTUM
    def calculate_system_quantum(self, ready_queue):
        if not ready_queue: return 5
        
        predictions = []
        for p in ready_queue:
            pred = self.femto_predict(p)
            p.predicted_next = pred
            predictions.append(pred)
            
        if not predictions: return 5
        
        # Median Calculation
        median = statistics.median(predictions)
        
        # Clamp (Safety Bounds)
        return max(2, min(int(median), 25))

    def run(self):
        time = 0
        queue = [] # List for flexible manipulation
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

            # --- DYNAMIC QUANTUM CALCULATION ---
            tq = self.calculate_system_quantum(queue)
            
            # --- EXECUTION ---
            p = queue.pop(0) # FIFO dispatch
            if p.start_time == -1: p.start_time = time
            
            run_time = min(p.remaining_time, tq)
            time += run_time
            p.remaining_time -= run_time
            
            # Update History (Push actual runtime to window)
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
                queue.append(p) # Preempted