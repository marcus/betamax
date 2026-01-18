# Betamax

Terminal session recorder for TUI apps. Inspired by [charmbracelet/vhs](https://github.com/charmbracelet/vhs), using tmux for headless operation.

![Betamax](betamax.png)

## Installation

```bash
# Clone and add to PATH
git clone https://github.com/youruser/betamax ~/code/betamax
export PATH="$HOME/code/betamax:$PATH"

# Or symlink to a directory in your PATH
ln -s ~/code/betamax/betamax /usr/local/bin/betamax
```

### Dependencies

- `tmux` - required for headless terminal sessions
- `termshot` - for PNG output (`brew install homeport/tap/termshot`)
- `aha` - for HTML output (`brew install aha`)
- `ffmpeg` - for GIF recording (`brew install ffmpeg`)

## Quick Start

```bash
# Inline keys
betamax "vim /tmp/test.txt" -- i "hello world" Escape ":wq" Enter

# Keys file
betamax "myapp" -f capture-screenshot.keys
```

## Usage

```
betamax [options] <command> -- <key1> <key2> ...
betamax [options] <command> -f <keys-file>
```

### Options

| Option | Description |
|--------|-------------|
| `-s, --session NAME` | Session name (default: betamax) |
| `-d, --delay MS` | Delay between keys in ms (default: 500) |
| `-w, --wait PATTERN` | Wait for pattern before sending keys |
| `-t, --timeout SEC` | Timeout waiting for app (default: 30) |
| `-k, --keep` | Keep session alive after keys sent |
| `-c, --capture` | Capture and print final pane state |
| `-o, --output-dir DIR` | Output directory for captures (default: ./captures) |
| `-f, --keys-file FILE` | Read keys from file |
| `--cols COLS` | Terminal width (default: current terminal) |
| `--rows ROWS` | Terminal height (default: current terminal) |
| `--shell PATH` | Shell to use in tmux session |

## Keys File Format

Keys files are declarative scripts that define terminal interactions. Each line is either a directive, an action, or a key to send.

### Example

```bash
# capture-demo.keys

# Settings (VHS-inspired) - CLI flags override these
@set:cols:120
@set:rows:40
@set:delay:100
@set:output:./screenshots
@set:shell:/bin/bash
@require:termshot

# Keys and actions
@sleep:500                # Wait for app to start
Escape                    # Clear any input focus
@wait:Ready               # Wait for "Ready" text
j@50                      # Navigate down quickly (50ms delay)
j@50
j@50
Enter@300                 # Select item, wait 300ms
@capture:demo.png         # Take screenshot
q                         # Quit
y                         # Confirm
```

### Settings Directives

Settings at the top of a keys file make it self-describing and reproducible.

| Directive | Description |
|-----------|-------------|
| `@set:cols:N` | Terminal width (overridden by `--cols`) |
| `@set:rows:N` | Terminal height (overridden by `--rows`) |
| `@set:delay:MS` | Default delay between keys (overridden by `-d`) |
| `@set:output:DIR` | Output directory (overridden by `-o`) |
| `@set:timeout:SEC` | Wait timeout (overridden by `-t`) |
| `@set:shell:PATH` | Shell for consistent environment (overridden by `--shell`) |
| `@set:gif_delay:MS` | Frame duration in GIF playback (default: 200ms) |
| `@require:CMD` | Fail fast if CMD not in PATH |

### Actions

| Action | Description |
|--------|-------------|
| `@sleep:MS` | Wait MS milliseconds |
| `@wait:PATTERN` | Wait for text pattern to appear |
| `@wait:/REGEX/` | Wait for regex pattern to match |
| `@capture` | Capture to stdout |
| `@capture:NAME.png` | Save as PNG (requires termshot) |
| `@capture:NAME.html` | Save as HTML (requires aha) |
| `@capture:NAME.txt` | Save as plain text with ANSI codes |
| `@capture:NAME` | Save all available formats |
| `@pause` | Wait for Enter (interactive debugging) |
| `@record:start` | Start GIF recording |
| `@record:stop:NAME.gif` | Stop recording and save GIF |
| `@frame` | Capture a frame (during recording) |

### Key Syntax

Keys use tmux send-keys format:

| Key | Syntax |
|-----|--------|
| Letters/numbers | `a`, `b`, `1`, `2` |
| Enter | `Enter` |
| Escape | `Escape` |
| Tab / Shift+Tab | `Tab`, `BTab` |
| Arrow keys | `Up`, `Down`, `Left`, `Right` |
| Ctrl+key | `C-c`, `C-v`, `C-x` |
| Alt+key | `M-x`, `M-a` |
| Function keys | `F1`, `F2`, ... `F12` |
| Space | `Space` |
| Backspace | `BSpace` |
| Delete | `DC` |
| Home/End | `Home`, `End` |
| Page Up/Down | `PPage`, `NPage` |

### Per-Key Timing

Override the default delay for individual keys using `key@MS`:

```bash
j@50        # Press j, wait 50ms
j@50        # Rapid navigation
j@50
Enter@1000  # Press Enter, wait 1 second
```

## Examples

### Capture a TUI Screenshot

```bash
betamax "sidecar" -w Sidecar -f capture-td.keys
```

Where `capture-td.keys`:
```bash
@set:cols:200
@set:rows:50
@set:output:./screenshots
@require:termshot

@sleep:500
1                         # Switch to first tab
@sleep:300
@capture:sidecar-td.png
q
y
```

### Quick Inline Demo

```bash
betamax "htop" -w "CPU" --cols 120 --rows 30 -- \
  @sleep:1000 @capture:htop.png q
```

### Interactive Debugging

```bash
betamax "myapp" -k -f debug.keys
# Session stays alive, attach with: tmux attach -t betamax
```

### Record a GIF

GIF recording captures frames at specific points, giving you precise control over the animation.

```bash
betamax 'vim --clean -c "set shortmess+=I"' -f record-vim.keys
```

Where `record-vim.keys`:
```bash
@set:cols:80
@set:rows:24
@set:delay:80

# Wait for vim to load
@sleep:400

# Start recording
@record:start

# Type with frame capture after each character
i
@frame
H
@frame
e
@frame
l
@frame
l
@frame
o
@frame

# Exit insert mode and pause to show result
Escape
@sleep:300

# Quit
:q!
Enter

# Save the GIF
@record:stop:vim-demo.gif
```

**How GIF recording works:**
- `@record:start` begins a recording session
- `@frame` captures the current terminal state as a frame
- `@sleep` automatically captures frames before and after the pause
- `@record:stop:NAME.gif` compiles frames into an animated GIF
- Use `@set:gif_delay:MS` to control playback speed (default: 200ms per frame)

**Tips:**
- Use `@frame` after each key you want visible in the animation
- Use `@sleep` to add pauses that highlight important states
- Frames are only captured at explicit points, not on every keystroke
- For apps that quit (like vim), frames after exit are gracefully skipped

## Design Philosophy

Betamax is inspired by [VHS](https://github.com/charmbracelet/vhs) but takes a different approach:

- **tmux-based**: Uses tmux for headless operation instead of a custom terminal emulator
- **Lightweight**: Single bash script with minimal dependencies
- **Declarative**: Keys files are self-describing with inline settings
- **CI-friendly**: Reproducible captures for documentation and testing

## License

MIT
