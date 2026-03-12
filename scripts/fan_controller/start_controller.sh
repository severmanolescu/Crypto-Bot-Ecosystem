#!/bin/bash

# Name of the screen session
SESSION_NAME="fan_controller"

# Path to your Python script
PYTHON_SCRIPT="fan_controller.py"

# Full path to venv Python
VENV_PYTHON="venv/bin/python"

# Start the screen session and run the Python script
export TERM=xterm

echo "Starting fan controller..."
screen -dmS "$SESSION_NAME" "$VENV_PYTHON" "$PYTHON_SCRIPT"

if [ $? -eq 0 ]; then
    echo "Screen session started successfully"
else
    echo "Failed to start screen session"
fi
