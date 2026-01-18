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

## Your First Recording

Capture a simple terminal session inline:

```bash
betamax "echo 'Hello, Betamax!'" -- @sleep:500 @capture:hello.txt
```

This runs `echo`, waits 500ms, and captures the output to `hello.txt`.

For more complex workflows, use a keys file:

```bash
betamax "htop" -w "CPU" -- @sleep:1000 @capture:htop.png q
```

## Next Steps

See the [CLI Reference](/docs/cli-reference) for all options and the keys file format.
