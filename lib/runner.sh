#!/bin/bash
# betamax/lib/runner.sh - Key sending and command execution

run_keys() {
  local CAPTURE_COUNT=0

  for key in "${KEYS[@]}"; do
    case "$key" in
      @capture:*)
        # Capture to file(s)
        local spec="${key#@capture:}"
        local cap_name="${spec%.*}"
        local cap_ext="${spec##*.}"

        if [[ "$cap_name" == "$cap_ext" ]]; then
          capture_to_file "$cap_name" "all"
        else
          capture_to_file "$cap_name" "$cap_ext"
        fi
        ;;
      @capture)
        ((CAPTURE_COUNT++)) || true
        capture_to_stdout "$CAPTURE_COUNT"
        ;;
      @sleep:*)
        local MS="${key#@sleep:}"
        local SLEEP_SEC=$(echo "scale=3; $MS / 1000" | bc)
        echo "Sleeping ${MS}ms..."
        sleep "$SLEEP_SEC"
        ;;
      @wait:*)
        local PATTERN="${key#@wait:}"
        echo "Waiting for '$PATTERN'..."

        local REGEX GREP_OPTS
        if [[ "$PATTERN" =~ ^/(.+)/$ ]]; then
          REGEX="${BASH_REMATCH[1]}"
          GREP_OPTS="-E"
        else
          REGEX="$PATTERN"
          GREP_OPTS="-F"
        fi

        for ((i=0; i<TIMEOUT*2; i++)); do
          if tmux_cmd capture-pane -t "$SESSION" -p 2>/dev/null | grep -q $GREP_OPTS "$REGEX"; then
            break
          fi
          sleep 0.5
        done
        ;;
      @pause)
        echo "Paused. Press Enter to continue..."
        read -r
        ;;
      *)
        # Check for inline timing override: key@MS
        if [[ "$key" =~ ^(.+)@([0-9]+)$ ]]; then
          local ACTUAL_KEY="${BASH_REMATCH[1]}"
          local CUSTOM_MS="${BASH_REMATCH[2]}"
          local CUSTOM_SEC=$(echo "scale=3; $CUSTOM_MS / 1000" | bc)
          tmux_cmd send-keys -t "$SESSION" "$ACTUAL_KEY"
          sleep "$CUSTOM_SEC"
        else
          tmux_cmd send-keys -t "$SESSION" "$key"
          sleep "$DELAY_SEC"
        fi
        ;;
    esac
  done
}
