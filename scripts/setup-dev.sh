#!/usr/bin/env bash
# ==============================================================================
# LAYA OS - Development Environment Setup
# Prepares Python virtual environment, dependencies, and git hooks.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Setting up LAYA OS Development Environment ==="
cd "${REPO_ROOT}"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Upgrading pip and installing dependencies..."
pip install --upgrade pip
pip install -r requirements-dev.txt

echo "Running test suite..."
pytest

echo "=== LAYA OS Setup Complete! ==="
