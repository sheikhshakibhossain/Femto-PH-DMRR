from workload import generate_smart_workload
from algorithms import RoundRobin, FemtoScheduler
import copy

def calculate_metrics(scheduler_obj):
    total_tat = 0
    total_wt = 0
    n = len(scheduler_obj.completed_processes)
    
    for p in scheduler_obj.completed_processes:
        # TAT = Completion - Arrival
        tat = p.completion_time - p.arrival_time
        # WT = TAT - Total_Burst_Time
        total_burst = sum(p.bursts)
        wt = tat - total_burst
        
        total_tat += tat
        total_wt += wt
        
    return {
        "Name": scheduler_obj.name,
        "Avg_TAT": total_tat / n,
        "Avg_WT": total_wt / n
    }

def main():
    print("--- 1. Generating Smart Workload ---")
    # Generate one dataset to be used by ALL algorithms
    dataset = generate_smart_workload(n=20)
    print(f"Generated {len(dataset)} processes with mixed behaviors (Stable, Ramping, Volatile).")

    # Deep copy dataset for each runner so they don't share state
    data_rr1 = copy.deepcopy(dataset)
    data_rr2 = copy.deepcopy(dataset)
    data_femto = copy.deepcopy(dataset)

    print("\n--- 2. Running Simulations ---")
    
    # Run Algorithm 1: RR (Low Quantum)
    rr_low = RoundRobin(data_rr1, quantum=5)
    rr_low.run()
    
    # Run Algorithm 2: RR (High Quantum)
    rr_high = RoundRobin(data_rr2, quantum=15)
    rr_high.run()
    
    # Run Algorithm 3: Femto-Window
    femto = FemtoScheduler(data_femto)
    femto.run()

    print("\n--- 3. Performance Evaluation ---")
    results = [
        calculate_metrics(rr_low),
        calculate_metrics(rr_high),
        calculate_metrics(femto)
    ]
    
    # Print Table
    print(f"{'Algorithm':<25} | {'Avg TAT':<10} | {'Avg WT':<10}")
    print("-" * 55)
    for r in results:
        print(f"{r['Name']:<25} | {r['Avg_TAT']:<10.2f} | {r['Avg_WT']:<10.2f}")
        
    print("\nanalysis: If Femto-Window Avg WT is lower than RR, the dynamic quantum is working!")

if __name__ == "__main__":
    main()