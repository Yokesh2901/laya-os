#!/usr/bin/env bash
# ==============================================================================
# LAYA OS - Desktop & AI Core Runner
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"

echo "Starting LAYA OS System Core (D-Bus)..."
python3 -m system.dbus.service &
SYSTEM_PID=$!

echo "Starting LAYA AI Core Daemon..."
python3 -m laya.main &
AI_PID=$!

echo "Starting LAYA Desktop Shell..."
python3 -m desktop.shell.main &
DESKTOP_PID=$!

trap "kill $SYSTEM_PID $AI_PID $DESKTOP_PID 2>/dev/null || true" EXIT

wait
