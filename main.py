import matplotlib.pyplot as plt
import copy
import numpy as np
from workload import generate_smart_workload
from algorithms import FCFS, SJF, SRTF, RoundRobin, PriorityRR, FemtoScheduler

def calculate_metrics(scheduler_obj):
    completed = scheduler_obj.completed_processes
    n = len(completed)
    
    total_tat = 0
    total_wt = 0
    total_rt = 0
    total_burst_time = 0
    max_completion_time = 0
    
    for p in completed:
        # Turnaround Time = Completion - Arrival
        tat = p.completion_time - p.arrival_time
        
        # Total Burst
        proc_total_burst = sum(p.bursts)
        
        # Waiting Time = Turnaround - Total CPU Burst
        wt = tat - proc_total_burst
        
        # Response Time = First Start Time - Arrival Time
        rt = p.start_time - p.arrival_time
        
        total_tat += tat
        total_wt += wt
        total_rt += rt
        total_burst_time += proc_total_burst
        
        if p.completion_time > max_completion_time:
            max_completion_time = p.completion_time

    # Avoid division by zero
    if n == 0: return {}

    avg_tat = total_tat / n
    avg_wt = total_wt / n
    avg_rt = total_rt / n
    throughput = n / max_completion_time if max_completion_time > 0 else 0
    utilization = (total_burst_time / max_completion_time) * 100 if max_completion_time > 0 else 0

    return {
        "Name": scheduler_obj.name,
        "Avg_TAT": avg_tat,
        "Avg_WT": avg_wt,
        "Avg_RT": avg_rt,
        "Throughput": throughput,
        "CPU_Util": utilization,
        "Ctx_Switch": scheduler_obj.context_switches
    }

def plot_dashboard(results):
    names = [r['Name'] for r in results]
    avg_tat = [r['Avg_TAT'] for r in results]
    avg_wt = [r['Avg_WT'] for r in results]
    avg_rt = [r['Avg_RT'] for r in results]
    # Scale Throughput for visibility
    throughput = [r['Throughput'] * 100 for r in results] 
    utilization = [r['CPU_Util'] for r in results]

    # Create a dashboard with 2 rows and 2 columns
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Femto-Window vs Standards: Comprehensive Analysis', fontsize=16)

    x = np.arange(len(names))
    width = 0.25

    # --- PLOT 1: Time Metrics (Grouped Bar) ---
    ax1 = axs[0, 0]
    rects1 = ax1.bar(x - width, avg_tat, width, label='Turnaround Time')
    rects2 = ax1.bar(x, avg_wt, width, label='Waiting Time')
    rects3 = ax1.bar(x + width, avg_rt, width, label='Response Time')
    
    ax1.set_ylabel('Time (Ticks)')
    ax1.set_title('Time Efficiency (Lower is Better)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
    ax1.legend()
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    # --- PLOT 2: CPU Utilization ---
    ax2 = axs[0, 1]
    colors = plt.cm.viridis(np.linspace(0, 1, len(names)))
    bars2 = ax2.bar(names, utilization, color=colors)
    ax2.set_ylabel('Utilization (%)')
    ax2.set_title('CPU Utilization (Higher is Better)')
    ax2.set_ylim(0, 105)
    ax2.set_xticks(x)
    ax2.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
    ax2.bar_label(bars2, fmt='%.1f%%')

    # --- PLOT 3: Throughput ---
    ax3 = axs[1, 0]
    bars3 = ax3.bar(names, throughput, color='teal')
    ax3.set_ylabel('Processes per 100 Ticks')
    ax3.set_title('Throughput')
    ax3.set_xticks(x)
    ax3.set_xticklabels(names, rotation=20, ha="right", fontsize=9)

    # --- PLOT 4: Context Switches (The "Efficiency" Metric) ---
    ax4 = axs[1, 1]
    ctx = [r['Ctx_Switch'] for r in results]
    bars4 = ax4.bar(names, ctx, color='salmon')
    ax4.set_ylabel('Count')
    ax4.set_title('Context Switches (Lower overhead is Better)')
    ax4.set_xticks(x)
    ax4.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
    ax4.bar_label(bars4, fmt='%.0f')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

def main():

    process_count_list = [10, 20, 50, 100, 200, 400]
    for process_count in process_count_list:

        print("--- 1. Generating Smart Workload (HEAVY) ---")
        # Using 20 for quick test, change to 400 for full stress test
        dataset = generate_smart_workload(n=process_count) 
        print(f"Generated {len(dataset)} processes with heavy bursts (30-60 ticks).")

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

        # --- 3. CONSOLE OUTPUT (ALL METRICS) ---
        print("\n--- 3. Numerical Results (Console) ---")
        
        # Headers aligned for readability
        headers = ["Algorithm", "TAT", "Wait", "Resp", "Switches", "Throughput*", "Util %"]
        print(f"{headers[0]:<25} | {headers[1]:<8} | {headers[2]:<8} | {headers[3]:<8} | {headers[4]:<8} | {headers[5]:<12} | {headers[6]:<8}")
        print("-" * 95)
        
        for r in metrics_list:
            tp_scaled = r['Throughput'] * 100
            print(f"{r['Name']:<25} | {r['Avg_TAT']:<8.0f} | {r['Avg_WT']:<8.0f} | {r['Avg_RT']:<8.0f} | {r['Ctx_Switch']:<8} | {tp_scaled:<12.2f} | {r['CPU_Util']:<8.1f}")
        
        print(f"\n*Throughput is measured in Processes per 100 Ticks")

        print("\n--- 4. Visualizing Results ---")
        plot_dashboard(metrics_list)


if __name__ == "__main__":
    main()