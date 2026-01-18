---
sidebar_position: 1
title: Getting Started
---

# Getting Started with Betamax

Betamax is a terminal session recorder for TUI applications, using tmux for headless operation.

## Prerequisites

**Required:**
- `tmux` - headless terminal sessions

**Optional (for output formats):**
- `termshot` - PNG screenshots
- `aha` - HTML output
- `ffmpeg` - GIF recording

## Installation

Clone the repository and add to your PATH:

```bash
git clone https://github.com/marcus/betamax ~/code/betamax
export PATH="$HOME/code/betamax:$PATH"
```

Or symlink to a directory already in your PATH:

```bash
ln -s ~/code/betamax/betamax /usr/local/bin/betamax
```

## Installing Dependencies (macOS)

```bash
brew install tmux
brew install homeport/tap/termshot
brew install aha
brew install ffmpeg
```

## Verify Installation

```bash
betamax --help
```

![betamax help](/img/demos/betamax_help.png)

## Your First Recording

### Interactive Recording

Record your terminal session and capture keystrokes with timing:

```bash
betamax record -o demo.keys vim test.txt
```

Type normally, then press `Ctrl+D` or `exit` to stop. Your keystrokes are saved to `demo.keys` with precise timing.

Play it back:

```bash
betamax "vim test.txt" -f demo.keys
```

### Quick Inline Capture

For simple captures, use inline keys:

```bash
betamax "echo 'Hello, Betamax!'" -- @sleep:500 @capture:hello.txt
```

This runs `echo`, waits 500ms, and captures the output to `hello.txt`.

### Screenshot with Wait

Wait for an app to load, then capture:

```bash
betamax "htop" -w "CPU" -- @sleep:1000 @capture:htop.png q
```

![top demo](/img/demos/top_demo.png)

## Next Steps

See the [CLI Reference](/docs/cli-reference) for all options and the keys file format.
