---
sidebar_position: 6
title: Troubleshooting
---

# Troubleshooting

Common issues and how to resolve them.

## Missing Dependencies

Betamax checks for required tools at startup. If something is missing, you'll see a clear error.

### Required

| Tool | Purpose | Install (macOS) | Install (Linux) |
|------|---------|-----------------|-----------------|
| `tmux` | Headless terminal sessions | `brew install tmux` | `apt install tmux` |
| `bc` | Timing calculations | `brew install bc` | `apt install bc` |
| `python3` | Recording and GIF generation | Included with macOS | `apt install python3` |

### Optional

| Tool | Purpose | Install (macOS) | Install (Linux) |
|------|---------|-----------------|-----------------|
| `termshot` | PNG screenshots | `brew install homeport/tap/termshot` | See [termshot repo](https://github.com/homeport/termshot) |
| `aha` | HTML output | `brew install aha` | `apt install aha` |
| `ffmpeg` | GIF recording | `brew install ffmpeg` | `apt install ffmpeg` |
| `Pillow` | Decoration rendering | `pip install Pillow` | `pip install Pillow` |

**Error examples:**

```
Error: bc is required for betamax timing calculations
  Install with: brew install bc (macOS) or apt install bc (Linux)
```

```
Error: termshot required for GIF recording
Error: ffmpeg required for GIF recording
```

You can also use `@require` in keys files to check for dependencies before execution:

```
@require:jq
@require:curl
```

If a required command is missing:

```
Error: Missing required commands: jq curl
```

## Validation Errors

Betamax validates keys files before execution and reports errors with line numbers. You can also validate without running:

```bash
betamax --validate-only myapp -f demo.keys
```

### Common Validation Errors

**Missing values:**
```
Error: Missing value for cols (line 3: @set:cols:)
```

**Invalid types:**
```
Error: Invalid integer for delay: abc (line 5: @set:delay:abc)
Error: Invalid speed value: fast (must be numeric) (line 7: @set:speed:fast)
```

**Out of range:**
```
Error: Speed must be between 0.25 and 4.0 (got: 10)
Error: shadow_blur must be 0-100 (got: 200)
Error: shadow_opacity must be 0.0-1.0 (got: 2.5)
```

**Invalid colors:**
```
Error: Invalid color format for bar_color: red (expected RRGGBB or #RRGGBB)
```

**Unknown settings:**
```
Error: Unknown setting: colour
```

**Unknown themes:**
```
Error: Unknown theme: darkula (use: dracula, catppuccin-mocha, gruvbox-dark, nord, ...)
```

### Typo Detection

Betamax suggests corrections for misspelled directives:

```
Warning: Unknown directive @slep (did you mean @sleep?)
Warning: Unknown directive @import (did you mean @source?)
```

## @source Import Errors

The `@source` directive imports keys from other files. Several things can go wrong:

**File not found:**
```
Error: @source file not found: ./common/setup.keys
  Referenced from: demo.keys
```

**Circular imports:**
```
Error: Circular @source detected
  File: /path/to/a.keys
  Import chain:
    -> /path/to/a.keys
    -> /path/to/b.keys
    -> /path/to/a.keys (circular)
```

**Depth limit exceeded (max 10 levels):**
```
Error: @source depth limit exceeded (10 levels)
  Circular import? Check: /path/to/deep.keys
```

Source paths are resolved relative to the file containing the `@source` directive.

## @repeat Structure Errors

```
Error: Missing repeat count (line 5: @repeat)
Error: Invalid repeat count: abc (line 5: @repeat:abc)
Error: Repeat count must be positive (line 5: @repeat:0)
Error: Nested @repeat not supported (line 8: @repeat:3)
Error: @end without matching @repeat (line 10: @end)
Error: @repeat on line 5 has no matching @end (line 5: @repeat:3)
```

Betamax does not support nested `@repeat` blocks. To repeat nested sequences, use `@source` to import a file that contains its own `@repeat`.

## tmux Session Issues

### Orphaned Sessions

If betamax is interrupted (e.g. `kill -9`), tmux sessions may be left running. Betamax uses an isolated tmux socket named `betamax`.

**List orphaned sessions:**
```bash
tmux -L betamax list-sessions
```

**Kill all betamax sessions:**
```bash
tmux -L betamax kill-server
```

**Kill a specific session:**
```bash
tmux -L betamax kill-session -t betamax
```

### Session Already Exists

Betamax kills any existing session with the same name before starting a new one. If you use custom session names (`-s`), ensure they don't conflict with other betamax runs.

### Inspecting Sessions

Use `--keep` / `-k` to keep the tmux session alive after betamax finishes:

```bash
betamax -k myapp -f demo.keys
```

Attach to inspect:

```bash
tmux -L betamax attach -t betamax
```

## Signal Handling

Pressing `Ctrl+C` during betamax execution sends SIGINT. Betamax runs with `set -e`, so this will terminate the script. The tmux session should be cleaned up, but if it isn't, see [Orphaned Sessions](#orphaned-sessions) above.

## GIF Recording Issues

### No Frames Captured

```
Error: No frames captured
```

This means `@record:start` was used but no `@frame` directives (or `@sleep` with capture) generated any frames before `@record:stop`. Ensure your keys file includes timing and content between the record start and stop.

### GIF Creation Failed

```
Error: Failed to create GIF
```

Check that `ffmpeg` is installed and working. Also verify that `termshot` is available for capturing individual frames.

### GIF Filename

```
Error: Missing GIF filename for @record:stop
Error: GIF filename must end with .gif
```

The `@record:stop` directive requires a filename: `@record:stop:output.gif`

## Platform Notes

### macOS

- Dependencies are available via Homebrew
- The default shell is zsh; use `--shell /bin/bash` if your keys file assumes bash
- `bc` is included with macOS by default

### Linux

- Install dependencies via your package manager (`apt`, `dnf`, `pacman`, etc.)
- Ensure your terminal supports truecolor (24-bit color) for accurate theme rendering
- If running in a headless environment (CI), tmux works without a display since it runs its own terminal

### Truecolor Support

Themes and color options require a terminal that supports truecolor (24-bit RGB). Most modern terminals do. To test:

```bash
printf "\x1b[38;2;255;100;0mTruecolor test\x1b[0m\n"
```

If you see orange text, your terminal supports truecolor.

## Timeout Errors

```
Error: Timeout waiting for pattern 'Ready'
```

The `--wait` / `-w` pattern wasn't found within the timeout period (default: 30 seconds). Solutions:

- Increase the timeout: `--timeout 60`
- Verify the pattern matches what the application actually prints
- Check that the application starts correctly in tmux

## See Also

- [Getting Started](/docs/intro) - Installation and prerequisites
- [CLI Reference](/docs/cli-reference) - All command-line options
- [Keys File Format](/docs/keys-file-format) - Directive syntax reference
