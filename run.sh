#!/bin/bash

# Chatshare run script
# Usage: ./run.sh [start|test]

case "$1" in
    start)
        echo "Starting Chatshare application..."
        python3 -m src.chatshare
        ;;
    tests)
        echo "Running tests..."
        python3 -m unittest discover -s tests -p "*.py" -v
        ;;
    lint)
        echo "Running linter..."
        pylint pylint **/*.py
        ;;
    *)
        echo ""
        echo " Madhouse Miners Chatshare v2 "
        echo "Copyright 2025 Madhouse Miners"
        echo ""
        echo "------------------------------"
        echo ""
        echo "Usage: $0 {start|tests|lint}"
        echo "  start - Start the Chatshare application."
        echo "  tests - Run all unit tests."
        echo "  lint  - Run the linter."
        echo ""
        exit 1
        ;;
esac