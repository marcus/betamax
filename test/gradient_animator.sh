#!/bin/bash
# gradient_animator.sh - Display gradient logo animation frames
# Waits for Enter key between frames to allow betamax to capture

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Hide cursor
printf '\e[?25l'

# Trap to restore cursor on exit
trap 'printf "\e[?25h"' EXIT

# Display each phase (0-23 for full smooth rainbow cycle)
for phase in {0..23}; do
  clear
  "$SCRIPT_DIR/gradient_logo.sh" "$phase"
  read -r  # Wait for Enter from betamax
done
