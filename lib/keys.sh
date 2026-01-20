#!/bin/bash
# betamax/lib/keys.sh - Keys file loading and directive processing

# Note: load_keys_file_with_lines() in validate.sh now handles file loading
# with line tracking for validation error messages.

expand_loops() {
  local EXPANDED_KEYS=()
  local in_loop=false
  local loop_count=0
  local loop_body=()

  for key in "${KEYS[@]}"; do
    if [[ "$key" == @repeat:* ]]; then
      if [[ "$in_loop" == true ]]; then
        echo "Error: Nested @repeat not supported" >&2
        exit 1
      fi
      in_loop=true
      loop_count="${key#@repeat:}"
      loop_body=()
    elif [[ "$key" == "@end" ]]; then
      if [[ "$in_loop" != true ]]; then
        echo "Error: @end without matching @repeat" >&2
        exit 1
      fi
      # Expand the loop
      for ((i=0; i<loop_count; i++)); do
        for body_key in "${loop_body[@]}"; do
          EXPANDED_KEYS+=("$body_key")
        done
      done
      in_loop=false
      loop_body=()
    elif [[ "$in_loop" == true ]]; then
      loop_body+=("$key")
    else
      EXPANDED_KEYS+=("$key")
    fi
  done

  if [[ "$in_loop" == true ]]; then
    echo "Error: @repeat without matching @end" >&2
    exit 1
  fi

  KEYS=("${EXPANDED_KEYS[@]}")
}

process_directives() {
  local REQUIRED_CMDS=()
  local FILTERED_KEYS=()

  for key in "${KEYS[@]}"; do
    case "$key" in
      @set:cols:*)
        [[ "$TERM_COLS_SET_BY_CLI" != true ]] && TERM_COLS_OVERRIDE="${key#@set:cols:}"
        ;;
      @set:rows:*)
        [[ "$TERM_ROWS_SET_BY_CLI" != true ]] && TERM_ROWS_OVERRIDE="${key#@set:rows:}"
        ;;
      @set:delay:*)
        [[ "$DELAY_MS_SET_BY_CLI" != true ]] && DELAY_MS="${key#@set:delay:}"
        ;;
      @set:output:*)
        [[ "$OUTPUT_DIR_SET_BY_CLI" != true ]] && OUTPUT_DIR="${key#@set:output:}"
        ;;
      @set:timeout:*)
        [[ "$TIMEOUT_SET_BY_CLI" != true ]] && TIMEOUT="${key#@set:timeout:}"
        ;;
      @set:shell:*)
        [[ "$SHELL_SET_BY_CLI" != true ]] && SHELL_OVERRIDE="${key#@set:shell:}"
        ;;
      @set:gif_delay:*)
        GIF_FRAME_DELAY_MS="${key#@set:gif_delay:}"
        ;;
      @set:speed:*)
        local speed_val="${key#@set:speed:}"
        # Validate speed is a number in range 0.25-4.0
        if [[ "$speed_val" =~ ^[0-9]*\.?[0-9]+$ ]]; then
          local valid=$(echo "$speed_val >= 0.25 && $speed_val <= 4.0" | bc -l)
          if [[ "$valid" == "1" ]]; then
            GIF_PLAYBACK_SPEED="$speed_val"
          else
            echo "Error: @set:speed must be between 0.25 and 4.0 (got: $speed_val)" >&2
            exit 1
          fi
        else
          echo "Error: @set:speed requires a numeric value (got: $speed_val)" >&2
          exit 1
        fi
        ;;
      @set:window_bar:*)
        GIF_WINDOW_BAR="${key#@set:window_bar:}"
        ;;
      @set:bar_color:*)
        local color="${key#@set:bar_color:}"
        [[ "$color" != \#* ]] && color="#$color"
        GIF_BAR_COLOR="$color"
        ;;
      @set:border_radius:*)
        GIF_BORDER_RADIUS="${key#@set:border_radius:}"
        ;;
      @set:margin:*)
        GIF_MARGIN="${key#@set:margin:}"
        ;;
      @set:margin_color:*)
        local color="${key#@set:margin_color:}"
        [[ "$color" != \#* ]] && color="#$color"
        GIF_MARGIN_COLOR="$color"
        ;;
      @set:padding:*)
        GIF_PADDING="${key#@set:padding:}"
        ;;
      @set:padding_color:*)
        local color="${key#@set:padding_color:}"
        [[ "$color" != \#* ]] && color="#$color"
        GIF_PADDING_COLOR="$color"
        ;;
      @require:*)
        REQUIRED_CMDS+=("${key#@require:}")
        ;;
      *)
        FILTERED_KEYS+=("$key")
        ;;
    esac
  done

  KEYS=("${FILTERED_KEYS[@]}")

  # Validate required dependencies
  if [[ ${#REQUIRED_CMDS[@]} -gt 0 ]]; then
    local MISSING=()
    for cmd in "${REQUIRED_CMDS[@]}"; do
      if ! command -v "$cmd" &>/dev/null; then
        MISSING+=("$cmd")
      fi
    done
    if [[ ${#MISSING[@]} -gt 0 ]]; then
      echo "Error: Missing required commands: ${MISSING[*]}" >&2
      exit 1
    fi
  fi
}
