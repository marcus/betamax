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

## See Also

- [Keys File Format](/docs/keys-file-format) - Detailed reference for keys file syntax
- [Recording Guide](/docs/guides/recording) - In-depth guide to recording sessions
- [Examples](/docs/examples) - Practical examples for common use cases
