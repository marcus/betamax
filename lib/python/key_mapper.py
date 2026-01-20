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

from .response_filter import ResponseFilter


class KeyMapper:
    """Maps raw terminal escape sequences to betamax key names."""

    # Escape sequences mapped to betamax key names (longest first for matching)
    # Modifier codes: 2=Shift, 3=Alt, 4=Alt+Shift, 5=Ctrl, 6=Ctrl+Shift, 7=Ctrl+Alt, 8=Ctrl+Alt+Shift
    ESCAPE_SEQUENCES = {
        # Shift+Arrow keys (modifier 2)
        b'\x1b[1;2A': 'S-Up',
        b'\x1b[1;2B': 'S-Down',
        b'\x1b[1;2C': 'S-Right',
        b'\x1b[1;2D': 'S-Left',

        # Alt+Arrow keys (modifier 3)
        b'\x1b[1;3A': 'M-Up',
        b'\x1b[1;3B': 'M-Down',
        b'\x1b[1;3C': 'M-Right',
        b'\x1b[1;3D': 'M-Left',

        # Ctrl+Arrow keys (modifier 5)
        b'\x1b[1;5A': 'C-Up',
        b'\x1b[1;5B': 'C-Down',
        b'\x1b[1;5C': 'C-Right',
        b'\x1b[1;5D': 'C-Left',

        # Ctrl+Shift+Arrow keys (modifier 6)
        b'\x1b[1;6A': 'C-S-Up',
        b'\x1b[1;6B': 'C-S-Down',
        b'\x1b[1;6C': 'C-S-Right',
        b'\x1b[1;6D': 'C-S-Left',

        # Alt+Shift+Arrow keys (modifier 4)
        b'\x1b[1;4A': 'M-S-Up',
        b'\x1b[1;4B': 'M-S-Down',
        b'\x1b[1;4C': 'M-S-Right',
        b'\x1b[1;4D': 'M-S-Left',

        # Ctrl+Alt+Arrow keys (modifier 7)
        b'\x1b[1;7A': 'C-M-Up',
        b'\x1b[1;7B': 'C-M-Down',
        b'\x1b[1;7C': 'C-M-Right',
        b'\x1b[1;7D': 'C-M-Left',

        # Function keys (base - SS3 style for F1-F4)
        b'\x1bOP': 'F1',
        b'\x1bOQ': 'F2',
        b'\x1bOR': 'F3',
        b'\x1bOS': 'F4',

        # Function keys (CSI style F5-F12)
        b'\x1b[15~': 'F5',
        b'\x1b[17~': 'F6',
        b'\x1b[18~': 'F7',
        b'\x1b[19~': 'F8',
        b'\x1b[20~': 'F9',
        b'\x1b[21~': 'F10',
        b'\x1b[23~': 'F11',
        b'\x1b[24~': 'F12',

        # Shift+Function keys (modifier 2) - F1-F4 use CSI 1;2X format
        b'\x1b[1;2P': 'S-F1',
        b'\x1b[1;2Q': 'S-F2',
        b'\x1b[1;2R': 'S-F3',
        b'\x1b[1;2S': 'S-F4',
        b'\x1b[15;2~': 'S-F5',
        b'\x1b[17;2~': 'S-F6',
        b'\x1b[18;2~': 'S-F7',
        b'\x1b[19;2~': 'S-F8',
        b'\x1b[20;2~': 'S-F9',
        b'\x1b[21;2~': 'S-F10',
        b'\x1b[23;2~': 'S-F11',
        b'\x1b[24;2~': 'S-F12',

        # Alt+Function keys (modifier 3)
        b'\x1b[1;3P': 'M-F1',
        b'\x1b[1;3Q': 'M-F2',
        b'\x1b[1;3R': 'M-F3',
        b'\x1b[1;3S': 'M-F4',
        b'\x1b[15;3~': 'M-F5',
        b'\x1b[17;3~': 'M-F6',
        b'\x1b[18;3~': 'M-F7',
        b'\x1b[19;3~': 'M-F8',
        b'\x1b[20;3~': 'M-F9',
        b'\x1b[21;3~': 'M-F10',
        b'\x1b[23;3~': 'M-F11',
        b'\x1b[24;3~': 'M-F12',

        # Ctrl+Function keys (modifier 5)
        b'\x1b[1;5P': 'C-F1',
        b'\x1b[1;5Q': 'C-F2',
        b'\x1b[1;5R': 'C-F3',
        b'\x1b[1;5S': 'C-F4',
        b'\x1b[15;5~': 'C-F5',
        b'\x1b[17;5~': 'C-F6',
        b'\x1b[18;5~': 'C-F7',
        b'\x1b[19;5~': 'C-F8',
        b'\x1b[20;5~': 'C-F9',
        b'\x1b[21;5~': 'C-F10',
        b'\x1b[23;5~': 'C-F11',
        b'\x1b[24;5~': 'C-F12',

        # Ctrl+Shift+Function keys (modifier 6)
        b'\x1b[1;6P': 'C-S-F1',
        b'\x1b[1;6Q': 'C-S-F2',
        b'\x1b[1;6R': 'C-S-F3',
        b'\x1b[1;6S': 'C-S-F4',
        b'\x1b[15;6~': 'C-S-F5',
        b'\x1b[17;6~': 'C-S-F6',
        b'\x1b[18;6~': 'C-S-F7',
        b'\x1b[19;6~': 'C-S-F8',
        b'\x1b[20;6~': 'C-S-F9',
        b'\x1b[21;6~': 'C-S-F10',
        b'\x1b[23;6~': 'C-S-F11',
        b'\x1b[24;6~': 'C-S-F12',

        # Alt+Shift+Function keys (modifier 4)
        b'\x1b[1;4P': 'M-S-F1',
        b'\x1b[1;4Q': 'M-S-F2',
        b'\x1b[1;4R': 'M-S-F3',
        b'\x1b[1;4S': 'M-S-F4',
        b'\x1b[15;4~': 'M-S-F5',
        b'\x1b[17;4~': 'M-S-F6',
        b'\x1b[18;4~': 'M-S-F7',
        b'\x1b[19;4~': 'M-S-F8',
        b'\x1b[20;4~': 'M-S-F9',
        b'\x1b[21;4~': 'M-S-F10',
        b'\x1b[23;4~': 'M-S-F11',
        b'\x1b[24;4~': 'M-S-F12',

        # Navigation keys
        b'\x1b[5~': 'PPage',
        b'\x1b[6~': 'NPage',
        b'\x1b[2~': 'IC',
        b'\x1b[3~': 'DC',

        # Navigation with modifiers
        b'\x1b[5;5~': 'C-PPage',
        b'\x1b[6;5~': 'C-NPage',
        b'\x1b[2;5~': 'C-IC',
        b'\x1b[3;5~': 'C-DC',
        b'\x1b[5;3~': 'M-PPage',
        b'\x1b[6;3~': 'M-NPage',
        b'\x1b[2;3~': 'M-IC',
        b'\x1b[3;3~': 'M-DC',

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
        b'\x1b[1~': 'Home',  # Alternative Home
        b'\x1b[4~': 'End',   # Alternative End

        # Home/End with modifiers
        b'\x1b[1;5H': 'C-Home',
        b'\x1b[1;5F': 'C-End',
        b'\x1b[1;3H': 'M-Home',
        b'\x1b[1;3F': 'M-End',
        b'\x1b[1;2H': 'S-Home',
        b'\x1b[1;2F': 'S-End',

        # Bracketed paste mode markers
        b'\x1b[200~': 'PasteStart',
        b'\x1b[201~': 'PasteEnd',

        # Application keypad mode (numpad keys)
        b'\x1bOp': 'KP0',
        b'\x1bOq': 'KP1',
        b'\x1bOr': 'KP2',
        b'\x1bOs': 'KP3',
        b'\x1bOt': 'KP4',
        b'\x1bOu': 'KP5',
        b'\x1bOv': 'KP6',
        b'\x1bOw': 'KP7',
        b'\x1bOx': 'KP8',
        b'\x1bOy': 'KP9',
        b'\x1bOk': 'KP+',
        b'\x1bOm': 'KP-',
        b'\x1bOj': 'KP*',
        b'\x1bOo': 'KP/',
        b'\x1bOn': 'KP.',
        b'\x1bOM': 'KPEnter',

        # Application cursor mode arrows (rarely used, but some apps enable it)
        b'\x1bOA': 'Up',
        b'\x1bOB': 'Down',
        b'\x1bOC': 'Right',
        b'\x1bOD': 'Left',

        # Backtab
        b'\x1b[Z': 'BTab',

        # Focus events (terminal sends these when focus changes)
        b'\x1b[I': 'FocusIn',
        b'\x1b[O': 'FocusOut',
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

    def __init__(self, filter_responses: bool = False, debug_filter: bool = False):
        """
        Initialize the key mapper with an empty buffer.

        Args:
            filter_responses: If True, pre-filter terminal responses before parsing
            debug_filter: If True, log filtered sequences (requires filter_responses)
        """
        self._buffer = b''
        self._last_read_time = 0.0
        # Pre-sort escape sequences once (longest first for matching)
        self._sorted_sequences = sorted(
            self.ESCAPE_SEQUENCES.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        # Response filtering
        self._filter_responses = filter_responses
        self._response_filter = ResponseFilter(debug=debug_filter) if filter_responses else None

    def parse_input(self, data: bytes, timeout_occurred: bool = False) -> List[Tuple[str, bytes]]:
        """
        Parse raw input bytes and return list of (key_name, raw_bytes) tuples.

        Args:
            data: Raw bytes from terminal input
            timeout_occurred: True if this call is due to timeout (flush buffer)

        Returns:
            List of (key_name, raw_bytes) tuples
        """
        # Pre-filter terminal responses if enabled
        if self._filter_responses and self._response_filter:
            data = self._response_filter.filter(data)

        self._buffer += data
        results = []

        while self._buffer:
            # Check if buffer starts with escape
            if self._buffer[0:1] == b'\x1b':
                # Try to match escape sequences (pre-sorted, longest first)
                matched = False
                for seq, key_name in self._sorted_sequences:
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
                    results.append((key_name, self._buffer[0:1]))
                    self._buffer = self._buffer[1:]
                elif byte_val in self.CONTROL_CHARS:
                    key_name = self.CONTROL_CHARS[byte_val]
                    results.append((key_name, self._buffer[0:1]))
                    self._buffer = self._buffer[1:]
                elif 0x20 <= byte_val <= 0x7e:
                    # Printable ASCII
                    key_name = chr(byte_val)
                    results.append((key_name, self._buffer[0:1]))
                    self._buffer = self._buffer[1:]
                elif byte_val >= 0x80:
                    # UTF-8 multi-byte sequence
                    try:
                        # Determine sequence length from first byte
                        if byte_val & 0b11100000 == 0b11000000:
                            length = 2  # 110xxxxx = 2-byte sequence
                        elif byte_val & 0b11110000 == 0b11100000:
                            length = 3  # 1110xxxx = 3-byte sequence
                        elif byte_val & 0b11111000 == 0b11110000:
                            length = 4  # 11110xxx = 4-byte sequence
                        else:
                            raise ValueError('Invalid UTF-8 start byte')

                        if len(self._buffer) < length:
                            # Incomplete sequence, wait for more data
                            break

                        utf8_bytes = self._buffer[:length]
                        char = utf8_bytes.decode('utf-8', errors='strict')
                        results.append((char, utf8_bytes))
                        self._buffer = self._buffer[length:]
                    except (ValueError, UnicodeDecodeError):
                        # Invalid UTF-8, output as hex
                        key_name = f'0x{byte_val:02x}'
                        results.append((key_name, self._buffer[0:1]))
                        self._buffer = self._buffer[1:]
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

    def get_filtered_responses(self) -> list:
        """
        Get the log of filtered terminal responses.

        Only populated when filter_responses=True and debug_filter=True.

        Returns:
            List of (type, sequence) tuples
        """
        if self._response_filter:
            return self._response_filter.get_filtered_log()
        return []


def key_name_to_tmux(key_name: str) -> str:
    """
    Convert a key name to tmux send-keys format if needed.

    Most key names are already compatible, but some need adjustment.
    """
    # tmux uses the same names for most keys
    return key_name
