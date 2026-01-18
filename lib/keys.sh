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
