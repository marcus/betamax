---
sidebar_position: 3
title: Keys File Format
---

# Keys File Format

Keys files are declarative scripts that define terminal interactions for Betamax. Each file is self-describing and contains all the information needed to reproduce a terminal session.

![Betamax keys file workflow](/img/demos/betamax_keysfile.gif)

## Overview

A keys file consists of:
- **Comments** - Lines starting with `#`
- **Settings directives** - Configure terminal dimensions, delays, and dependencies
- **Actions** - Control timing, waiting, capturing, and recording
- **Keys** - Individual keystrokes to send to the terminal

Each line contains exactly one directive, action, or key. Blank lines are ignored.

## Comments and Blank Lines

Comments start with `#` and continue to the end of the line. Use them to document your keys files:

```bash
# This is a comment explaining the next action
@sleep:500

# Navigate through the menu
j
j
Enter
```

Blank lines are ignored and can be used to organize your file into logical sections.

## Settings Directives

Settings at the top of a keys file make it self-describing and reproducible. CLI flags override these values when specified.

| Directive | Description | CLI Override |
|-----------|-------------|--------------|
| `@set:cols:N` | Terminal width in columns | `--cols` |
| `@set:rows:N` | Terminal height in rows | `--rows` |
| `@set:delay:MS` | Default delay between keys in milliseconds | `-d, --delay` |
| `@set:output:DIR` | Output directory for captures | `-o, --output-dir` |
| `@set:timeout:SEC` | Timeout for wait operations in seconds | `-t, --timeout` |
| `@set:shell:PATH` | Shell to use for consistent environment | `--shell` |
| `@set:gif_delay:MS` | Frame duration in GIF playback (default: 200ms) | - |
| `@set:speed:N` | GIF playback speed multiplier, 0.25-4.0 (default: 1.0) | - |
| `@set:loop_offset:MS` | Duplicate first MS of frames at end for seamless looping | - |
| `@set:window_bar:STYLE` | Add macOS-style window bar: `colorful`, `colorful_right`, `rings`, `none` | - |
| `@set:bar_color:RRGGBB` | Window bar background color (6 hex digits, no `#` prefix) | - |
| `@set:bar_height:N` | Window bar height in pixels (default: 30) | - |
| `@set:border_radius:N` | Rounded corner radius in pixels | - |
| `@set:margin:N` | Outer margin in pixels | - |
| `@set:margin_color:RRGGBB` | Margin background color (6 hex digits, no `#` prefix) | - |
| `@set:padding:N` | Inner padding in pixels | - |
| `@set:padding_color:RRGGBB` | Padding background color (6 hex digits, no `#` prefix) | - |

**Note:** Color values use 6 hex digits without the `#` prefix because `#` starts comments in keys files.

### Example Settings Block

```bash
@set:cols:120
@set:rows:40
@set:delay:100
@set:output:./screenshots
@set:shell:/bin/bash
@set:gif_delay:150
@set:speed:1.5

# Decoration settings for polished GIFs
@set:window_bar:colorful
@set:bar_color:282a36
@set:border_radius:8
@set:margin:20
@set:margin_color:1a1a2e
```

## Dependency Checking with @require

The `@require:CMD` directive checks that a command exists in PATH before running the keys file. This allows fast failure with clear error messages.

```bash
@require:termshot    # Required for PNG output
@require:aha         # Required for HTML output
@require:ffmpeg      # Required for GIF recording
```

If the required command is not found, Betamax exits immediately with an error.

## Modular Keys Files with @source

The `@source:PATH` directive imports keys from another file, enabling reusable setup sequences and modular organization.

```bash
# main.keys
@source:common/setup.keys      # Import shared setup
@source:themes/dracula.keys    # Import decoration settings

@record:start
# ... your recording ...
@record:stop:demo.gif
```

### Path Resolution

Paths are resolved relative to the current file's directory:

```
project/
├── demos/
│   └── main.keys          # @source:../common/setup.keys
├── common/
│   └── setup.keys         # Resolves correctly
```

### Features

- **Relative paths**: Resolve from the sourcing file's directory
- **Nested imports**: Sourced files can themselves use `@source`
- **Circular detection**: Betamax detects and reports circular imports with the full import chain
- **Depth limit**: Maximum 10 levels of nesting to prevent runaway imports
- **Settings preservation**: `@set` directives from sourced files are applied

### Example: Shared Setup

```bash
# common/terminal-setup.keys
@set:cols:80
@set:rows:24
@set:delay:80
@require:termshot
@require:ffmpeg
```

```bash
# demos/vim-demo.keys
@source:../common/terminal-setup.keys
@set:gif_delay:150

@sleep:400
@record:start
i
@frame
# ... rest of recording
```

### Error Handling

Betamax provides clear error messages for common issues:

- **File not found**: Shows the full path that couldn't be found
- **Circular import**: Shows the complete import chain (A → B → C → A)
- **Typo detection**: Suggests `@source` if you use `@import`, `@include`, etc.

## Actions

Actions control the flow of execution, timing, and output capture.

| Action | Description |
|--------|-------------|
| `@sleep:MS` | Wait MS milliseconds before continuing |
| `@sleep:MS:capture` | Wait MS milliseconds, capture frames before and after (opt-in for GIF recording) |
| `@wait:PATTERN` | Wait for text pattern to appear in terminal |
| `@wait:/REGEX/` | Wait for regex pattern to match in terminal |
| `@capture` | Capture terminal state to stdout |
| `@capture:NAME.png` | Save screenshot as PNG (requires termshot) |
| `@capture:NAME.html` | Save as HTML with colors (requires aha) |
| `@capture:NAME.txt` | Save as plain text with ANSI codes |
| `@capture:NAME` | Save in all available formats |
| `@record:start` | Start GIF recording session |
| `@record:pause` | Pause frame capture (session continues), auto-captures on resume |
| `@record:resume` | Resume frame capture, capturing current state |
| `@hide` | Hide recording - keys execute but frames not captured |
| `@show` | Show recording - resume capturing frames (no auto-capture) |
| `@frame` | Capture current state as a GIF frame (during recording) |
| `@record:stop:NAME.gif` | Stop recording and save animated GIF |
| `@repeat:N` | Begin a loop that repeats N times |
| `@end` | End the current `@repeat` loop |
| `@pause` | Wait for Enter key (interactive debugging) |

### Wait Patterns

Wait for specific text or patterns before continuing:

```bash
@wait:Ready           # Wait for literal text "Ready"
@wait:/Loading\.+/    # Wait for regex pattern
```

### Capture Examples

```bash
@capture:screenshot.png    # Save PNG only
@capture:output.html       # Save HTML only
@capture:terminal.txt      # Save text with ANSI codes
@capture:demo              # Save demo.png, demo.html, and demo.txt
```

### Loop with @repeat

Use `@repeat:N` and `@end` to repeat a sequence of keys and actions:

```bash
@repeat:5
j
@frame
@end
```

This sends `j` five times, capturing a frame after each press.

## Key Syntax

Keys use tmux send-keys format. Most printable characters are sent literally.

### Literal Keys

Single characters are sent directly:

```bash
a
b
1
2
```

### Special Keys

| Key | Syntax |
|-----|--------|
| Enter | `Enter` |
| Escape | `Escape` |
| Tab | `Tab` |
| Shift+Tab | `BTab` |
| Space | `Space` |
| Backspace | `BSpace` |
| Delete | `DC` |
| Arrow keys | `Up`, `Down`, `Left`, `Right` |
| Home / End | `Home`, `End` |
| Page Up / Down | `PPage`, `NPage` |
| Function keys | `F1`, `F2`, ... `F12` |
| Ctrl+key | `C-c`, `C-v`, `C-x` |
| Alt+key | `M-x`, `M-a` |

### Examples

```bash
Escape          # Press Escape
C-c             # Ctrl+C
M-x             # Alt+X
F1              # Function key F1
```

## Per-Key Timing

Override the default delay for individual keys using the `@MS` suffix:

```
key@MS
```

The number after `@` specifies milliseconds to wait after sending that key.

### Examples

```bash
j@50           # Press j, wait 50ms (fast navigation)
j@50
j@50
Enter@1000     # Press Enter, wait 1 second
```

This is useful for:
- **Rapid navigation** - Use short delays like `@50` for repeated keys
- **Waiting for responses** - Use longer delays like `@1000` after actions that take time

## Complete Example

Here is a complete keys file demonstrating all features:

```bash
# demo-capture.keys
# Captures a screenshot of a TUI application

# Settings - make this file self-describing
@set:cols:120
@set:rows:40
@set:delay:100
@set:output:./screenshots
@set:shell:/bin/bash

# Dependencies - fail fast if missing
@require:termshot

# Wait for application to start
@sleep:500

# Wait for ready indicator
@wait:Ready

# Navigate the menu quickly
j@50
j@50
j@50

# Select item and wait for it to load
Enter@500

# Capture the screenshot
@capture:demo.png

# Exit the application
q
y
```

### GIF Recording Example

```bash
# record-typing.keys
# Records an animated GIF of typing in vim

@set:cols:80
@set:rows:24
@set:delay:80
@set:gif_delay:150

@require:termshot
@require:ffmpeg

# Wait for vim to load
@sleep:400

# Start recording
@record:start

# Type "Hello" with frame after each character
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

# Exit insert mode
Escape
@sleep:300
@frame

# Quit vim
:q!
Enter

# Save the recording
@record:stop:typing-demo.gif
```

### Loop Example

```bash
# scroll-demo.keys
# Demonstrates scrolling with @repeat

@set:cols:80
@set:rows:24
@set:delay:100

@sleep:500
@record:start

# Scroll down 10 times
@repeat:10
j
@frame
@end

# Scroll back up 10 times
@repeat:10
k
@frame
@end

@record:stop:scroll-demo.gif
```
