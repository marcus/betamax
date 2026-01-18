# Betamax Interactive Recording Feature

## Overview

This feature allows users to interactively record their terminal sessions and automatically generate betamax-compatible `.keys` files. Instead of manually writing keys files, users can:

1. Start a recording session
2. Interact naturally (open vim, type, run commands)
3. End the session
4. Get a `.keys` file ready for betamax playback/GIF generation

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           User's Terminal                                │
│  $ betamax record -o demo.keys vim test.txt                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       betamax-record (Python)                            │
│  ┌────────────┐    ┌──────────────┐    ┌───────────────────────────┐   │
│  │  stdin     │───▶│ Input Logger │───▶│ PTY Master (write side)   │   │
│  └────────────┘    │ + Converter  │    └───────────────────────────┘   │
│                    └──────────────┘                 │                   │
│  ┌────────────┐                                     ▼                   │
│  │  stdout    │◀──────────────────────────────────────────────────────  │
│  └────────────┘                         PTY Slave → tmux/shell/vim      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Output: demo.keys                               │
│  @set:cols:80                                                            │
│  @set:rows:24                                                            │
│  @set:delay:100                                                          │
│  @record:start                                                           │
│  i                                                                       │
│  @frame                                                                  │
│  H   # ... captured keystrokes with timing                               │
│  @record:stop:demo.gif                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. betamax-record (Python Script)
**Location**: `bin/betamax-record`

A Python script that:
- Uses the `pty` module to create a pseudo-terminal
- Intercepts all input, logs it with timestamps
- Forwards input/output transparently to the user
- Converts raw escape sequences to betamax key names
- Generates a `.keys` file on exit

### 2. Escape Sequence Mapper
**Location**: `lib/key_mapper.py`

Maps raw terminal bytes/sequences to betamax key names:
- `\x1b[A` → `Up`
- `\x1b[B` → `Down`
- `\x1b[C` → `Right`
- `\x1b[D` → `Left`
- `\x1b` (alone) → `Escape`
- `\x7f` or `\x08` → `BSpace`
- `\r` → `Enter`
- `\t` → `Tab`
- `\x01`-`\x1a` → `C-a` through `C-z`
- `\x1b[1;5A` → `C-Up` (Ctrl+Up)
- `\x1bOP` → `F1`, etc.

### 3. Keys File Generator
**Location**: `lib/keys_generator.py`

Converts logged keystrokes to `.keys` format:
- Adds timing via `@sleep` or per-key timing (`key@ms`)
- Optionally adds `@frame` after each keystroke (for GIF mode)
- Wraps in `@record:start`/`@record:stop` if GIF output requested
- Adds `@set:` directives for terminal dimensions

### 4. CLI Integration
**Location**: `betamax` (bash wrapper update)

Add a `record` subcommand:
```bash
betamax record [options] [command]
```

## User Experience

### Basic Recording
```bash
# Record a vim session
$ betamax record -o demo.keys vim test.txt
Recording started. Press Ctrl+D or exit to stop.
[user interacts with vim]
Recording saved to demo.keys (127 keystrokes, 45.3s)

# Play back to generate GIF
$ betamax vim test.txt -f demo.keys
```

### One-Step GIF Recording
```bash
# Record and auto-generate GIF
$ betamax record --gif demo.gif vim test.txt
Recording started. Press Ctrl+D or exit to stop.
[user interacts with vim]
Recording complete. Generating GIF...
Saved: demo.gif (127 frames, 45.3s)
```

### Recording with Frame Control
```bash
# Use Ctrl+G to mark frames during recording
$ betamax record --frame-key C-g -o demo.keys vim test.txt
Recording started. Press Ctrl+G to mark frames. Ctrl+D to stop.
[user presses Ctrl+G at key moments]
Recording saved to demo.keys (127 keystrokes, 15 frames)
```

### Default Behaviors

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output` | `recording.keys` | Output file name |
| `--gif` | (none) | Also generate GIF after recording |
| `--auto-frame` | false | Add @frame after every keystroke |
| `--frame-key` | `C-g` | Hotkey to manually mark frames |
| `--delay` | measured | Use actual timing vs fixed delay |
| `--min-delay` | 50ms | Minimum delay between keys |
| `--max-delay` | 2000ms | Cap long pauses |
| `--cols` | current | Terminal width |
| `--rows` | current | Terminal height |

## Special Keys Mapping

| Terminal Sequence | Betamax Key |
|-------------------|-------------|
| `\x1b[A` | `Up` |
| `\x1b[B` | `Down` |
| `\x1b[C` | `Right` |
| `\x1b[D` | `Left` |
| `\x1b[H` or `\x1bOH` | `Home` |
| `\x1b[F` or `\x1bOF` | `End` |
| `\x1b[5~` | `PPage` |
| `\x1b[6~` | `NPage` |
| `\x1b[2~` | `IC` (Insert) |
| `\x1b[3~` | `DC` (Delete) |
| `\x1bOP` | `F1` |
| `\x1bOQ` | `F2` |
| `\x1bOR` | `F3` |
| `\x1bOS` | `F4` |
| `\x1b[15~` | `F5` |
| `\x1b[17~` | `F6` |
| `\x1b[18~` | `F7` |
| `\x1b[19~` | `F8` |
| `\x1b[20~` | `F9` |
| `\x1b[21~` | `F10` |
| `\x1b[23~` | `F11` |
| `\x1b[24~` | `F12` |
| `\x1b` (alone, 50ms timeout) | `Escape` |
| `\x7f` | `BSpace` |
| `\r` | `Enter` |
| `\t` | `Tab` |
| `\x1b[Z` | `BTab` |
| ` ` (space) | `Space` |
| `\x01`-`\x1a` | `C-a` to `C-z` |
| `\x1b` + char | `M-{char}` (Alt) |

## Implementation Details

### Python PTY Recording

```python
#!/usr/bin/env python3
"""betamax-record: Interactive terminal session recorder"""

import pty
import os
import sys
import select
import tty
import termios
import time

class TerminalRecorder:
    def __init__(self, output_file, command):
        self.output_file = output_file
        self.command = command
        self.keystrokes = []  # (timestamp, raw_bytes, key_name)
        self.start_time = None

    def record(self):
        # Save terminal state
        old_tty = termios.tcgetattr(sys.stdin)
        try:
            # Set raw mode
            tty.setraw(sys.stdin)

            # Fork pty
            pid, master_fd = pty.fork()

            if pid == 0:  # Child
                os.execvp(self.command[0], self.command)
            else:  # Parent
                self.start_time = time.time()
                self._copy_with_logging(master_fd)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, old_tty)

    def _copy_with_logging(self, master_fd):
        while True:
            r, _, _ = select.select([sys.stdin, master_fd], [], [])

            if sys.stdin in r:
                data = os.read(sys.stdin.fileno(), 1024)
                if not data:
                    break
                # Log the input
                self._log_input(data)
                # Forward to pty
                os.write(master_fd, data)

            if master_fd in r:
                data = os.read(master_fd, 1024)
                if not data:
                    break
                # Forward output to user
                os.write(sys.stdout.fileno(), data)
```

### Escape Sequence Parsing

The recorder buffers input and parses escape sequences:

1. Read bytes into buffer
2. If starts with `\x1b`, wait up to 50ms for more bytes
3. Match against known sequences (longest match first)
4. Convert to key name or fall back to raw character

### Timing Strategy

- Record actual time delta between keystrokes
- On export, optionally:
  - Use actual timing with per-key `@sleep` or `key@ms`
  - Clamp to min/max range
  - Use fixed delay (ignore recorded timing)

## File Structure

```
betamax/
├── betamax                    # Main entry (updated)
├── bin/
│   └── betamax-record         # Python recording script
├── lib/
│   ├── ...                    # Existing bash modules
│   └── python/
│       ├── __init__.py
│       ├── recorder.py        # PTY recording logic
│       ├── key_mapper.py      # Escape sequence → key name
│       └── keys_generator.py  # Generate .keys file
└── test/
    ├── ...                    # Existing tests
    └── test_recorder.py       # Recording tests
```

## Testing Strategy

1. **Unit tests for key_mapper.py**: Test all escape sequence conversions
2. **Unit tests for keys_generator.py**: Test .keys file generation
3. **Integration tests**: Record a session, replay with betamax, verify output
4. **Manual testing**: Interactive recording with vim, htop, etc.

## Future Enhancements

1. **Live preview**: Show the recording playing back in a split pane
2. **Edit mode**: Interactive editor for the captured keystrokes
3. **Multiple format export**: Export to asciinema format as well
4. **Recording resume**: Append to existing .keys file
5. **Scrubbing UI**: Replay with ability to trim start/end
