#!/bin/bash

# Name of the screen session
SESSION_NAME="fan_controller"

# Path to your Python script
PYTHON_SCRIPT="fan_controller.py"

# Start the screen session and run the Python script
screen -dmS "$SESSION_NAME" python "$PYTHON_SCRIPT"
