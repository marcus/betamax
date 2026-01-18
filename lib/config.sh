#!/bin/bash
# betamax/lib/config.sh - Default configuration

# Session defaults
SESSION="betamax"
DELAY_MS=500
DELAY_MS_SET_BY_CLI=false
WAIT_PATTERN=""
TIMEOUT=30
TIMEOUT_SET_BY_CLI=false
KEEP=false
CAPTURE=false
OUTPUT_DIR="./captures"
OUTPUT_DIR_SET_BY_CLI=false
KEYS_FILE=""
TERM_COLS_OVERRIDE=""
TERM_COLS_SET_BY_CLI=false
TERM_ROWS_OVERRIDE=""
TERM_ROWS_SET_BY_CLI=false
SHELL_OVERRIDE=""
SHELL_SET_BY_CLI=false
COMMAND=""
KEYS=()

# Computed at runtime
DELAY_SEC=""
TERM_COLS=""
TERM_LINES=""

# GIF recording state
RECORDING=false
RECORDING_DIR=""
RECORDING_FRAME=0
RECORDING_COLS=""
GIF_FRAME_DELAY_MS=200  # Time each frame displays in GIF (default: 200ms)

# tmux socket name (isolates betamax sessions)
TMUX_SOCKET="betamax"

# Helper to run tmux with our socket
tmux_cmd() {
  tmux -L "$TMUX_SOCKET" "$@"
}

# Compute delay in seconds from milliseconds
compute_delay_sec() {
  DELAY_SEC=$(echo "scale=3; $DELAY_MS / 1000" | bc)
}

# Compute terminal dimensions
compute_terminal_size() {
  TERM_COLS="${TERM_COLS_OVERRIDE:-$(tput cols 2>/dev/null || echo 80)}"
  TERM_LINES="${TERM_ROWS_OVERRIDE:-$(tput lines 2>/dev/null || echo 24)}"
}
