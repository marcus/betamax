"""
response_filter.py - Filter terminal response sequences from recorded input

Terminal applications often query the terminal for information (cursor position,
device attributes, colors). The terminal responds with escape sequences that
pollute recordings. This module filters those responses before keystroke parsing.

VHS-inspired approach: Pre-filter raw input using regex patterns to remove
terminal responses, keeping only actual user input.
"""

import re
import logging
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)


class ResponseFilter:
    """
    Filters terminal response sequences from raw input bytes.

    Terminal responses include:
    - Cursor position reports (CPR): ESC[row;colR
    - Device attribute responses (DA): ESC[?...c
    - OSC responses: ESC]N;...ST (color queries, title responses)
    - Primary/secondary device attribute queries
    """

    # Compiled regex patterns for terminal responses
    # Using bytes patterns for direct matching on raw input
    RESPONSE_PATTERNS = [
        # Cursor Position Report: ESC[row;colR
        # Example: ESC[24;80R (cursor at row 24, col 80)
        (re.compile(rb'\x1b\[\d+;\d+R'), 'CPR'),

        # Primary Device Attributes response: ESC[?...c
        # Example: ESC[?64;1;2;6;9;15;18;21;22c
        (re.compile(rb'\x1b\[\?[\d;]*c'), 'DA1'),

        # Secondary Device Attributes response: ESC[>...c
        # Example: ESC[>0;136;0c (VT100, firmware version)
        (re.compile(rb'\x1b\[>[\d;]*c'), 'DA2'),

        # Tertiary Device Attributes response: ESC[=...c
        (re.compile(rb'\x1b\[=[\d;]*c'), 'DA3'),

        # OSC response with BEL terminator: ESC]N;...BEL
        # Example: ESC]11;rgb:0000/0000/0000BEL (background color)
        (re.compile(rb'\x1b\]\d+;[^\x07\x1b]*\x07'), 'OSC-BEL'),

        # OSC response with ST terminator: ESC]N;...ESC\
        # Example: ESC]11;rgb:ffff/ffff/ffffESC\
        (re.compile(rb'\x1b\]\d+;[^\x07\x1b]*\x1b\\'), 'OSC-ST'),

        # DECRPM (DEC Report Mode): ESC[?N;M$y
        # Example: ESC[?2026;2$y (synchronized output mode status)
        (re.compile(rb'\x1b\[\?\d+;\d+\$y'), 'DECRPM'),

        # DSR responses - Operating Status Report: ESC[0n
        (re.compile(rb'\x1b\[0n'), 'DSR-OK'),

        # DSR responses - Device Status Report error: ESC[3n
        (re.compile(rb'\x1b\[3n'), 'DSR-ERR'),

        # DECXCPR - Extended Cursor Position Report: ESC[?row;col;pageR
        (re.compile(rb'\x1b\[\?\d+;\d+;\d+R'), 'DECXCPR'),

        # XTWINOPS responses (window operations): ESC[4;height;widtht etc
        (re.compile(rb'\x1b\[\d+;\d+;\d+t'), 'XTWINOPS'),

        # XTWINOPS text area size: ESC[8;rows;colst
        (re.compile(rb'\x1b\[8;\d+;\d+t'), 'XTWINOPS-SIZE'),
    ]

    def __init__(self, debug: bool = False):
        """
        Initialize the response filter.

        Args:
            debug: If True, log filtered sequences for troubleshooting
        """
        self.debug = debug
        self._filtered_log: List[Tuple[str, bytes]] = []

    def filter(self, data: bytes) -> bytes:
        """
        Filter terminal response sequences from raw input.

        Args:
            data: Raw bytes from terminal input

        Returns:
            Filtered bytes with terminal responses removed
        """
        if not data:
            return data

        result = data

        for pattern, name in self.RESPONSE_PATTERNS:
            matches = list(pattern.finditer(result))
            for match in reversed(matches):  # Reverse to preserve indices
                filtered_seq = match.group()
                if self.debug:
                    logger.debug(f"Filtered {name}: {filtered_seq!r}")
                    self._filtered_log.append((name, filtered_seq))
                # Remove the matched sequence
                result = result[:match.start()] + result[match.end():]

        return result

    def filter_with_log(self, data: bytes) -> Tuple[bytes, List[Tuple[str, bytes]]]:
        """
        Filter terminal responses and return what was filtered.

        Args:
            data: Raw bytes from terminal input

        Returns:
            Tuple of (filtered_bytes, list of (type, sequence) tuples)
        """
        self._filtered_log = []
        old_debug = self.debug
        self.debug = True

        result = self.filter(data)

        self.debug = old_debug
        return result, self._filtered_log.copy()

    def get_filtered_log(self) -> List[Tuple[str, bytes]]:
        """
        Get the log of filtered sequences from the last filter() call.

        Only populated when debug=True.

        Returns:
            List of (type, sequence) tuples
        """
        return self._filtered_log.copy()

    def clear_log(self):
        """Clear the filtered sequence log."""
        self._filtered_log = []


def filter_terminal_responses(data: bytes, debug: bool = False) -> bytes:
    """
    Convenience function to filter terminal responses from raw input.

    Args:
        data: Raw bytes from terminal input
        debug: If True, log filtered sequences

    Returns:
        Filtered bytes with terminal responses removed
    """
    return ResponseFilter(debug=debug).filter(data)
