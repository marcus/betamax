#!/bin/bash
# betamax/lib/logging.sh - Standardized logging for shell scripts

# Log levels: debug < info < warning < error
# Default level: info (set via BETAMAX_LOG_LEVEL environment variable)
BETAMAX_LOG_LEVEL="${BETAMAX_LOG_LEVEL:-info}"

# Color codes for terminal output
LOG_COLOR_DEBUG="\033[36m"    # cyan
LOG_COLOR_INFO="\033[32m"     # green
LOG_COLOR_WARNING="\033[33m"  # yellow
LOG_COLOR_ERROR="\033[31m"    # red
LOG_COLOR_RESET="\033[0m"

# Detect if output is a terminal (supports color)
if [[ -t 2 ]]; then
  LOG_USE_COLOR=true
else
  LOG_USE_COLOR=false
fi

# Get log level priority (higher = more verbose)
_get_log_priority() {
  case "$1" in
    debug) echo 3 ;;
    info)  echo 2 ;;
    warning|warn) echo 1 ;;
    error) echo 0 ;;
    *) echo 2 ;; # default to info
  esac
}

# Check if log level should be output
_should_log() {
  local msg_level="$1"
  local msg_priority=$(_get_log_priority "$msg_level")
  local current_priority=$(_get_log_priority "$BETAMAX_LOG_LEVEL")
  [[ "$msg_priority" -le "$current_priority" ]]
}

# Internal logging function with timestamp and context
_log_internal() {
  local level="$1"
  local context="$2"
  local message="$3"

  if ! _should_log "$level"; then
    return 0
  fi

  # Get color based on level
  local color=""
  case "$level" in
    debug)   color="$LOG_COLOR_DEBUG" ;;
    info)    color="$LOG_COLOR_INFO" ;;
    warning) color="$LOG_COLOR_WARNING" ;;
    error)   color="$LOG_COLOR_ERROR" ;;
  esac

  # Format message with timestamp and context
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  local context_str=""
  if [[ -n "$context" ]]; then
    context_str="[$context] "
  fi

  local prefix="[$timestamp] $(printf '%-7s' "$level") "

  if [[ "$LOG_USE_COLOR" == "true" ]]; then
    printf "%s%s%s%s\n" "$color" "$prefix" "$context_str" "$message$LOG_COLOR_RESET" >&2
  else
    printf "%s%s%s\n" "$prefix" "$context_str" "$message" >&2
  fi
}

# Public logging functions with optional context parameter

# Log debug message (only when BETAMAX_LOG_LEVEL=debug)
# Usage: log_debug "message" or log_debug "context" "message"
log_debug() {
  if [[ $# -eq 2 ]]; then
    _log_internal "debug" "$1" "$2"
  else
    _log_internal "debug" "" "$1"
  fi
}

# Log info message (default level)
# Usage: log_info "message" or log_info "context" "message"
log_info() {
  if [[ $# -eq 2 ]]; then
    _log_internal "info" "$1" "$2"
  else
    _log_internal "info" "" "$1"
  fi
}

# Log warning (shows by default)
# Usage: log_warning "message" or log_warning "context" "message"
log_warning() {
  if [[ $# -eq 2 ]]; then
    _log_internal "warning" "$1" "$2"
  else
    _log_internal "warning" "" "$1"
  fi
}

# Log error and optionally exit (always shown)
# Usage: log_error "message" [exit_code]
# Usage: log_error "context" "message" [exit_code]
log_error() {
  local context=""
  local message=""
  local exit_code=1

  if [[ $# -eq 1 ]]; then
    message="$1"
  elif [[ $# -eq 2 ]]; then
    # Could be "context" "message" or "message" "exit_code"
    if [[ "$2" =~ ^[0-9]+$ ]]; then
      message="$1"
      exit_code="$2"
    else
      context="$1"
      message="$2"
    fi
  elif [[ $# -eq 3 ]]; then
    context="$1"
    message="$2"
    exit_code="$3"
  fi

  _log_internal "error" "$context" "$message"
  return "$exit_code"
}

# Log and exit with error
# Usage: die "message" [exit_code]
die() {
  log_error "$@"
  exit "${PIPESTATUS[0]}"
}

# Enable debug logging
enable_debug() {
  BETAMAX_LOG_LEVEL="debug"
  log_debug "Debug logging enabled"
}

# Export functions so they're available in sourced scripts
export -f log_debug log_info log_warning log_error die enable_debug
export BETAMAX_LOG_LEVEL
