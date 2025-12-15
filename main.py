import matplotlib.pyplot as plt
import copy
import numpy as np
import os
import csv
from workload import generate_smart_workload
from algorithms import FCFS, SJF, SRTF, RoundRobin, PriorityRR, FemtoScheduler

# Ensure results directory exists
OUTPUT_DIR = "results"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def calculate_metrics(scheduler_obj):
    completed = scheduler_obj.completed_processes
    n = len(completed)
    
    total_tat = 0
    total_wt = 0
    total_rt = 0
    total_burst_time = 0
    max_completion_time = 0
    
    for p in completed:
        tat = p.completion_time - p.arrival_time
        proc_total_burst = sum(p.bursts)
        wt = tat - proc_total_burst
        rt = p.start_time - p.arrival_time
        
        total_tat += tat
        total_wt += wt
        total_rt += rt
        total_burst_time += proc_total_burst
        
        if p.completion_time > max_completion_time:
            max_completion_time = p.completion_time

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

def save_to_csv(results, process_count):
    filename = os.path.join(OUTPUT_DIR, f"metrics_{process_count}_processes.csv")
    keys = results[0].keys()
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    print(f"   [Saved CSV]: {filename}")

def plot_dashboard(results, process_count):
    names = [r['Name'] for r in results]
    avg_tat = [r['Avg_TAT'] for r in results]
    avg_wt = [r['Avg_WT'] for r in results]
    avg_rt = [r['Avg_RT'] for r in results]
    throughput = [r['Throughput'] * 100 for r in results] 
    utilization = [r['CPU_Util'] for r in results]
    ctx = [r['Ctx_Switch'] for r in results]

    fig, axs = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(f'Performance Analysis: {process_count} Processes (Heavy Burst)', fontsize=16)
    x = np.arange(len(names))
    width = 0.25

    # Plot 1: Time Metrics
    ax1 = axs[0, 0]
    ax1.bar(x - width, avg_tat, width, label='Turnaround Time')
    ax1.bar(x, avg_wt, width, label='Waiting Time')
    ax1.bar(x + width, avg_rt, width, label='Response Time')
    ax1.set_ylabel('Time (Ticks)')
    ax1.set_title('Time Efficiency (Lower is Better)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=20, ha="right", fontsize=8)
    ax1.legend()
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    # Plot 2: CPU Utilization
    ax2 = axs[0, 1]
    colors = plt.cm.viridis(np.linspace(0, 1, len(names)))
    bars2 = ax2.bar(names, utilization, color=colors)
    ax2.set_ylabel('Utilization (%)')
    ax2.set_title('CPU Utilization (Higher is Better)')
    ax2.set_ylim(0, 105)
    ax2.set_xticks(x)
    ax2.set_xticklabels(names, rotation=20, ha="right", fontsize=8)
    ax2.bar_label(bars2, fmt='%.1f%%')

    # Plot 3: Context Switches
    ax3 = axs[1, 0]
    bars3 = ax3.bar(names, ctx, color='salmon')
    ax3.set_ylabel('Count')
    ax3.set_title('Context Switches (Efficiency Metric)')
    ax3.set_xticks(x)
    ax3.set_xticklabels(names, rotation=20, ha="right", fontsize=8)
    ax3.bar_label(bars3, fmt='%.0f')

    # Plot 4: Throughput
    ax4 = axs[1, 1]
    bars4 = ax4.bar(names, throughput, color='teal')
    ax4.set_ylabel('Procs per 100 Ticks')
    ax4.set_title('Throughput')
    ax4.set_xticks(x)
    ax4.set_xticklabels(names, rotation=20, ha="right", fontsize=8)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save instead of show
    save_path = os.path.join(OUTPUT_DIR, f"dashboard_{process_count}_procs.png")
    plt.savefig(save_path)
    print(f"   [Saved Plot]: {save_path}")
    plt.close() # Close figure to free memory

def plot_scalability_analysis(history, process_counts):
    print("\n--- 5. Generating Scalability Analysis Charts ---")
    
    # We want 4 charts: Switches, Response, Wait, Turnaround
    metrics_to_plot = [
        ('Ctx_Switch', 'Context Switches (Efficiency)', 'Count'),
        ('Avg_RT', 'Avg Response Time (Responsiveness)', 'Ticks'),
        ('Avg_WT', 'Avg Waiting Time', 'Ticks'),
        ('Avg_TAT', 'Avg Turnaround Time', 'Ticks')
    ]
    
    for metric_key, title, ylabel in metrics_to_plot:
        plt.figure(figsize=(10, 6))
        
        # Iterate over each algorithm
        for algo_name, metrics in history.items():
            # Extract the specific metric data for this algo across all process counts
            y_values = [m[metric_key] for m in metrics]
            
            # Style Femto distinctively
            if "Femto" in algo_name:
                plt.plot(process_counts, y_values, marker='o', linewidth=3, label=algo_name, color='red')
            else:
                plt.plot(process_counts, y_values, marker='x', linestyle='--', label=algo_name, alpha=0.7)
        
        plt.xlabel('Number of Processes (Load)')
        plt.ylabel(ylabel)
        plt.title(f'Scalability Analysis: {title}')
        plt.legend()
        plt.grid(True)
        
        save_path = os.path.join(OUTPUT_DIR, f"scalability_{metric_key}.png")
        plt.savefig(save_path)
        print(f"   [Saved Scalability Chart]: {save_path}")
        plt.close()

def main():
    # Global history storage for final comparisons
    # Structure: { "AlgoName": [ {result_dict_10}, {result_dict_20}, ... ] }
    global_history = {}
    
    process_count_list = [10, 20, 50, 100, 200, 400]
    
    for process_count in process_count_list:
        print(f"\n--- Processing Load: {process_count} Processes ---")
        dataset = generate_smart_workload(n=process_count) 
        
        schedulers = [
            FCFS(copy.deepcopy(dataset)),
            SJF(copy.deepcopy(dataset)),
            SRTF(copy.deepcopy(dataset)),
            PriorityRR(copy.deepcopy(dataset), quantum=4),
            RoundRobin(copy.deepcopy(dataset), quantum=5),
            RoundRobin(copy.deepcopy(dataset), quantum=20),
            FemtoScheduler(copy.deepcopy(dataset))
        ]

        # Run this iteration
        results = []
        for sched in schedulers:
            sched.run()
            res = calculate_metrics(sched)
            results.append(res)
            
            # Store for global history
            if res['Name'] not in global_history:
                global_history[res['Name']] = []
            global_history[res['Name']].append(res)

        # Save Iteration Data
        save_to_csv(results, process_count)
        plot_dashboard(results, process_count)
        
        # Console Summary for this iteration
        print(f"   > Best Wait Time: {min(results, key=lambda x: x['Avg_WT'])['Name']}")
        print(f"   > Fewest Switches: {min(results, key=lambda x: x['Ctx_Switch'])['Name']}")

    # --- Final Cross-Comparison Visualization ---
    plot_scalability_analysis(global_history, process_count_list)
    print(f"\n[DONE] All results saved in directory: '{OUTPUT_DIR}/'")

if __name__ == "__main__":
    main()