#!/bin/bash
# betamax/lib/keys.sh - Keys file loading and directive processing

load_keys_file() {
  if [[ -z "$KEYS_FILE" ]]; then
    return 0
  fi

  if [[ ! -f "$KEYS_FILE" ]]; then
    echo "Error: Keys file not found: $KEYS_FILE" >&2
    exit 1
  fi

  while IFS= read -r line || [[ -n "$line" ]]; do
    # Strip inline comments
    line="${line%%#*}"
    # Trim whitespace
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    # Skip empty lines
    [[ -z "$line" ]] && continue
    KEYS+=("$line")
  done < "$KEYS_FILE"
}

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
