#!/bin/bash
# betamax/lib/keys.sh - Keys file loading and directive processing

# Note: load_keys_file_with_lines() in validate.sh now handles file loading
# with line tracking for validation error messages.

# Track visited files for circular import detection
declare -a SOURCE_VISITED_FILES=()
declare -i SOURCE_DEPTH=0
declare -i SOURCE_MAX_DEPTH=10

# Process @source directives to import keys from other files
# Must be called after loading keys file but before other processing
process_source_directives() {
  local current_file="${1:-$KEYS_FILE}"
  local PROCESSED_KEYS=()

  # Get directory of current file for relative path resolution
  local current_dir
  local current_file_abs=""
  if [[ -n "$current_file" ]]; then
    current_dir="$(cd "$(dirname "$current_file")" && pwd)"
    current_file_abs="$current_dir/$(basename "$current_file")"

    # Track current file to detect circular imports
    # Only add if not already tracked (for recursive calls)
    local already_tracked=false
    for f in "${SOURCE_VISITED_FILES[@]}"; do
      if [[ "$f" == "$current_file_abs" ]]; then
        already_tracked=true
        break
      fi
    done
    if [[ "$already_tracked" == false ]]; then
      SOURCE_VISITED_FILES+=("$current_file_abs")
    fi
  else
    current_dir="$(pwd)"
  fi

  for key in "${KEYS[@]}"; do
    if [[ "$key" == @source:* ]]; then
      local source_path="${key#@source:}"

      # Resolve relative to current file
      if [[ "$source_path" != /* ]]; then
        source_path="$current_dir/$source_path"
      fi
      source_path="$(cd "$(dirname "$source_path")" 2>/dev/null && pwd)/$(basename "$source_path")"

      # Check depth limit
      if [[ $SOURCE_DEPTH -ge $SOURCE_MAX_DEPTH ]]; then
        echo "Error: @source depth limit exceeded ($SOURCE_MAX_DEPTH levels)" >&2
        echo "  Circular import? Check: $source_path" >&2
        exit 1
      fi

      # Check for circular import
      local file
      for file in "${SOURCE_VISITED_FILES[@]}"; do
        if [[ "$file" == "$source_path" ]]; then
          echo "Error: Circular @source detected" >&2
          echo "  File: $source_path" >&2
          echo "  Import chain:" >&2
          for visited in "${SOURCE_VISITED_FILES[@]}"; do
            echo "    -> $visited" >&2
          done
          echo "    -> $source_path (circular)" >&2
          exit 1
        fi
      done

      # Check file exists
      if [[ ! -f "$source_path" ]]; then
        echo "Error: @source file not found: $source_path" >&2
        echo "  Referenced from: $current_file" >&2
        exit 1
      fi

      # Track this file
      SOURCE_VISITED_FILES+=("$source_path")
      ((SOURCE_DEPTH++))

      # Load the sourced file
      local SOURCED_KEYS=()
      while IFS= read -r line || [[ -n "$line" ]]; do
        # Strip inline comments
        line="${line%%#*}"
        # Trim whitespace
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line%"${line##*[![:space:]]}"}"
        # Skip empty lines
        [[ -z "$line" ]] && continue
        SOURCED_KEYS+=("$line")
      done < "$source_path"

      # Recursively process @source in the sourced file
      local OLD_KEYS=("${KEYS[@]}")
      KEYS=("${SOURCED_KEYS[@]}")
      process_source_directives "$source_path"
      SOURCED_KEYS=("${KEYS[@]}")
      KEYS=("${OLD_KEYS[@]}")

      # Add sourced keys to output
      for sourced_key in "${SOURCED_KEYS[@]}"; do
        PROCESSED_KEYS+=("$sourced_key")
      done

      ((SOURCE_DEPTH--))
    else
      PROCESSED_KEYS+=("$key")
    fi
  done

  KEYS=("${PROCESSED_KEYS[@]}")
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
      @set:loop_offset:*)
        local offset_val="${key#@set:loop_offset:}"
        # Validate loop offset is a positive integer
        if [[ "$offset_val" =~ ^[0-9]+$ ]] && [[ "$offset_val" -gt 0 ]]; then
          GIF_LOOP_OFFSET="$offset_val"
        else
          echo "Error: @set:loop_offset requires a positive integer in milliseconds (got: $offset_val)" >&2
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
      @set:bar_height:*)
        GIF_BAR_HEIGHT="${key#@set:bar_height:}"
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
