---
sidebar_position: 2
title: Recording Sessions
---

# Recording Terminal Sessions

Record your terminal sessions interactively with `betamax record`. This captures every keystroke with precise timing, generating `.keys` files that can be played back for demos, documentation, or GIF creation.

## Overview

Instead of manually writing keys files, you can record your actual terminal session:

```bash
betamax record -o demo.keys vim test.txt
```

Type normally, then press `Ctrl+D` or type `exit` to stop. Your keystrokes are saved with timing information for natural playback.

## Basic Recording

### Record a Session

```bash
betamax record -o session.keys <command>
```

This launches `<command>` in an interactive terminal. Everything you type is captured.

### Stop Recording

- Press `Ctrl+D` (end of input)
- Type `exit` (if running a shell)
- The recording also stops at `--max-duration` (default: 5 minutes)

### Play Back

```bash
betamax "<command>" -f session.keys
```

## Recording Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output FILE` | `recording.keys` | Output `.keys` file path |
| `--gif FILE` | - | Generate GIF after recording |
| `--auto-frame` | - | Add `@frame` after every keystroke |
| `--frame-key KEY` | `C-g` | Hotkey to mark frames manually |
| `--delay MS` | - | Use fixed delay (ignore timing) |
| `--min-delay MS` | `50` | Minimum delay threshold |
| `--max-delay MS` | `2000` | Maximum delay cap |
| `--cols COLS` | current | Terminal width |
| `--rows ROWS` | current | Terminal height |
| `--max-duration SEC` | `300` | Max recording time (5 min) |

## Recording with GIF Output

Generate a GIF directly from your recording:

```bash
betamax record --gif demo.gif --auto-frame htop
```

This:
1. Records your session to a `.keys` file
2. Wraps it with `@record:start` and `@record:stop` directives
3. Adds `@frame` after each keystroke (with `--auto-frame`)
4. Generates the GIF automatically

### Manual Frame Marking

For more control over which frames appear in your GIF, use `--frame-key`:

```bash
betamax record --gif demo.gif --frame-key C-g vim test.txt
```

Press `Ctrl+G` during recording to mark important frames. Only marked frames appear in the GIF.

## Timing Control

### Measured Timing (Default)

By default, the recorder captures the actual time between your keystrokes. This produces natural-feeling playback that matches your typing rhythm.

### Fixed Timing

Use `--delay` to ignore measured timing and use a constant delay:

```bash
betamax record --delay 100 -o demo.keys vim
```

All keys play back with 100ms between them.

### Delay Thresholds

Fine-tune timing capture:

```bash
betamax record --min-delay 30 --max-delay 1500 -o demo.keys vim
```

- `--min-delay`: Delays shorter than this become zero (for rapid typing)
- `--max-delay`: Delays longer than this are clamped (for pauses)

Long pauses (≥500ms) are automatically converted to `@sleep` directives.

## What Gets Recorded

### Captured

- All printable characters
- Special keys: `Enter`, `Escape`, `Tab`, `Backspace`, `Delete`
- Arrow keys: `Up`, `Down`, `Left`, `Right`
- Navigation: `Home`, `End`, `PPage`, `NPage`
- Function keys: `F1`-`F12`
- Modifier combinations: `C-a`, `M-x`, `C-S-Left`, etc.
- UTF-8 characters (emojis, international text)

### Filtered Out

- Terminal escape sequences (device queries, cursor reports)
- Terminal noise from the application
- The frame-key itself (only marks frames, not recorded)

## Generated File Format

A recorded `.keys` file looks like:

```bash
# Command: vim test.txt
# Duration: 23s | Keystrokes: 45

@set:cols:120
@set:rows:30
@set:delay:85

i@50
"Hello, world!"
Escape
@sleep:800
":wq"
Enter
```

### Timing Annotations

- `key@MS` - This key had a specific delay (e.g., `j@120` = 120ms before 'j')
- `@sleep:MS` - Long pause (automatically inserted for delays ≥500ms)
- `@set:delay:MS` - Median delay, used as default for unmarked keys

## Examples

### Record a Vim Session

```bash
betamax record -o vim_demo.keys vim test.txt
# Type your demo, then :wq or Ctrl+D
```

### Record htop with Auto-GIF

```bash
betamax record --gif htop_demo.gif --auto-frame htop
# Navigate around, then q to quit
```

### Record with Custom Terminal Size

```bash
betamax record --cols 100 --rows 30 -o demo.keys bash
```

### Record with Manual Frame Marking

```bash
betamax record --gif tutorial.gif --frame-key C-f -o tutorial.keys vim
# Press Ctrl+F at each step you want captured
```

### Quick Recording with Time Limit

```bash
betamax record --max-duration 60 -o quick.keys myapp
# Recording stops after 1 minute
```

## Tips

### Use Auto-Frame for Typing Demos

When demonstrating typing, `--auto-frame` captures every character for a smooth animation.

### Use Manual Frames for Navigation

When demonstrating menu navigation or complex interactions, manually mark frames at key points.

### Set Terminal Size Explicitly

For reproducible recordings, always specify `--cols` and `--rows`:

```bash
betamax record --cols 80 --rows 24 -o demo.keys vim
```

### Review Before Generating GIF

Record without `--gif` first, review the `.keys` file, then generate:

```bash
# Record
betamax record -o demo.keys vim test.txt

# Review (edit if needed)
cat demo.keys

# Generate GIF
betamax "vim test.txt" -f demo.keys
```

### Edit the Keys File

The `.keys` file is plain text. You can:
- Remove mistakes
- Adjust timing
- Add `@frame` directives manually
- Insert `@sleep` for emphasis

## See Also

- [CLI Reference](/docs/cli-reference#betamax-record) - Complete option reference
- [Recording GIFs](/docs/guides/gif-recording) - GIF-specific directives and tips
- [Keys File Format](/docs/keys-file-format) - All directives and syntax
