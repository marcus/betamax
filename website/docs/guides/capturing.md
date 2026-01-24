---
sidebar_position: 3
title: Capturing Screenshots
---

# Capturing TUI Screenshots

Capture PNG screenshots of any TUI application interactively with `betamax capture`. Press a hotkey at any point during your session to snapshot the terminal state.

## Overview

```bash
betamax capture vim myfile.py
```

This launches your command inside a transparent tmux session. Press `Ctrl+G` at any time to capture the current screen as a PNG. When you exit, betamax reports the captured file paths.

## Basic Usage

### Start a Capture Session

```bash
betamax capture [command]
```

If no command is given, your default shell is launched.

### Take a Screenshot

Press `Ctrl+G` (default) at any time. A brief green confirmation message appears, then you continue working normally.

### Finish

Exit your command normally (`:wq` in vim, `q` in htop, `exit` in a shell). Betamax prints the paths of all captured PNGs.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--key KEY` | `C-g` | Capture hotkey (tmux key format) |
| `--output-dir DIR` | `./captures` | Output directory for PNGs |
| `--cols N` | current terminal | Terminal width |
| `--rows N` | current terminal | Terminal height |

### Decoration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--window-bar STYLE` | - | Window bar: `colorful`, `colorful_right`, `rings` |
| `--bar-color COLOR` | `#1e1e1e` | Window bar background |
| `--border-radius N` | `0` | Corner radius in pixels |
| `--margin N` | `0` | Outer margin in pixels |
| `--margin-color COLOR` | `#000000` | Margin color |
| `--padding N` | `0` | Inner padding in pixels |
| `--padding-color COLOR` | `#1e1e1e` | Padding color |
| `--shadow` | off | Enable drop shadow |
| `--theme NAME` | - | Apply a color theme |

## Examples

### Capture a Vim Session

```bash
betamax capture vim myfile.py
# Edit normally, press Ctrl+G when you see something worth capturing
# :wq to exit
```

### Capture with Decorations

```bash
betamax capture --theme dracula --shadow --window-bar colorful htop
```

Produces polished screenshots with a macOS-style window bar, drop shadow, and Dracula color theme.

### Custom Hotkey

If `Ctrl+G` conflicts with your TUI (e.g., vim uses it for file info):

```bash
betamax capture --key C-s vim myfile.py
```

Now `Ctrl+S` triggers capture instead.

### Shell Session with Multiple Captures

```bash
betamax capture
# Run various commands, capture interesting output
# Press Ctrl+G after each command you want to screenshot
# Type 'exit' when done
```

### Set Terminal Size

```bash
betamax capture --cols 120 --rows 40 vim
```

## How It Works

1. `betamax capture` creates a tmux session on a separate socket (`betamax`)
2. Your command runs inside this session with the status bar hidden
3. A tmux key binding (`bind-key -n`) intercepts the hotkey before it reaches your TUI
4. On hotkey press: `tmux capture-pane` grabs the screen, `termshot` renders it as PNG, and optional decorations are applied
5. On exit: the session is cleaned up and file paths are printed

## Configuration

Instead of passing flags every time, use config files and presets.

### Config Files

Betamax searches for config files in this order:

1. `.betamaxrc` in the current directory (searched up to git root)
2. `~/.config/betamax/config` (global)

Format is simple `key=value` with `#` comments:

```bash
# .betamaxrc - project defaults
theme=dracula
shadow=true
window-bar=colorful
border-radius=8
output-dir=./screenshots
```

### Named Presets

Save reusable configurations as presets:

```bash
# ~/.config/betamax/presets/docs.conf
theme=catppuccin-mocha
shadow=true
window-bar=colorful
border-radius=8
padding=10
margin=20
```

Use with `--preset`:

```bash
betamax capture --preset docs vim
```

A config file can also reference a preset as a base:

```bash
# .betamaxrc
preset=docs
theme=nord    # override the preset's theme
```

### Precedence

CLI flags > project `.betamaxrc` > global config > preset > defaults

### Saving Raw Text

Use `--save-text` (or `save-text=true` in config) to keep the raw ANSI text file alongside each PNG. Useful for debugging or re-rendering with different decorations.

## Orphaned Sessions

If your terminal crashes or you force-quit during a capture session, the tmux session persists. On the next run, betamax warns you:

```
Warning: Found orphaned capture session(s):
  betamax-capture-12345
Clean up with: tmux -L betamax kill-session -t <name>
```

To clean up all betamax sessions:

```bash
tmux -L betamax kill-server
```

## Tips

### Ctrl+G in Vim

In vim, `Ctrl+G` shows file info in the status line. If you use this frequently, change the capture key:

```bash
betamax capture --key C-\\ vim    # Use Ctrl+\
betamax capture --key F12 vim     # Use F12
```

### Combine with Themes

Use `--theme` with `--shadow` and `--window-bar` for documentation-ready screenshots:

```bash
betamax capture --theme catppuccin-mocha --shadow --window-bar colorful --border-radius 8 --padding 10
```

### Multiple Captures

You can press the capture hotkey as many times as you want. Each capture gets a unique timestamped filename.

## See Also

- [CLI Reference](/docs/cli-reference#betamax-capture) - Complete option reference
- [Recording Sessions](/docs/guides/recording) - Record keystrokes for playback
- [Recording GIFs](/docs/guides/gif-recording) - Create animated GIF demos
