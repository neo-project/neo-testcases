#!/bin/bash
# Run tests in the tests directory

echo "$(date) - Running tests..."

groups=(
    "basics"
)

for group in ${groups[@]}; do
    echo "$(date) - Running $group tests..."
    for file in testcases/$group/*.py; do
        basename=$(basename $file .py) # remove the .py extension
        echo "$(date) - Run $basename test..."

        python3 -B -m testcases.$group.$basename
        if [ $? -ne 0 ]; then
            echo "$(date) - Failed to run $basename test"
        else
            echo "$(date) - Passed $basename test"
        fi
    done
    echo "$(date) - $group tests completed"
done

echo "$(date) - Tests completed"