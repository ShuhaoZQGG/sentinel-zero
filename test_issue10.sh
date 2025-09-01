#!/bin/bash
# Test Issue #10 - long string arguments

echo "Test 1: Command with full arguments in -c option"
sentinel-zero start \
    -n "orchestrate-project" \
    -c './orchestrate.sh "start a new project sentinel-zero, A macOS service that starts, monitors, schedules, and automatically restarts command-line processes with configurable retry policies. Check the detailed vision in README.md file"' \
    -d "/Users/shuhaozhang/Project/sentinel-zero" \
    --restart-policy standard

echo ""
echo "Test 2: Command with --args option"
sentinel-zero start \
    -n "orchestrate-project2" \
    -c "./orchestrate.sh" \
    --args "start a new project sentinel-zero, A macOS service that starts, monitors, schedules, and automatically restarts command-line processes with configurable retry policies. Check the detailed vision in README.md file" \
    -d "/Users/shuhaozhang/Project/sentinel-zero"
