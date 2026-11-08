#!/bin/bash

# Test runner script for all 99 configurations
# Updated for HW2 with delete functionality

EXECUTABLE="bin/concurrent_hash_table"

if [ ! -f "$EXECUTABLE" ]; then
    echo "Error: Executable $EXECUTABLE not found!"
    echo "Please run 'make' first to build the program."
    exit 1
fi

mkdir -p results

# Base data sizes (150K, 300K, 600K)
DATA_SIZES=("150K" "300K" "600K")

# Thread counts (2^0 to 2^10)
THREAD_COUNTS=(1 2 4 8 16 32 64 128 256 512 1024)

# Table size multipliers (3x, 4x, 5x of unique data count)
TABLE_MULTIPLIERS=(3 4 5)

# Colors for output 
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "Running All Test Configurations for HW2"
echo "=========================================="
echo "Total configurations: $(( ${#DATA_SIZES[@]} * ${#THREAD_COUNTS[@]} * ${#TABLE_MULTIPLIERS[@]} ))"
echo ""

count=0
total=$(( ${#DATA_SIZES[@]} * ${#THREAD_COUNTS[@]} * ${#TABLE_MULTIPLIERS[@]} ))

for data_size in "${DATA_SIZES[@]}"; do
    # Set input files based on data size
    input_file1="inputs/${data_size}_set1.txt"
    input_file2="inputs/${data_size}_set2.txt"
    
    if [ ! -f "$input_file1" ] || [ ! -f "$input_file2" ]; then
        echo -e "${RED}Error: Input files missing for $data_size${NC}"
        continue
    fi

    # Get numeric value of data size
    base_value=$(echo "$data_size" | sed 's/K//')
    base_value=$((base_value * 1000))  # Convert to absolute count (150K -> 150000)
    base_unique=$((base_value / 5))    # Unique count = total/5

    for threads in "${THREAD_COUNTS[@]}"; do
        for multiplier in "${TABLE_MULTIPLIERS[@]}"; do
            count=$((count + 1))
            
            # Calculate table size
            table_size=$((base_unique * multiplier))
            table_size_k=$((table_size / 1000))
            table_size_str="${table_size_k}K"
            
            # Progress indicator
            progress=$((count * 100 / total))
            printf "${YELLOW}[%3d/99] (%2d%%) ${NC}" $count $progress
            
            # Define flow and input files
            FLOW=("insert" "insert" "delete" "insert")
            INPUT_FILES=("$input_file1" "$input_file2" "$input_file1" "$input_file2")
            
            # Build flow string for display
            flow_str=$(IFS=_; echo "${FLOW[*]}")
            
            echo -n "Testing: data=$data_size, threads=$threads, table=${table_size_str} (${multiplier}x unique), flow=$flow_str... "
            
            # Execute command
            if "$EXECUTABLE" \
                --data_size "$data_size" \
                --threads "$threads" \
                --tsize "$table_size_str" \
                --flow "${FLOW[@]}" \
                --input "${INPUT_FILES[@]}" > /dev/null 2>&1; then
                echo -e "${GREEN}PASSED${NC}"
            else
                echo -e "${RED}FAILED${NC}"
                echo "  Command: $EXECUTABLE --data_size $data_size --threads $threads --tsize $table_size_str --flow ${FLOW[@]} --input ${INPUT_FILES[@]}"
            fi
            
            # Small delay to avoid overwhelming the system
            sleep 0.1
        done
    done
done

echo ""
echo "=========================================="
echo "Test Execution Summary"
echo "=========================================="

# Count the result files
result_count=$(ls results/results_*.txt 2>/dev/null | wc -l)
echo "Result files generated: $result_count/99"

if [ $result_count -eq 99 ]; then
    echo -e "${GREEN}✓ All tests completed successfully!${NC}"
else
    echo -e "${RED}✗ Some tests may have failed. Check the output above.${NC}"
    echo "Missing $((99 - result_count)) result files"
fi

echo ""
echo "Next steps:"
echo "1. Check results/ directory for output files"
echo "2. Run analysis scripts:"
echo "   $ python3 scripts/analyze_results.py"
echo "3. Generate performance charts from the results"
echo "4. Prepare final report"
echo ""
echo "Results are saved in: results/"
ls -lh results/ | head -10