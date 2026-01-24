---
sidebar_position: 2
title: CLI Reference
---

# CLI Reference

Complete reference for the Betamax command-line interface.

## Synopsis

```
betamax [options] <command> -- <key1> <key2> ...
betamax [options] <command> -f <keys-file>
betamax record [options] <command>
betamax capture [options] [command]
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `-s, --session NAME` | `betamax` | Session name for tmux |
| `-d, --delay MS` | `500` | Delay between keys in milliseconds |
| `-w, --wait PATTERN` | - | Wait for pattern before sending keys |
| `-t, --timeout SEC` | `30` | Timeout waiting for app |
| `-k, --keep` | - | Keep session alive after keys sent |
| `-c, --capture` | - | Capture and print final pane state |
| `-o, --output-dir DIR` | `./captures` | Output directory for captures |
| `-f, --keys-file FILE` | - | Read keys from file |
| `--cols COLS` | current terminal | Terminal width |
| `--rows ROWS` | current terminal | Terminal height |
| `--shell PATH` | - | Shell to use in tmux session |
| `--validate-only` | - | Validate keys file syntax without executing |

### Decoration Options

These flags apply to `@capture` and `@record:stop` actions in keys files. CLI flags override `@set:` directives, which override config file values.

| Option | Default | Description |
|--------|---------|-------------|
| `--window-bar STYLE` | - | Window bar: `colorful`, `colorful_right`, `rings` |
| `--bar-color COLOR` | `#1e1e1e` | Window bar background color |
| `--bar-height N` | `30` | Window bar height in pixels |
| `--border-radius N` | `0` | Corner radius in pixels |
| `--margin N` | `0` | Outer margin in pixels |
| `--margin-color COLOR` | `#000000` | Margin color |
| `--padding N` | `0` | Inner padding in pixels |
| `--padding-color COLOR` | `#1e1e1e` | Padding color |
| `--shadow` | off | Enable drop shadow |
| `--shadow-blur N` | `15` | Shadow blur radius |
| `--shadow-offset-x N` | `0` | Shadow horizontal offset |
| `--shadow-offset-y N` | `8` | Shadow vertical offset |
| `--shadow-opacity F` | `0.4` | Shadow opacity (0.0-1.0) |
| `--shadow-color COLOR` | `#000000` | Shadow color |
| `--theme NAME` | - | Color theme (dracula, nord, catppuccin-mocha, etc.) |
| `--preset NAME` | - | Load preset from `~/.config/betamax/presets/` |

## Examples

### Basic Usage

Send inline keys to a command:

```bash
betamax "vim /tmp/test.txt" -- i "hello world" Escape ":wq" Enter
```

### Using a Keys File

```bash
betamax "myapp" -f capture-screenshot.keys
```

### Wait for Application Ready

Wait for specific text before sending keys:

```bash
betamax "htop" -w "CPU" -- @sleep:1000 @capture:htop.png q
```

### Custom Terminal Size

```bash
betamax "htop" --cols 120 --rows 30 -- @sleep:1000 q
```

### Keep Session Alive for Debugging

```bash
betamax "myapp" -k -f debug.keys
# Attach with: tmux attach -t betamax
```

### Custom Session Name

Run multiple instances with different session names:

```bash
betamax -s session1 "app1" -f keys1.keys &
betamax -s session2 "app2" -f keys2.keys &
```

### Capture Output to Custom Directory

```bash
betamax "neofetch" -o ./screenshots -- @sleep:500 @capture:system
```

### Capture and Print to Stdout

```bash
betamax "ls --color" -c -- @sleep:100
```

### Decorated Playback

Override decorations from the command line without editing the keys file:

```bash
betamax "myapp" -f demo.keys --theme dracula --shadow --window-bar colorful
betamax "myapp" -f demo.keys --border-radius 10 --padding 10 --margin 20
```

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | General error (missing dependencies, invalid options) |
| `124` | Timeout waiting for pattern |

---

## `betamax record`

Record interactive terminal sessions and generate `.keys` files with precise keystroke timing.

### Synopsis

```
betamax record [options] <command>
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output FILE` | `recording.keys` | Output `.keys` file path |
| `--gif FILE` | - | Generate animated GIF after recording |
| `--auto-frame` | - | Add `@frame` directive after every keystroke |
| `--frame-key KEY` | `C-g` | Hotkey to manually mark frames during recording |
| `--delay MS` | - | Use fixed delay instead of measured timing |
| `--min-delay MS` | `50` | Minimum delay threshold (shorter delays become zero) |
| `--max-delay MS` | `2000` | Maximum delay cap (longer delays clamped) |
| `--cols COLS` | current terminal | Terminal width |
| `--rows ROWS` | current terminal | Terminal height |
| `--max-duration SEC` | `300` | Maximum recording duration (5 minutes) |

### Recording Workflow

1. **Start**: Launch with `betamax record -o output.keys <command>`
2. **Record**: Type normally - all keystrokes are captured with timing
3. **Mark frames**: Press `Ctrl+G` (or custom `--frame-key`) to mark GIF frames
4. **Stop**: Press `Ctrl+D` or type `exit` to end recording

### Examples

#### Basic Recording

```bash
betamax record -o session.keys vim test.txt
```

#### Record with GIF Generation

```bash
betamax record --gif demo.gif --auto-frame htop
```

#### Custom Frame Hotkey

```bash
betamax record --frame-key C-f -o demo.keys myapp
```

#### Fixed Delay Timing

```bash
betamax record --delay 100 -o demo.keys vim
```

### Features

- **UTF-8 support**: Multi-byte characters properly captured
- **Modifier keys**: Ctrl, Alt, Shift combinations recorded accurately
- **Terminal noise filtering**: Automatic filtering of terminal escape sequences
- **Timing analysis**: Calculates median delay for natural playback

### Generated File Format

The `.keys` file includes:

```bash
# Command: vim test.txt
# Duration: 45s | Keystrokes: 23

@set:cols:80
@set:rows:24
@set:delay:120

i@50
"hello world"
Escape
@sleep:500
":wq"
Enter
```

---

## `betamax capture`

Capture PNG screenshots of any TUI interactively. Binds a hotkey that works regardless of what application is running.

### Synopsis

```
betamax capture [options] [command]
```

If no command is given, launches your default shell.

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--key KEY` | `C-g` | Capture hotkey (tmux key format) |
| `--output-dir DIR` | `./captures` | Output directory for PNGs |
| `--cols N` | current terminal | Terminal width |
| `--rows N` | current terminal | Terminal height |
| `--preset NAME` | - | Load named preset from `~/.config/betamax/presets/` |
| `--save-text` | off | Also save raw ANSI text file alongside PNG |
| `--window-bar STYLE` | - | Window bar: `colorful`, `colorful_right`, `rings` |
| `--bar-color COLOR` | `#1e1e1e` | Window bar background |
| `--border-radius N` | `0` | Corner radius in pixels |
| `--margin N` | `0` | Outer margin in pixels |
| `--margin-color COLOR` | `#000000` | Margin color |
| `--padding N` | `0` | Inner padding in pixels |
| `--padding-color COLOR` | `#1e1e1e` | Padding color |
| `--shadow` | off | Enable drop shadow |
| `--theme NAME` | - | Apply a color theme |

### Capture Workflow

1. **Start**: Launch with `betamax capture [command]`
2. **Interact**: Use your application normally
3. **Capture**: Press `Ctrl+G` (or custom `--key`) to screenshot
4. **Finish**: Exit the command normally - file paths are printed

### Examples

#### Basic Capture

```bash
betamax capture vim myfile.py
```

#### Decorated Screenshots

```bash
betamax capture --theme dracula --shadow --window-bar colorful htop
```

#### Custom Hotkey

```bash
betamax capture --key C-s vim
```

#### Shell Session

```bash
betamax capture
# Run commands, press Ctrl+G to capture, type 'exit' when done
```

### Recovery

Orphaned sessions (from crashes) are detected on startup. Clean up with:

```bash
tmux -L betamax kill-session -t <name>
```

---

## See Also

- [Keys File Format](/docs/keys-file-format) - Detailed reference for keys file syntax
- [Recording Guide](/docs/guides/recording) - In-depth guide to recording sessions
- [Capturing Screenshots](/docs/guides/capturing) - In-depth guide to interactive capture
- [Examples](/docs/examples) - Practical examples for common use cases
