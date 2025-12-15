import random

class Process:
    def __init__(self, pid, arrival_time, behavior):
        self.pid = pid
        self.arrival_time = arrival_time
        self.behavior = behavior
        self.bursts = self._generate_bursts()
        self.priority = random.randint(1, 5)
        
        # State variables for execution
        self.current_burst_index = 0
        self.remaining_time = 0 if not self.bursts else self.bursts[0]
        self.start_time = -1
        self.finish_time = 0
        self.completion_time = 0
        
        # Femto-Window Context (The "History")
        self.burst_history = [] 
        self.predicted_next = 0
        self.is_volatile = False

    def _generate_bursts(self):
        # Generates a sequence of CPU bursts based on behavior profile
        count = random.randint(8, 12)
        bursts = []
        
        if self.behavior == "STABLE":
            base = random.randint(5, 15)
            # Low variance (±1)
            bursts = [max(1, base + random.randint(-1, 1)) for _ in range(count)]
            
        elif self.behavior == "RAMPING":
            start = random.randint(2, 6)
            # Linear increase
            bursts = [start + (i * 2) for i in range(count)]
            
        elif self.behavior == "VOLATILE":
            # Wild swings
            bursts = [random.choice([random.randint(2, 5), random.randint(20, 30)]) for _ in range(count)]
            
        return bursts

def generate_smart_workload(n=15):
    data = []
    current_time = 0
    for i in range(n):
        b_type = random.choice(["STABLE", "STABLE", "RAMPING", "VOLATILE"])
        p = Process(f"P{i}", current_time, b_type)
        data.append(p)
        current_time += random.randint(1, 4) # Arrival gap
    return data