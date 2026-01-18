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

## See Also

- [Keys File Format](/docs/keys-file-format) - Detailed reference for keys file syntax
- [Examples](/docs/examples) - Practical examples for common use cases
