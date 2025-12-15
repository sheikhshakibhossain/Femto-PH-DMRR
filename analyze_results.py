import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os

# Configuration
RESULT_DIR = "results"
OUTPUT_REPORT = "final_analysis_report.txt"

def load_data():
    """Reads all CSV files from the results directory and combines them."""
    all_files = glob.glob(os.path.join(RESULT_DIR, "metrics_*_processes.csv"))
    
    if not all_files:
        print("Error: No CSV files found in 'results/'. Run main.py first.")
        return None

    df_list = []
    for filename in all_files:
        try:
            # Extract process count from filename (e.g., 'metrics_400_processes.csv')
            # Assuming format: metrics_{NUMBER}_processes.csv
            base = os.path.basename(filename)
            proc_count = int(base.split('_')[1])
            
            df = pd.read_csv(filename)
            df['Load'] = proc_count
            df_list.append(df)
        except Exception as e:
            print(f"Skipping {filename}: {e}")

    if not df_list:
        return None

    combined_df = pd.concat(df_list, ignore_index=True)
    return combined_df.sort_values(by=['Load', 'Name'])

def generate_text_report(df):
    """Generates a textual analysis of Femto vs Standards."""
    
    # Get the Maximum Load scenarios (e.g., 400 processes)
    max_load = df['Load'].max()
    subset = df[df['Load'] == max_load]
    
    # Identify Algorithms (Adjust strings to match your main.py names)
    try:
        femto = subset[subset['Name'].str.contains("Femto")].iloc[0]
        rr5 = subset[subset['Name'].str.contains("Q=5")].iloc[0]
        rr20 = subset[subset['Name'].str.contains("Q=20")].iloc[0]
        srtf = subset[subset['Name'].str.contains("SRTF")].iloc[0]
    except IndexError:
        print("Could not find required algorithms for comparison.")
        return

    # --- Calculation Logic ---
    # 1. Efficiency Gain (Context Switches vs RR-5)
    switch_reduction = ((rr5['Ctx_Switch'] - femto['Ctx_Switch']) / rr5['Ctx_Switch']) * 100
    
    # 2. Responsiveness Gain (Response Time vs RR-20)
    resp_gain = ((rr20['Avg_RT'] - femto['Avg_RT']) / rr20['Avg_RT']) * 100
    
    # 3. Optimality Gap (Wait Time vs SRTF - The Theoretical Ideal)
    # How far is Femto from the perfect SRTF?
    optimality_gap = ((femto['Avg_WT'] - srtf['Avg_WT']) / srtf['Avg_WT']) * 100

    report = f"""
==========================================================
FEMTO-WINDOW SCHEDULER: FINAL PERFORMANCE ANALYSIS REPORT
==========================================================
Dataset Analysis: {df['Load'].nunique()} Simulation Runs (10 to {max_load} Processes)
Analysis Baseline: Maximum System Load ({max_load} Processes)

1. EFFICIENCY ANALYSIS (Overhead Reduction)
   vs Round Robin (Q=5):
   - RR(Q=5) Context Switches: {int(rr5['Ctx_Switch'])}
   - Femto Context Switches:   {int(femto['Ctx_Switch'])}
   -------------------------------------------------------
   >>> RESULT: Femto reduced system overhead by {switch_reduction:.2f}%
   
2. RESPONSIVENESS ANALYSIS (User Experience)
   vs Round Robin (Q=20):
   - RR(Q=20) Avg Response:    {rr20['Avg_RT']:.1f} ticks
   - Femto Avg Response:       {femto['Avg_RT']:.1f} ticks
   -------------------------------------------------------
   >>> RESULT: Femto is {resp_gain:.2f}% faster to respond than RR(20).

3. THEORETICAL OPTIMALITY
   vs SRTF (Preemptive Shortest Job First - "God Mode"):
   - SRTF Avg Wait Time:       {srtf['Avg_WT']:.1f} ticks
   - Femto Avg Wait Time:      {femto['Avg_WT']:.1f} ticks
   -------------------------------------------------------
   >>> RESULT: Femto is within {optimality_gap:.2f}% of the theoretical limit
               without knowing burst times in advance.

4. SCALABILITY CONCLUSION
   Under heavy load, Femto-Window successfully identifies 'Stable' 
   processes and scales the Time Quantum, avoiding the thrashing 
   seen in RR(Q=5) while maintaining the interactivity missing 
   in RR(Q=20).
==========================================================
"""
    print(report)
    with open(OUTPUT_REPORT, "w") as f:
        f.write(report)
    print(f"[Report Saved]: {OUTPUT_REPORT}")

def plot_comparative_gains(df):
    """Plots a bar chart showing % Improvement of Femto over others."""
    max_load = df['Load'].max()
    subset = df[df['Load'] == max_load]
    
    femto = subset[subset['Name'].str.contains("Femto")].iloc[0]
    rr5 = subset[subset['Name'].str.contains("Q=5")].iloc[0]
    rr20 = subset[subset['Name'].str.contains("Q=20")].iloc[0]
    
    # Data for plotting
    metrics = ['Context Switches', 'Response Time']
    # How much LOWER is Femto?
    switch_imp = ((rr5['Ctx_Switch'] - femto['Ctx_Switch']) / rr5['Ctx_Switch']) * 100
    resp_imp = ((rr20['Avg_RT'] - femto['Avg_RT']) / rr20['Avg_RT']) * 100
    
    values = [switch_imp, resp_imp]
    baseline_names = ['vs RR(Q=5)', 'vs RR(Q=20)']
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(metrics, values, color=['#2ecc71', '#3498db'], width=0.5)
    
    plt.title(f"Femto-Window Improvements at Peak Load ({max_load} Processes)", fontsize=14)
    plt.ylabel("% Improvement (Higher is Better)")
    plt.ylim(0, 100)
    
    # Add text labels
    for bar, base_name in zip(bars, baseline_names):
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 2, f"{yval:.1f}%", ha='center', fontweight='bold')
        plt.text(bar.get_x() + bar.get_width()/2, yval / 2, base_name, ha='center', color='white', fontweight='bold')

    plt.grid(axis='y', linestyle='--', alpha=0.5)
    
    save_path = os.path.join(RESULT_DIR, "final_improvement_chart.png")
    plt.savefig(save_path)
    print(f"[Chart Saved]: {save_path}")
    plt.show()

def plot_heatmap(df):
    """Optional: Heatmap of Wait Time vs Load for all Algos"""
    pivot_table = df.pivot(index='Name', columns='Load', values='Avg_WT')
    
    plt.figure(figsize=(12, 8))
    sns.heatmap(pivot_table, annot=True, fmt=".0f", cmap="YlOrRd", linewidths=.5)
    plt.title("Heatmap: Average Waiting Time vs System Load")
    plt.ylabel("Scheduling Algorithm")
    plt.xlabel("Number of Processes")
    
    save_path = os.path.join(RESULT_DIR, "wait_time_heatmap.png")
    plt.savefig(save_path)
    print(f"[Chart Saved]: {save_path}")

if __name__ == "__main__":
    data = load_data()
    if data is not None:
        generate_text_report(data)
        plot_comparative_gains(data)
        # Check if seaborn is installed for heatmap, else skip
        try:
            plot_heatmap(data)
        except NameError:
            print("Skipping heatmap (Seaborn not found)")