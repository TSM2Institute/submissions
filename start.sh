#!/bin/bash
while true; do
    echo "Starting Python server..." >&2
    python -u server.py
    EXIT_CODE=$?
    echo "Server exited with code $EXIT_CODE, restarting in 1 second..." >&2
    sleep 1
done
