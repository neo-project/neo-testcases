#!/bin/bash
# Run tests in the tests directory

echo "$(date) - Running tests..."
groups=(
    "basics"
    "crypto"
    "fee"
    "governance"
    "policy"
    "stdlib"
    "plugins/rpcserver"
)

selected_groups=${groups[@]}
skip_initial=false
while [[ $# -gt 0 ]]; do
  case $1 in
    --groups)
      selected_groups=($2)
      shift 2
      ;;
    --skip-initial)
      skip_initial=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--groups group1,group2,...] [--skip-initial]"
      exit 1
      ;;
  esac
done

# validate selected groups
for group in ${selected_groups[@]}; do
    if [[ ! " ${groups[@]} " =~ " ${group} " ]]; then
        echo "$(date) - Invalid group: $group"
        exit 1
    fi
done

failures=()
if [ "$skip_initial" = false ]; then
    echo "$(date) - Running initial tests..."
    python3 -B -m testcases.initial
    if [ $? -ne 0 ]; then
        echo "$(date) - Failed to run initial tests"
        failures+=("initial")
    else
        echo "$(date) - Passed initial tests"
    fi
fi

for group in ${selected_groups[@]}; do
    echo "$(date) - Running $group tests..."
    for file in testcases/$group/*.py; do
        basename=$(basename $file .py) # remove the .py extension
        echo "$(date) - Run $basename test..."

        module=$(echo $group | sed 's/\//./g') # replace '/' with '.' in the group name
        python3 -B -m testcases.$module.$basename
        if [ $? -ne 0 ]; then
            echo "$(date) - Failed to run $basename test"
            failures+=("$group/$basename")
        else
            echo "$(date) - Passed $basename test"
        fi
    done
    echo "$(date) - $group tests completed"
done

echo "$(date) - Tests completed"
if [ ${#failures[@]} -gt 0 ]; then
    echo "$(date) - Failed tests: ${failures[@]}"
    exit 1
else
    echo "$(date) - All tests passed"
    exit 0
fi