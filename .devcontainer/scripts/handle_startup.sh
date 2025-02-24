#!/bin/bash

if [ -z "$IS_DEV_CONTAINER" ]; then
    echo "Running simulation in production mode."

    # Run the simulation task
    source vegetatation/task.sh
fi 

if [ ! -z "$IS_DEV_CONTAINER" ]; then
    echo "Running in dev mode. Press Ctrl+C to exit."

    # Keep container alive, for interactive development
    tail -f /dev/null
fi
