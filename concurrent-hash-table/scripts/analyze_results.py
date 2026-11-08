import os
import re
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import glob


def parse_result_file(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        operations = []
        current_op = {}
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("Actions:"):
                current_op = {"action": line.split(":")[1].strip()}
                i += 1
                while i < len(lines) and lines[i].strip() != "":
                    if lines[i].startswith("ExecutionTime:"):
                        time_match = re.search(r'ExecutionTime:\s*(\d+(?:\.\d+)?)\s*ms', lines[i])
                        current_op["time"] = float(time_match.group(1)) if time_match else 0.0
                    elif lines[i].startswith("NumberOfHandledCollision:"):
                        collision_match = re.search(r'NumberOfHandledCollision:\s*(\d+)', lines[i])
                        current_op["collisions"] = int(collision_match.group(1)) if collision_match else 0
                    elif lines[i].startswith("Data:"):
                        current_op["data"] = lines[i][5:].strip()
                    i += 1
                operations.append(current_op)
            else:
                i += 1
        

        total_time = sum(op["time"] for op in operations)
        total_collisions = sum(op["collisions"] for op in operations)
        
        return total_time, total_collisions
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return 0.0, 0

def parse_filename(filename):
    pattern = r'results_(\d+[Kk]?)_(\d+)_(\d+[Kk]?)_([\w_]+)\.txt'
    match = re.search(pattern, os.path.basename(filename))
    
    if match:
        data_size = match.group(1).upper()  # e.g., '150K'
        threads = int(match.group(2))
        table_size = match.group(3).upper()  # e.g., '300K'
        flow = match.group(4)  # operation flow
        return data_size, threads, table_size, flow
    
    return None, None, None, None

def collect_results():
    results = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    
    results_dir = "results"
    if not os.path.exists(results_dir):
        print(f"Error: {results_dir} directory not found!")
        return results
    
    result_files = glob.glob(os.path.join(results_dir, "Results_*.txt"))
    print(f"Found {len(result_files)} result files")
    
    for filepath in result_files:
        data_size, threads, table_size, flow = parse_filename(filepath)
        
        if data_size and threads is not None and table_size:
            exec_time, collisions = parse_result_file(filepath)
            # Normalize data sizes to consistent format (e.g., 150K -> 150000)
            numeric_data = int(data_size.replace('K', '')) * 1000
            numeric_table = int(table_size.replace('K', '')) * 1000
            
            # Calculate unique data count (1/5 of total data)
            unique_count = numeric_data // 5
            
            # Calculate table multiplier (table_size / unique_count)
            multiplier = numeric_table / unique_count
            
            # Store results by data size and multiplier
            results[numeric_data][multiplier][threads] = (exec_time, collisions)
    
    return results

def generate_charts(results):    
    plot_dir = "plots"
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    
    chart_count = 0
    
    for data_size in sorted(results.keys()):
        data_str = f"{data_size//1000}K"
        
        for multiplier in sorted(results[data_size].keys()):
            multiplier_str = f"{multiplier:.1f}x"
            chart_count += 1
            
            thread_data = results[data_size][multiplier]
            thread_counts = sorted(thread_data.keys())
            exec_times = [thread_data[t][0] for t in thread_counts]
            collision_counts = [thread_data[t][1] for t in thread_counts]
            
            # Create thread labels
            thread_labels = []
            for t in thread_counts:
                if t == 1:
                    thread_labels.append("ST")
                else:
                    thread_labels.append(f"MT({t})")
            
            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            fig.suptitle(f"Performance Analysis: {data_str} Data, Table Size = {multiplier_str} Unique", fontsize=14)
            
            # Execution time bar plot
            bars1 = ax1.bar(range(len(thread_counts)), exec_times, color='steelblue', alpha=0.7, edgecolor='black')
            ax1.set_xlabel('Thread Configuration', fontsize=12)
            ax1.set_ylabel('Execution Time (ms)', fontsize=12)
            ax1.set_title('Execution Time vs Thread Count', fontsize=13)
            ax1.grid(True, linestyle='--', alpha=0.7, axis='y')
            ax1.set_xticks(range(len(thread_counts)))
            ax1.set_xticklabels(thread_labels, rotation=45)
            ax1.tick_params(axis='both', which='major', labelsize=10)
            ax1.set_ylim(0, max(exec_times) * 1.1)  # Start from 0 with 10% headroom
            
            # Find and mark minimum execution time
            min_time = min(exec_times)
            min_idx = exec_times.index(min_time)
            ax1.bar(min_idx, min_time, color='green', alpha=0.8, edgecolor='black')
            ax1.text(min_idx, min_time + max(exec_times) * 0.02, f'MIN\n{min_time:.1f}ms', 
                    ha='center', va='bottom', fontweight='bold', fontsize=9, color='green')
            
            # Collision count bar plot
            bars2 = ax2.bar(range(len(thread_counts)), collision_counts, color='coral', alpha=0.7, edgecolor='black')
            ax2.set_xlabel('Thread Configuration', fontsize=12)
            ax2.set_ylabel('Collision Count', fontsize=12)
            ax2.set_title('Collision Count vs Thread Count', fontsize=13)
            ax2.grid(True, linestyle='--', alpha=0.7, axis='y')
            ax2.set_xticks(range(len(thread_counts)))
            ax2.set_xticklabels(thread_labels, rotation=45)
            ax2.tick_params(axis='both', which='major', labelsize=10)
            ax2.set_ylim(0, max(collision_counts) * 1.1)  # Start from 0 with 10% headroom
            
            # Find and mark minimum collision count
            min_collisions = min(collision_counts)
            min_coll_idx = collision_counts.index(min_collisions)
            ax2.bar(min_coll_idx, min_collisions, color='darkgreen', alpha=0.8, edgecolor='black')
            ax2.text(min_coll_idx, min_collisions + max(collision_counts) * 0.02, f'MIN\n{min_collisions}', 
                    ha='center', va='bottom', fontweight='bold', fontsize=9, color='darkgreen')
            
            # Add value labels on bars
            for i, v in enumerate(exec_times):
                ax1.text(i, v + max(exec_times) * 0.01, f'{v:.1f}', ha='center', va='bottom', fontsize=8)
            
            for i, v in enumerate(collision_counts):
                ax2.text(i, v + max(collision_counts) * 0.01, f'{v}', ha='center', va='bottom', fontsize=8)
            
            plt.tight_layout()
            plt.subplots_adjust(top=0.85)
            
            # Save chart
            chart_filename = os.path.join(plot_dir, f"performance_{data_str}_{multiplier_str.replace('.', '_')}.png")
            plt.savefig(chart_filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Generated chart {chart_count}/9: {chart_filename}")
    
    return chart_count

def analyze_performance(results):
    print("\n" + "="*80)
    print("PERFORMANCE ANALYSIS SUMMARY")
    print("="*80)
    print(f"{'Data Size':<10} {'Table Size':<12} {'Best Threads':<12} {'Time (ms)':<12} {'Speedup':<12} {'Worse than ST':<15} {'Max Collisions':<15}")
    print("-" * 80)
    
    for data_size in sorted(results.keys()):
        data_str = f"{data_size//1000}K"
        
        for multiplier in sorted(results[data_size].keys()):
            multiplier_str = f"{multiplier:.1f}x"
            thread_data = results[data_size][multiplier]
            
            # Find best thread count
            best_threads = 1
            best_time = thread_data[1][0]
            for threads, (time, _) in thread_data.items():
                if time < best_time:
                    best_time = time
                    best_threads = threads
            
            # Calculate speedup
            st_time = thread_data[1][0]
            speedup = st_time / best_time if best_time > 0 else 0
            
            # Find when performance becomes worse than single-thread
            worse_threads = None
            for threads in sorted(thread_data.keys()):
                if threads > 1 and thread_data[threads][0] > st_time:
                    worse_threads = threads
                    break
            
            # Get max collisions
            max_collisions = max(collisions for _, (_, collisions) in thread_data.items())
            
            print(f"{data_str:<10} {multiplier_str:<12} {best_threads:<12} {best_time:<12.2f} {speedup:<12.2f}x {str(worse_threads) if worse_threads else 'Never':<15} {max_collisions:<15}")

def generate_summary_table_plot(results):
    """Generate a PNG plot of the summary table with optimal configurations and worsening thresholds"""
    
    # Collect all data sizes and multipliers
    data_sizes = sorted(results.keys())
    all_multipliers = set()
    for data_size in data_sizes:
        all_multipliers.update(results[data_size].keys())
    multipliers = sorted(all_multipliers)
    
    # Prepare data for the table
    table_data = []
    headers = ['Data Size', 'Table Size', 'Optimal Threads', 'Execution Time (ms)', 'Speedup', 'Worsening Threshold']
    
    for data_size in data_sizes:
        data_str = f"{data_size//1000}K"
        
        for multiplier in multipliers:
            if multiplier in results[data_size]:
                thread_data = results[data_size][multiplier]
                
                # Find optimal thread count (minimum execution time)
                best_threads = 1
                best_time = thread_data[1][0]
                for threads, (time, _) in thread_data.items():
                    if time < best_time:
                        best_time = time
                        best_threads = threads
                
                # Find worsening threshold (when performance becomes worse than single-thread)
                st_time = thread_data[1][0]
                worsening_threshold = None
                for threads in sorted(thread_data.keys()):
                    if threads > 1 and thread_data[threads][0] > st_time:
                        worsening_threshold = threads
                        break
                
                # Calculate speedup
                speedup = st_time / best_time if best_time > 0 else 0
                
                # Format data
                multiplier_str = f"{multiplier:.1f}x"
                optimal_str = "ST" if best_threads == 1 else f"MT({best_threads})"
                time_str = f"{best_time:.1f}"
                speedup_str = f"{speedup:.2f}x"
                threshold_str = f"{worsening_threshold}" if worsening_threshold else "Never"
                
                table_data.append([data_str, multiplier_str, optimal_str, time_str, speedup_str, threshold_str])
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.axis('tight')
    ax.axis('off')
    
    # Create table
    table = ax.table(cellText=table_data, colLabels=headers, cellLoc='center', loc='center')
    
    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 2)
    
    # Header styling
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
        table[(0, i)].set_height(0.08)
    
    # Data row styling
    for i in range(1, len(table_data) + 1):
        for j in range(len(headers)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f0f0f0')
            else:
                table[(i, j)].set_facecolor('white')
            
            # Highlight optimal configurations
            if j == 2:  # Optimal Threads column
                if 'MT' in table_data[i-1][j]:
                    table[(i, j)].set_facecolor('#E8F5E8')
                    table[(i, j)].set_text_props(weight='bold', color='#2E7D32')
            
            # Highlight worsening threshold
            if j == 5:  # Worsening Threshold column
                if table_data[i-1][j] != "Never":
                    table[(i, j)].set_facecolor('#FFEBEE')
                    table[(i, j)].set_text_props(color='#C62828')
                else:
                    table[(i, j)].set_facecolor('#E8F5E8')
                    table[(i, j)].set_text_props(color='#2E7D32')
            
            table[(i, j)].set_height(0.06)
    
    # Add title
    plt.title('Performance Summary: Optimal Thread Configurations and Worsening Thresholds', 
              fontsize=16, fontweight='bold', pad=20)
    
    # Add legend
    legend_text = ("Legend:\n"
                  "• ST = Single Thread\n"
                  "• MT(n) = Multi-Thread with n threads\n"
                  "• Worsening Threshold = Thread count where performance becomes worse than single-thread\n"
                  "• Green highlighting = Optimal performance\n"
                  "• Red highlighting = Performance degradation point")
    
    plt.figtext(0.02, 0.02, legend_text, fontsize=10, verticalalignment='bottom', 
                bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.8))
    
    # Save the plot
    plot_dir = "plots"
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    
    table_filename = os.path.join(plot_dir, "performance_summary_table.png")
    plt.savefig(table_filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Generated summary table plot: {table_filename}")
    
    return table_filename

def generate_configuration_matrix_plot(results):
    """Generate a PNG plot of the configuration matrix showing optimal threads for each combination"""
    
    # Collect all data sizes and multipliers
    data_sizes = sorted(results.keys())
    all_multipliers = set()
    for data_size in data_sizes:
        all_multipliers.update(results[data_size].keys())
    multipliers = sorted(all_multipliers)
    
    # Create matrix data
    matrix_data = []
    row_labels = []
    col_labels = [f"{m:.1f}x" for m in multipliers]
    
    for data_size in data_sizes:
        data_str = f"{data_size//1000}K"
        row_labels.append(data_str)
        row_data = []
        
        for multiplier in multipliers:
            if multiplier in results[data_size]:
                thread_data = results[data_size][multiplier]
                
                # Find optimal thread count
                best_threads = 1
                best_time = thread_data[1][0]
                for threads, (time, _) in thread_data.items():
                    if time < best_time:
                        best_time = time
                        best_threads = threads
                
                if best_threads == 1:
                    cell_text = "ST"
                else:
                    cell_text = f"MT({best_threads})"
                row_data.append(cell_text)
            else:
                row_data.append("N/A")
        
        matrix_data.append(row_data)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('tight')
    ax.axis('off')
    
    # Create table
    table = ax.table(cellText=matrix_data, rowLabels=row_labels, colLabels=col_labels, 
                    cellLoc='center', loc='center')
    
    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.5, 2.5)
    
    # Header styling
    for i in range(len(col_labels)):
        table[(0, i)].set_facecolor('#2196F3')
        table[(0, i)].set_text_props(weight='bold', color='white')
        table[(0, i)].set_height(0.1)
    
    # Row label styling
    for i in range(len(row_labels)):
        table[(i+1, -1)].set_facecolor('#2196F3')
        table[(i+1, -1)].set_text_props(weight='bold', color='white')
    
    # Data cell styling
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            cell_text = matrix_data[i][j]
            if cell_text == "ST":
                table[(i+1, j)].set_facecolor('#FFCDD2')
                table[(i+1, j)].set_text_props(weight='bold', color='#D32F2F')
            elif cell_text.startswith("MT"):
                table[(i+1, j)].set_facecolor('#C8E6C9')
                table[(i+1, j)].set_text_props(weight='bold', color='#388E3C')
            else:
                table[(i+1, j)].set_facecolor('#F5F5F5')
                table[(i+1, j)].set_text_props(color='#757575')
            
            table[(i+1, j)].set_height(0.08)
    
    # Add title
    plt.title('Configuration Matrix: Optimal Thread Count by Data Size and Table Size', 
              fontsize=16, fontweight='bold', pad=20)
    
    # Add legend
    legend_text = ("Legend:\n"
                  "• ST = Single Thread (Red)\n"
                  "• MT(n) = Multi-Thread with n threads (Green)\n"
                  "• Rows = Data Size, Columns = Table Size Multiplier")
    
    plt.figtext(0.02, 0.02, legend_text, fontsize=11, verticalalignment='bottom', 
                bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.8))
    
    # Save the plot
    plot_dir = "plots"
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    
    matrix_filename = os.path.join(plot_dir, "configuration_matrix.png")
    plt.savefig(matrix_filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Generated configuration matrix plot: {matrix_filename}")
    
    return matrix_filename

def main():
    print("Multithreaded Hash Table with Delete Operation - Performance Analysis")
    print("=" * 80)
    
    print("Collecting results from files...")
    results = collect_results()
    
    if not results:
        print("No results found! Make sure to run all tests first.")
        return
    
    print("\nGenerating performance charts...")
    chart_count = generate_charts(results)
    
    if chart_count == 9:
        print(f"✓ Successfully generated all {chart_count} required charts")
    else:
        print(f"⚠ Generated {chart_count}/9 charts (some configurations may be missing)")
    
    analyze_performance(results)
    
    # Generate summary tables as PNG plots
    print("\nGenerating summary table plots...")
    generate_summary_table_plot(results)
    generate_configuration_matrix_plot(results)
    
    print("\n" + "="*80)
    print("Key Performance Insights:")
    print("1. The optimal thread count varies based on data size and table size")
    print("2. Smaller table sizes show more collisions, especially with higher thread counts")
    print("3. Performance typically degrades beyond 64-128 threads due to synchronization overhead")
    print("4. Larger tables reduce collisions but increase memory usage")
    print("="*80)
    
    print("\nAnalysis completed! Check the plots directory for generated charts.")

if __name__ == "__main__":
    main()