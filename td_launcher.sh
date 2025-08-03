#!/bin/bash
# Mac/Linux launcher script for TD Launcher
# Usage: ./td_launcher.sh [path_to_toe_file]

# Make sure we're in the script directory
cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH"
    echo "Please install Python 3 to run TD Launcher"
    exit 1
fi

# Check if the main script exists
if [ ! -f "td_launcher.py" ]; then
    echo "Error: td_launcher.py not found in $(pwd)"
    exit 1
fi

# Run the launcher with any provided arguments
if [ $# -eq 0 ]; then
    echo "Starting TD Launcher..."
    python3 td_launcher.py
else
    echo "Starting TD Launcher with file: $1"
    python3 td_launcher.py "$1"
fi