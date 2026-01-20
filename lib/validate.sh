#!/bin/bash
# betamax/lib/validate.sh - Pre-flight validation for .keys files

# Store original lines with line numbers for error reporting
declare -a ORIGINAL_LINES=()
declare -a LINE_NUMBERS=()

# Load keys file with line tracking for validation error messages
load_keys_file_with_lines() {
  if [[ -z "$KEYS_FILE" ]]; then
    return 0
  fi

  if [[ ! -f "$KEYS_FILE" ]]; then
    echo "Error: Keys file not found: $KEYS_FILE" >&2
    exit 1
  fi

  local line_num=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    ((line_num++))
    # Store original for error messages
    local original="$line"
    # Strip inline comments
    line="${line%%#*}"
    # Trim whitespace
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    # Skip empty lines
    [[ -z "$line" ]] && continue
    KEYS+=("$line")
    ORIGINAL_LINES+=("$original")
    LINE_NUMBERS+=("$line_num")
  done < "$KEYS_FILE"
}

# Report validation error with line info
validation_error() {
  local msg="$1"
  local idx="$2"
  if [[ -n "$idx" ]]; then
    echo "Error: $msg (line ${LINE_NUMBERS[$idx]}: ${ORIGINAL_LINES[$idx]})" >&2
  else
    echo "Error: $msg" >&2
  fi
}

# Report validation warning
validation_warning() {
  local msg="$1"
  local idx="$2"
  if [[ -n "$idx" ]]; then
    echo "Warning: $msg (line ${LINE_NUMBERS[$idx]})" >&2
  else
    echo "Warning: $msg" >&2
  fi
}

# Main validation function - returns 0 on success, exits 1 on error
validate_keys_file() {
  local errors=0
  local i

  for ((i=0; i<${#KEYS[@]}; i++)); do
    local key="${KEYS[$i]}"

    case "$key" in
      @set:*)
        validate_set_directive "$key" "$i" || ((errors++))
        ;;
      @repeat:*|@repeat)
        validate_repeat_directive "$key" "$i" || ((errors++))
        ;;
      @end)
        # Handled in validate_repeat_structure
        ;;
      @sleep:*|@sleep)
        validate_sleep_directive "$key" "$i" || ((errors++))
        ;;
      @wait:*|@wait)
        validate_wait_directive "$key" "$i" || ((errors++))
        ;;
      @capture:*|@capture)
        validate_capture_directive "$key" "$i" || ((errors++))
        ;;
      @record:*|@record)
        validate_record_directive "$key" "$i" || ((errors++))
        ;;
      @require:*|@require)
        validate_require_directive "$key" "$i" || ((errors++))
        ;;
      @source:*|@source)
        validate_source_directive "$key" "$i" || ((errors++))
        ;;
      @pause|@frame)
        # Valid standalone directives, no validation needed
        ;;
      @*)
        validate_unknown_directive "$key" "$i"
        ;;
      *)
        # Regular key - check for inline timing
        validate_key_timing "$key" "$i" || ((errors++))
        ;;
    esac
  done

  # Validate repeat/end structure
  validate_repeat_structure || ((errors++))

  if [[ $errors -gt 0 ]]; then
    exit 1
  fi

  return 0
}

# Validate @set directives
validate_set_directive() {
  local directive="$1"
  local idx="$2"
  local setting="${directive#@set:}"

  # Extract key and value
  local key="${setting%%:*}"
  local value="${setting#*:}"

  # Check if there's a value (key:value vs just key)
  if [[ "$key" == "$value" ]] || [[ -z "$value" ]]; then
    validation_error "Missing value for $key" "$idx"
    return 1
  fi

  case "$key" in
    cols|rows|timeout|gif_delay)
      if ! [[ "$value" =~ ^-?[0-9]+$ ]]; then
        validation_error "Invalid integer for $key: $value" "$idx"
        return 1
      fi
      if [[ "$value" -le 0 ]]; then
        validation_error "$key must be positive" "$idx"
        return 1
      fi
      ;;
    delay)
      if ! [[ "$value" =~ ^[0-9]+$ ]]; then
        validation_error "Invalid integer for delay: $value" "$idx"
        return 1
      fi
      # delay can be 0
      ;;
    output|shell)
      # Non-empty path is valid
      if [[ -z "$value" ]]; then
        validation_error "Missing value for $key" "$idx"
        return 1
      fi
      ;;
    speed)
      # Validate speed is a decimal between 0.25 and 4.0
      if ! [[ "$value" =~ ^[0-9]*\.?[0-9]+$ ]]; then
        validation_error "Invalid speed value: $value (must be numeric)" "$idx"
        return 1
      fi
      local valid=$(echo "$value >= 0.25 && $value <= 4.0" | bc -l)
      if [[ "$valid" != "1" ]]; then
        validation_error "Speed must be between 0.25 and 4.0 (got: $value)" "$idx"
        return 1
      fi
      ;;
    window_bar)
      # Valid styles: colorful, colorful_right, rings, none
      case "$value" in
        colorful|colorful_right|rings|none)
          ;;
        *)
          validation_error "Invalid window_bar style: $value (valid: colorful, colorful_right, rings, none)" "$idx"
          return 1
          ;;
      esac
      ;;
    bar_color|margin_color|padding_color)
      # Validate hex color format (6 hex digits, with or without # prefix)
      # Note: # starts a comment in .keys files, so prefer without #
      if ! [[ "$value" =~ ^#?[0-9a-fA-F]{6}$ ]]; then
        validation_error "Invalid color format for $key: $value (expected RRGGBB or #RRGGBB)" "$idx"
        return 1
      fi
      ;;
    border_radius|margin|padding)
      # Validate positive integer
      if ! [[ "$value" =~ ^[0-9]+$ ]]; then
        validation_error "Invalid integer for $key: $value" "$idx"
        return 1
      fi
      # Allow 0 for these (means disabled)
      ;;
    *)
      validation_error "Unknown setting: $key" "$idx"
      return 1
      ;;
  esac

  return 0
}

# Validate @repeat directive format
validate_repeat_directive() {
  local directive="$1"
  local idx="$2"

  if [[ "$directive" == "@repeat" ]]; then
    validation_error "Missing repeat count" "$idx"
    return 1
  fi

  local count="${directive#@repeat:}"

  if ! [[ "$count" =~ ^-?[0-9]+$ ]]; then
    validation_error "Invalid repeat count: $count" "$idx"
    return 1
  fi

  if [[ "$count" -le 0 ]]; then
    validation_error "Repeat count must be positive" "$idx"
    return 1
  fi

  return 0
}

# Validate @repeat/@end structure (nesting, matching)
validate_repeat_structure() {
  local in_loop=false
  local loop_start_line=""
  local loop_start_idx=""
  local i

  for ((i=0; i<${#KEYS[@]}; i++)); do
    local key="${KEYS[$i]}"

    if [[ "$key" == @repeat:* ]]; then
      if [[ "$in_loop" == true ]]; then
        validation_error "Nested @repeat not supported" "$i"
        return 1
      fi
      in_loop=true
      loop_start_line="${LINE_NUMBERS[$i]}"
      loop_start_idx="$i"
    elif [[ "$key" == "@end" ]]; then
      if [[ "$in_loop" != true ]]; then
        validation_error "@end without matching @repeat" "$i"
        return 1
      fi
      in_loop=false
    fi
  done

  if [[ "$in_loop" == true ]]; then
    validation_error "@repeat on line $loop_start_line has no matching @end" "$loop_start_idx"
    return 1
  fi

  return 0
}

# Validate @sleep directive
validate_sleep_directive() {
  local directive="$1"
  local idx="$2"

  if [[ "$directive" == "@sleep" ]]; then
    validation_error "Missing sleep duration" "$idx"
    return 1
  fi

  local spec="${directive#@sleep:}"

  # Check for :capture suffix
  local ms
  local suffix=""
  if [[ "$spec" == *:* ]]; then
    ms="${spec%%:*}"
    suffix="${spec#*:}"
    # Check for extra colons
    if [[ "$suffix" == *:* ]]; then
      validation_error "Invalid @sleep format" "$idx"
      return 1
    fi
    if [[ "$suffix" != "capture" ]]; then
      validation_error "Invalid sleep option: $suffix (expected :capture or nothing)" "$idx"
      return 1
    fi
  else
    ms="$spec"
  fi

  if [[ -z "$ms" ]]; then
    validation_error "Missing sleep duration" "$idx"
    return 1
  fi

  if ! [[ "$ms" =~ ^[0-9]+$ ]]; then
    validation_error "Invalid sleep duration: $ms" "$idx"
    return 1
  fi

  if [[ "$ms" -le 0 ]]; then
    validation_error "Sleep duration must be positive" "$idx"
    return 1
  fi

  return 0
}

# Validate @wait directive
validate_wait_directive() {
  local directive="$1"
  local idx="$2"

  if [[ "$directive" == "@wait" ]]; then
    validation_error "Missing wait pattern" "$idx"
    return 1
  fi

  local pattern="${directive#@wait:}"

  if [[ -z "$pattern" ]]; then
    validation_error "Missing wait pattern" "$idx"
    return 1
  fi

  # Check for unclosed regex
  if [[ "$pattern" =~ ^/ ]] && ! [[ "$pattern" =~ /$ ]]; then
    validation_error "Unclosed regex pattern (missing trailing /)" "$idx"
    return 1
  fi

  return 0
}

# Validate @capture directive
validate_capture_directive() {
  local directive="$1"
  local idx="$2"

  # @capture alone is valid (stdout capture)
  if [[ "$directive" == "@capture" ]]; then
    return 0
  fi

  local spec="${directive#@capture:}"

  # Check if has extension
  if [[ "$spec" == *.* ]]; then
    local ext="${spec##*.}"
    case "$ext" in
      txt|html|png)
        # Valid extensions
        ;;
      *)
        validation_error "Invalid capture format: $ext (valid: txt, html, png, or omit for all)" "$idx"
        return 1
        ;;
    esac
  fi
  # No extension = capture all formats, which is valid

  return 0
}

# Validate @record directive
validate_record_directive() {
  local directive="$1"
  local idx="$2"

  if [[ "$directive" == "@record" ]]; then
    validation_error "Invalid @record format (use @record:start, @record:pause, @record:resume, or @record:stop:<file>.gif)" "$idx"
    return 1
  fi

  local spec="${directive#@record:}"

  case "$spec" in
    start|pause|resume)
      # Valid
      ;;
    stop:*)
      local filename="${spec#stop:}"
      if [[ -z "$filename" ]]; then
        validation_error "Missing GIF filename for @record:stop" "$idx"
        return 1
      fi
      if [[ "$filename" != *.gif ]]; then
        validation_error "GIF filename must end with .gif" "$idx"
        return 1
      fi
      ;;
    *)
      validation_error "Unknown @record command: $spec (valid: start, pause, resume, stop:<file>.gif)" "$idx"
      return 1
      ;;
  esac

  return 0
}

# Validate @require directive
validate_require_directive() {
  local directive="$1"
  local idx="$2"

  if [[ "$directive" == "@require" ]]; then
    validation_error "Missing command name for @require" "$idx"
    return 1
  fi

  local cmd="${directive#@require:}"

  if [[ -z "$cmd" ]]; then
    validation_error "Missing command name for @require" "$idx"
    return 1
  fi

  if [[ "$cmd" == *" "* ]]; then
    validation_error "Invalid command name: contains spaces" "$idx"
    return 1
  fi

  return 0
}

# Validate @source directive
validate_source_directive() {
  local directive="$1"
  local idx="$2"

  if [[ "$directive" == "@source" ]]; then
    validation_error "Missing file path for @source" "$idx"
    return 1
  fi

  local path="${directive#@source:}"

  if [[ -z "$path" ]]; then
    validation_error "Missing file path for @source" "$idx"
    return 1
  fi

  # Check for null bytes (security)
  if [[ "$path" == *$'\x00'* ]]; then
    validation_error "@source path contains null bytes" "$idx"
    return 1
  fi

  # Resolve relative to keys file directory
  local full_path
  if [[ "$path" != /* ]]; then
    local keys_dir="$(dirname "$KEYS_FILE")"
    full_path="$keys_dir/$path"
  else
    full_path="$path"
  fi

  # Check file exists (warning only - might be created later)
  if [[ ! -f "$full_path" ]]; then
    validation_warning "@source file not found: $path" "$idx"
    # Not an error - file might be generated
  fi

  # Check for .keys extension
  if [[ "$path" != *.keys ]]; then
    validation_warning "@source file should have .keys extension" "$idx"
  fi

  return 0
}

# Warn on unknown @ directives
validate_unknown_directive() {
  local directive="$1"
  local idx="$2"
  local prefix="${directive%%:*}"

  # Known directive prefixes
  local known="@set @require @sleep @wait @pause @capture @record @repeat @end @frame @source"

  # Simple typo detection
  local suggestion=""
  case "$prefix" in
    @seet|@ste|@se)
      suggestion="@set"
      ;;
    @slep|@sleeo|@sleeep)
      suggestion="@sleep"
      ;;
    @wiat|@wat|@await)
      suggestion="@wait"
      ;;
    @caputre|@captur|@cap)
      suggestion="@capture"
      ;;
    @recrod|@reocrd|@rec|@recording)
      suggestion="@record"
      ;;
    @repat|@repaet|@loop)
      suggestion="@repeat"
      ;;
    @reuire|@requre|@req)
      suggestion="@require"
      ;;
    @fram|@frmae)
      suggestion="@frame"
      ;;
    @puase|@paus)
      suggestion="@pause"
      ;;
    @souce|@soruce|@src|@import|@include)
      suggestion="@source"
      ;;
  esac

  if [[ -n "$suggestion" ]]; then
    validation_warning "Unknown directive $prefix (did you mean $suggestion?)" "$idx"
  else
    validation_warning "Unknown directive $prefix" "$idx"
  fi
}

# Validate inline key timing
validate_key_timing() {
  local key="$1"
  local idx="$2"

  # Skip if no @ in key or if it's a modifier key like M-@
  if [[ "$key" != *@* ]]; then
    return 0
  fi

  # Check for M-@ (Alt+@) pattern - this is valid tmux key
  if [[ "$key" =~ ^[CM]-@ ]]; then
    return 0
  fi

  # Check for timing pattern: something@digits
  if [[ "$key" =~ ^(.+)@([0-9]*)$ ]]; then
    local timing="${BASH_REMATCH[2]}"
    if [[ -z "$timing" ]]; then
      validation_error "Invalid timing format: missing milliseconds" "$idx"
      return 1
    fi
    if [[ "$timing" -le 0 ]]; then
      validation_error "Timing override must be positive" "$idx"
      return 1
    fi
    return 0
  fi

  # Has @ but doesn't match timing pattern
  if [[ "$key" =~ @ ]] && ! [[ "$key" =~ ^[CM]-@ ]]; then
    # Check if it looks like a malformed timing
    if [[ "$key" =~ @[^0-9] ]]; then
      local after_at="${key#*@}"
      validation_error "Invalid timing value: $after_at" "$idx"
      return 1
    fi
  fi

  return 0
}
