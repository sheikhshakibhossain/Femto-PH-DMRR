import matplotlib.pyplot as plt
import copy
from workload import generate_smart_workload
from algorithms import FCFS, SJF, SRTF, RoundRobin, PriorityRR, FemtoScheduler

def calculate_metrics(scheduler_obj):
    total_tat = 0
    total_wt = 0
    total_context_switches = 0 # Not implemented in sim, but useful
    n = len(scheduler_obj.completed_processes)
    
    for p in scheduler_obj.completed_processes:
        tat = p.completion_time - p.arrival_time
        total_burst = sum(p.bursts)
        wt = tat - total_burst
        total_tat += tat
        total_wt += wt
        
    return {
        "Name": scheduler_obj.name,
        "Avg_TAT": total_tat / n,
        "Avg_WT": total_wt / n
    }

def plot_results(results):
    names = [r['Name'] for r in results]
    avg_wt = [r['Avg_WT'] for r in results]
    avg_tat = [r['Avg_TAT'] for r in results]

    x = range(len(names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    rects1 = ax.bar([i - width/2 for i in x], avg_wt, width, label='Avg Waiting Time')
    rects2 = ax.bar([i + width/2 for i in x], avg_tat, width, label='Avg Turnaround Time')

    ax.set_ylabel('Time (Ticks)')
    ax.set_title('Scheduler Performance Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15)
    ax.legend()
    
    # Add counts above bars
    ax.bar_label(rects1, padding=3, fmt='%.1f')
    ax.bar_label(rects2, padding=3, fmt='%.1f')

    plt.tight_layout()
    plt.show()

def main():
    print("--- 1. Generating Smart Workload ---")
    dataset = generate_smart_workload(n=15)
    print(f"Generated {len(dataset)} processes.")

    # Create deep copies for fairness
    schedulers = [
        FCFS(copy.deepcopy(dataset)),
        SJF(copy.deepcopy(dataset)),
        SRTF(copy.deepcopy(dataset)),
        PriorityRR(copy.deepcopy(dataset), quantum=4),
        RoundRobin(copy.deepcopy(dataset), quantum=5),
        RoundRobin(copy.deepcopy(dataset), quantum=20),
        FemtoScheduler(copy.deepcopy(dataset))
    ]

    print("\n--- 2. Running Simulations ---")
    metrics_list = []
    for sched in schedulers:
        print(f"Running {sched.name}...")
        sched.run()
        metrics_list.append(calculate_metrics(sched))

    print("\n--- 3. Tabular Results ---")
    print(f"{'Algorithm':<25} | {'Avg TAT':<10} | {'Avg WT':<10}")
    print("-" * 55)
    for r in metrics_list:
        print(f"{r['Name']:<25} | {r['Avg_TAT']:<10.2f} | {r['Avg_WT']:<10.2f}")

    print("\n--- 4. Plotting Graph ---")
    plot_results(metrics_list)

if __name__ == "__main__":
    main()