"""
key_mapper.py - Convert terminal escape sequences to betamax key names

Maps raw terminal input bytes to betamax key names like:
- \\x1b[A -> Up
- \\x1b[B -> Down
- \\x7f -> BSpace
- \\r -> Enter
"""

from typing import List, Tuple, Optional
import time


class KeyMapper:
    """Maps raw terminal escape sequences to betamax key names."""

    # Escape sequences mapped to betamax key names (longest first for matching)
    ESCAPE_SEQUENCES = {
        # Ctrl+Arrow keys (common terminal variants)
        b'\x1b[1;5A': 'C-Up',
        b'\x1b[1;5B': 'C-Down',
        b'\x1b[1;5C': 'C-Right',
        b'\x1b[1;5D': 'C-Left',

        # Function keys
        b'\x1b[15~': 'F5',
        b'\x1b[17~': 'F6',
        b'\x1b[18~': 'F7',
        b'\x1b[19~': 'F8',
        b'\x1b[20~': 'F9',
        b'\x1b[21~': 'F10',
        b'\x1b[23~': 'F11',
        b'\x1b[24~': 'F12',

        # Navigation keys
        b'\x1b[5~': 'PPage',
        b'\x1b[6~': 'NPage',
        b'\x1b[2~': 'IC',
        b'\x1b[3~': 'DC',

        # Arrow keys
        b'\x1b[A': 'Up',
        b'\x1b[B': 'Down',
        b'\x1b[C': 'Right',
        b'\x1b[D': 'Left',

        # Home/End (multiple variants)
        b'\x1b[H': 'Home',
        b'\x1b[F': 'End',
        b'\x1bOH': 'Home',
        b'\x1bOF': 'End',

        # Function keys (alternate sequences)
        b'\x1bOP': 'F1',
        b'\x1bOQ': 'F2',
        b'\x1bOR': 'F3',
        b'\x1bOS': 'F4',

        # Backtab
        b'\x1b[Z': 'BTab',
    }

    # Control characters (0x01-0x1a -> C-a through C-z)
    CONTROL_CHARS = {
        i: f'C-{chr(ord("a") + i - 1)}' for i in range(1, 27)
    }

    # Special single-byte keys
    SPECIAL_KEYS = {
        0x7f: 'BSpace',  # DEL
        0x08: 'BSpace',  # Backspace
        0x0d: 'Enter',   # CR
        0x0a: 'Enter',   # LF
        0x09: 'Tab',
        0x20: 'Space',
    }

    # Timeout for escape key detection (seconds)
    ESCAPE_TIMEOUT = 0.05  # 50ms

    def __init__(self):
        """Initialize the key mapper with an empty buffer."""
        self._buffer = b''
        self._last_read_time = 0.0

    def parse_input(self, data: bytes, timeout_occurred: bool = False) -> List[Tuple[str, bytes]]:
        """
        Parse raw input bytes and return list of (key_name, raw_bytes) tuples.

        Args:
            data: Raw bytes from terminal input
            timeout_occurred: True if this call is due to timeout (flush buffer)

        Returns:
            List of (key_name, raw_bytes) tuples
        """
        self._buffer += data
        results = []

        while self._buffer:
            # Check if buffer starts with escape
            if self._buffer[0:1] == b'\x1b':
                # Try to match escape sequences (longest first)
                matched = False
                for seq, key_name in sorted(
                    self.ESCAPE_SEQUENCES.items(),
                    key=lambda x: len(x[0]),
                    reverse=True
                ):
                    if self._buffer.startswith(seq):
                        results.append((key_name, seq))
                        self._buffer = self._buffer[len(seq):]
                        matched = True
                        break

                if not matched:
                    # Check for Alt+key (ESC followed by printable)
                    if len(self._buffer) >= 2:
                        next_byte = self._buffer[1:2]
                        if 0x20 <= next_byte[0] <= 0x7e:
                            # Alt+printable character
                            key_name = f'M-{chr(next_byte[0])}'
                            results.append((key_name, self._buffer[:2]))
                            self._buffer = self._buffer[2:]
                            matched = True

                if not matched:
                    # Could be incomplete sequence or bare escape
                    if len(self._buffer) == 1:
                        if timeout_occurred:
                            # Timeout: treat as bare Escape
                            results.append(('Escape', b'\x1b'))
                            self._buffer = b''
                        else:
                            # Wait for more data
                            break
                    else:
                        # Unknown sequence - output as Escape + rest
                        results.append(('Escape', b'\x1b'))
                        self._buffer = self._buffer[1:]

            else:
                # Single byte handling
                byte_val = self._buffer[0]

                if byte_val in self.SPECIAL_KEYS:
                    key_name = self.SPECIAL_KEYS[byte_val]
                elif byte_val in self.CONTROL_CHARS:
                    key_name = self.CONTROL_CHARS[byte_val]
                elif 0x20 <= byte_val <= 0x7e:
                    # Printable ASCII
                    key_name = chr(byte_val)
                else:
                    # Unknown byte - output as hex
                    key_name = f'0x{byte_val:02x}'

                results.append((key_name, self._buffer[0:1]))
                self._buffer = self._buffer[1:]

        return results

    def flush(self) -> List[Tuple[str, bytes]]:
        """
        Flush any remaining buffered input, treating incomplete sequences as-is.

        Returns:
            List of (key_name, raw_bytes) tuples
        """
        return self.parse_input(b'', timeout_occurred=True)

    def has_pending(self) -> bool:
        """Check if there's pending data in the buffer."""
        return len(self._buffer) > 0


def key_name_to_tmux(key_name: str) -> str:
    """
    Convert a key name to tmux send-keys format if needed.

    Most key names are already compatible, but some need adjustment.
    """
    # tmux uses the same names for most keys
    return key_name
