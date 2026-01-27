#!/bin/bash
# gradient_logo.sh - Output betamax logo with animated rainbow gradient wave
#
# Usage: ./gradient_logo.sh [phase]
#   phase: 0-23 (wave offset), default 0

PHASE=${1:-0}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGO_FILE="${SCRIPT_DIR}/../betamax.txt"

# Powder blue (#7EB8DA) to pastel purple (#B8A9C9) gradient using 256-color mode
# Smooth cycling: powder blue -> lavender -> pastel purple -> lavender -> powder blue
COLORS=(
  117 117 153 153 159 159
  152 146 146 147 147 183
  183 182 182 141 141 140
  140 177 177 146 153 117
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

# Add centered tagline in powder blue
echo ""
printf '\e[38;5;153m%s\e[0m\n' "      Record anything in the terminal"
