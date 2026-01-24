#!/bin/bash
# betamax/lib/args.sh - Argument parsing

show_help() {
  cat << 'EOF'
betamax - Reproducible terminal screenshots and GIF demos

Runs commands in a headless tmux session, sends keystrokes with controlled
timing, and captures output as PNG, HTML, text, or animated GIF.

Usage:
  betamax [options] <command> -- <key1> <key2> ...
  betamax [options] <command> -f <keys-file>
  betamax record [options] <command>
  betamax capture [options] [command]

Subcommands:
  record    Record an interactive session to a .keys file
            Run 'betamax record --help' for recording options
  capture   Capture TUI screenshots interactively with a hotkey
            Run 'betamax capture --help' for capture options

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
  --validate-only       Validate keys file syntax without executing

Decoration Options (apply to @capture and @record in keys files):
  --window-bar STYLE     Window bar: colorful, colorful_right, rings
  --bar-color COLOR      Bar background color (default: #1e1e1e)
  --bar-height N         Bar height in pixels (default: 30)
  --border-radius N      Corner radius in pixels (default: 0)
  --margin N             Outer margin in pixels (default: 0)
  --margin-color COLOR   Margin color (default: #000000)
  --padding N            Inner padding in pixels (default: 0)
  --padding-color COLOR  Padding color (default: #1e1e1e)
  --shadow               Enable drop shadow
  --shadow-blur N        Shadow blur radius (default: 15)
  --shadow-offset-x N    Shadow X offset (default: 0)
  --shadow-offset-y N    Shadow Y offset (default: 8)
  --shadow-opacity F     Shadow opacity 0.0-1.0 (default: 0.4)
  --shadow-color COLOR   Shadow color (default: #000000)
  --theme NAME           Color theme (dracula, nord, catppuccin-mocha, etc.)
  --preset NAME          Load preset from ~/.config/betamax/presets/

Keys File Format (.keys):
  Declarative scripts with settings, actions, and keystrokes.

  Settings:       @set:cols:80  @set:delay:100  @set:theme:dracula
                  @set:window_bar:colorful  @set:shadow:true
                  @set:border_radius:10  @set:margin:20  @set:padding:10
                  @set:gif_delay:200  @set:speed:1.5  @set:loop_offset:500
  Actions:        @sleep:1000  @wait:pattern  @pause  @source:other.keys
                  @capture:name.png  @capture:name.html  @capture:name.txt
                  @record:start  @record:stop:output.gif  @frame
                  @record:pause  @record:resume  @hide  @show
                  @repeat:3 ... @end  @require:dependency
  Keys:           Enter  Escape  Tab  Space  BSpace  Up  Down  Left  Right
                  C-c (Ctrl)  M-x (Alt)  F1-F12  Home  End  PPage  NPage  DC
  Per-key delay:  key@MS  (e.g. Enter@1000)

Config Files (key=value, # comments):
  .betamaxrc                               Project config (searched up to git root)
  ~/.config/betamax/config                  Global config
  ~/.config/betamax/presets/<name>.conf     Named presets (--preset NAME)

  Precedence: CLI flags > @set directives > .betamaxrc > global > preset > defaults

Dependencies:
  tmux       Required    Headless terminal sessions
  bc         Required    Timing calculations
  python3    Required    Recording and GIF generation
  termshot   For PNG     brew install homeport/tap/termshot
  aha        For HTML    brew install aha
  ffmpeg     For GIF     brew install ffmpeg
  Pillow     For decor   pip install Pillow

Examples:
  betamax vim test.txt -- i Hello Escape :wq Enter
  betamax vim test.txt -f demo.keys
  betamax --validate-only vim -f demo.keys
  betamax -k htop -- q                    # keep session for inspection
  betamax -c -d 100 bash -- ls Enter      # capture final output
  betamax myapp -f demo.keys --theme dracula --shadow --window-bar colorful
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
      --window-bar)
        GIF_WINDOW_BAR="$2"
        GIF_WINDOW_BAR_SET_BY_CLI=true
        shift 2
        ;;
      --bar-color)
        GIF_BAR_COLOR="$2"
        GIF_BAR_COLOR_SET_BY_CLI=true
        shift 2
        ;;
      --bar-height)
        GIF_BAR_HEIGHT="$2"
        GIF_BAR_HEIGHT_SET_BY_CLI=true
        shift 2
        ;;
      --border-radius)
        GIF_BORDER_RADIUS="$2"
        GIF_BORDER_RADIUS_SET_BY_CLI=true
        shift 2
        ;;
      --margin)
        GIF_MARGIN="$2"
        GIF_MARGIN_SET_BY_CLI=true
        shift 2
        ;;
      --margin-color)
        GIF_MARGIN_COLOR="$2"
        GIF_MARGIN_COLOR_SET_BY_CLI=true
        shift 2
        ;;
      --padding)
        GIF_PADDING="$2"
        GIF_PADDING_SET_BY_CLI=true
        shift 2
        ;;
      --padding-color)
        GIF_PADDING_COLOR="$2"
        GIF_PADDING_COLOR_SET_BY_CLI=true
        shift 2
        ;;
      --shadow)
        GIF_SHADOW=true
        GIF_SHADOW_SET_BY_CLI=true
        shift
        ;;
      --shadow-blur)
        GIF_SHADOW_BLUR="$2"
        GIF_SHADOW_BLUR_SET_BY_CLI=true
        shift 2
        ;;
      --shadow-offset-x)
        GIF_SHADOW_OFFSET_X="$2"
        GIF_SHADOW_OFFSET_X_SET_BY_CLI=true
        shift 2
        ;;
      --shadow-offset-y)
        GIF_SHADOW_OFFSET_Y="$2"
        GIF_SHADOW_OFFSET_Y_SET_BY_CLI=true
        shift 2
        ;;
      --shadow-opacity)
        GIF_SHADOW_OPACITY="$2"
        GIF_SHADOW_OPACITY_SET_BY_CLI=true
        shift 2
        ;;
      --shadow-color)
        GIF_SHADOW_COLOR="$2"
        GIF_SHADOW_COLOR_SET_BY_CLI=true
        shift 2
        ;;
      --theme)
        THEME="$2"
        THEME_SET_BY_CLI=true
        shift 2
        ;;
      --preset)
        PRESET="$2"
        shift 2
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
