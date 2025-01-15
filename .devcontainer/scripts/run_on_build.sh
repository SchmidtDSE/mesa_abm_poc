#!/bin/bash

# Set the directory path (default to current directory if not specified)
DIR=".devcontainer/scripts/on_build"

# Find all .sh files in the directory and make them executable
find "$DIR" -name "*.sh" -type f -exec chmod +x {} \;

# Loop through and execute each .sh file
for script in "$DIR"/*.sh; do
    if [ -f "$script" ]; then
        echo "=== Executing $script ==="
        bash "$script"
        
        # Check exit status
        if [ $? -eq 0 ]; then
            echo "✓ $script completed successfully"
        else
            echo "❌ $script failed with exit code $?"
        fi
        echo
    fi
done