import random

class Process:
    def __init__(self, pid, arrival_time, behavior):
        self.pid = pid
        self.arrival_time = arrival_time
        self.behavior = behavior
        self.bursts = self._generate_bursts()
        self.priority = random.randint(1, 5)
        
        # State variables
        self.current_burst_index = 0
        self.remaining_time = 0 if not self.bursts else self.bursts[0]
        self.start_time = -1
        self.finish_time = 0
        self.completion_time = 0
        
        # Femto-Window Context
        self.burst_history = [] 
        self.current_burst_accumulated = 0 # NEW: Tracks partial execution
        self.predicted_next = 0
        self.is_volatile = False

    def _generate_bursts(self):
        # Increased count slightly
        count = random.randint(8, 12)
        bursts = []
        
        if self.behavior == "STABLE":
            # HEAVY WORKLOAD FIX: Base is now 30-60 (was 5-15)
            # This forces RR(Q=5) to switch 6-12 times per burst
            base = random.randint(30, 60)
            bursts = [max(1, base + random.randint(-5, 5)) for _ in range(count)]
            
        elif self.behavior == "RAMPING":
            start = random.randint(5, 10)
            bursts = [start + (i * 5) for i in range(count)]
            
        elif self.behavior == "VOLATILE":
            # Mix of very short (interactive) and long (processing)
            bursts = [random.choice([random.randint(2, 5), random.randint(40, 80)]) for _ in range(count)]
            
        return bursts

def generate_smart_workload(n=20):
    data = []
    current_time = 0
    for i in range(n):
        b_type = random.choice(["STABLE", "STABLE", "RAMPING", "VOLATILE"])
        p = Process(f"P{i}", current_time, b_type)
        data.append(p)
        current_time += random.randint(1, 3) 
    return data