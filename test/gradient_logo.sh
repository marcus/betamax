#!/bin/bash
# gradient_logo.sh - Output betamax logo with animated rainbow gradient wave
#
# Usage: ./gradient_logo.sh [phase]
#   phase: 0-23 (wave offset), default 0

PHASE=${1:-0}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGO_FILE="${SCRIPT_DIR}/../betamax.txt"

# Rainbow colors using 256-color mode (smooth gradient)
# These cycle through: red -> orange -> yellow -> green -> cyan -> blue -> magenta -> red
COLORS=(
  196 202 208 214 220 226
  190 154 118 82 46 47
  51 45 39 33 27 21
  57 93 129 165 201 200
)
NUM_COLORS=${#COLORS[@]}

# Read and colorize the logo
while IFS= read -r line || [[ -n "$line" ]]; do
  output=""
  len=${#line}
  for ((i=0; i<len; i++)); do
    char="${line:i:1}"
    if [[ "$char" == " " ]]; then
      output+=" "
    else
      # Calculate color index based on column position + phase
      color_idx=$(( (i + PHASE) % NUM_COLORS ))
      color=${COLORS[$color_idx]}
      # Escape backslashes so printf %b doesn't interpret them
      if [[ "$char" == "\\" ]]; then
        char="\\\\"
      fi
      output+="\e[38;5;${color}m${char}"
    fi
  done
  printf '%b\e[0m\n' "$output"
done < "$LOGO_FILE"

# Add centered yellow tagline
echo ""
printf '\e[33m%s\e[0m\n' "      Record anything in the terminal"
