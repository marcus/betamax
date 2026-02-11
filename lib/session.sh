#!/bin/bash
# betamax/lib/session.sh - tmux session management

session_start() {
  # Kill any existing session with same name
  tmux_cmd kill-session -t "$SESSION" 2>/dev/null || true

  # Start tmux session with the command
  # remain-on-exit keeps the pane alive after command exits (for GIF capture)
  if [[ -n "$SHELL_OVERRIDE" ]]; then
    SHELL="$SHELL_OVERRIDE" tmux_cmd new-session -d -s "$SESSION" -x "$TERM_COLS" -y "$TERM_LINES" "$COMMAND"
  else
    tmux_cmd new-session -d -s "$SESSION" -x "$TERM_COLS" -y "$TERM_LINES" "$COMMAND"
  fi
  tmux_cmd set-option -t "$SESSION" remain-on-exit on
}

session_wait_for_pattern() {
  if [[ -z "$WAIT_PATTERN" ]]; then
    return 0
  fi

  log_debug "session" "Waiting for pattern: $WAIT_PATTERN"
  for ((i=0; i<TIMEOUT*2; i++)); do
    if tmux_cmd capture-pane -t "$SESSION" -p 2>/dev/null | grep -q "$WAIT_PATTERN"; then
      log_info "session" "Pattern found, proceeding with keys"
      sleep "$DELAY_SEC"
      return 0
    fi
    sleep 0.5
  done

  log_error "session" "Timeout waiting for pattern '$WAIT_PATTERN' (waited ${TIMEOUT}s)"
  tmux_cmd kill-session -t "$SESSION" 2>/dev/null || true
  exit 1
}

session_cleanup() {
  if [[ "$KEEP" == true ]]; then
    log_info "session" "Session '$SESSION' kept alive. Attach with: tmux -L $TMUX_SOCKET attach -t $SESSION"
  else
    sleep "$DELAY_SEC"
    tmux_cmd kill-session -t "$SESSION" 2>/dev/null || true
    log_info "session" "Completed successfully"
  fi
}
