#!/bin/bash
# Script to manage python virtual environment
# - If .venv exists: Freezes requirements to requirements.txt
# - If .venv missing: Creates .venv and installs from requirements.txt

# Ensure we are in the script's directory
cd "$(dirname "$0")"

VENV_NAME=".venv"
REQ_FILE="requirements.txt"

if [ ! -d "$VENV_NAME" ]; then
    echo "Virtual environment '$VENV_NAME' not found."
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_NAME"
    
    # Check if creation succeeded
    if [ ! -d "$VENV_NAME" ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi

    # Activate and install
    source "$VENV_NAME/bin/activate"
    
    # Upgrade pip just in case
    pip install --upgrade pip

    if [ -f "$REQ_FILE" ]; then
        echo "Installing requirements from $REQ_FILE..."
        pip install -r "$REQ_FILE"
        echo "Setup complete. Activate with: source $VENV_NAME/bin/activate"
    else
        echo "No $REQ_FILE found. Empty virtual environment created."
        echo "Activate with: source $VENV_NAME/bin/activate"
    fi
else
    echo "Virtual environment '$VENV_NAME' found."
    echo "Freezing installed packages to $REQ_FILE..."
    
    # Activate and freeze
    source "$VENV_NAME/bin/activate"
    pip freeze > "$REQ_FILE"
    
    if [ $? -eq 0 ]; then
        echo "Done. $REQ_FILE updated."
    else
        echo "Error: Failed to freeze requirements."
    fi
fi
