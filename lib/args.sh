#!/bin/bash
# betamax/lib/args.sh - Argument parsing

show_help() {
  cat << 'EOF'
betamax - Terminal session recorder for TUI apps

Usage:
  betamax [options] <command> -- <key1> <key2> ...
  betamax [options] <command> -f <keys-file>
  betamax record [options] <command>

Subcommands:
  record    Record an interactive session to a .keys file
            Run 'betamax record --help' for recording options

Options:
  -s, --session NAME    Session name (default: betamax)
  -d, --delay MS        Delay between keys in ms (default: 500)
  -w, --wait PATTERN    Wait for pattern before sending keys
  -t, --timeout SEC     Timeout waiting for app (default: 30)
  -k, --keep            Keep session alive after keys sent
  -c, --capture         Capture and print final pane state
  -o, --output-dir DIR  Output directory for captures (default: ./captures)
  -f, --keys-file FILE  Read keys from file (one per line)
  --cols COLS           Terminal width (default: current terminal)
  --rows ROWS           Terminal height (default: current terminal)
  --shell PATH          Shell to use in tmux session
  --validate-only       Validate keys file and exit (no execution)

See README.md for full documentation
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      -s|--session)
        SESSION="$2"
        shift 2
        ;;
      -d|--delay)
        DELAY_MS="$2"
        DELAY_MS_SET_BY_CLI=true
        shift 2
        ;;
      -w|--wait)
        WAIT_PATTERN="$2"
        shift 2
        ;;
      -t|--timeout)
        TIMEOUT="$2"
        TIMEOUT_SET_BY_CLI=true
        shift 2
        ;;
      -k|--keep)
        KEEP=true
        shift
        ;;
      -c|--capture)
        CAPTURE=true
        shift
        ;;
      -o|--output-dir)
        OUTPUT_DIR="$2"
        OUTPUT_DIR_SET_BY_CLI=true
        shift 2
        ;;
      -f|--keys-file)
        KEYS_FILE="$2"
        shift 2
        ;;
      --cols)
        TERM_COLS_OVERRIDE="$2"
        TERM_COLS_SET_BY_CLI=true
        shift 2
        ;;
      --rows)
        TERM_ROWS_OVERRIDE="$2"
        TERM_ROWS_SET_BY_CLI=true
        shift 2
        ;;
      --shell)
        SHELL_OVERRIDE="$2"
        SHELL_SET_BY_CLI=true
        shift 2
        ;;
      --validate-only)
        VALIDATE_ONLY=true
        shift
        ;;
      --)
        shift
        KEYS=("$@")
        break
        ;;
      -h|--help)
        show_help
        exit 0
        ;;
      *)
        if [[ -z "$COMMAND" ]]; then
          COMMAND="$1"
        else
          echo "Error: Unexpected argument: $1" >&2
          exit 1
        fi
        shift
        ;;
    esac
  done

  if [[ -z "$COMMAND" ]]; then
    echo "Error: No command specified" >&2
    echo "Usage: betamax [options] <command> -- <key1> <key2> ..." >&2
    exit 1
  fi
}
