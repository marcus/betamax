"""
recorder.py - PTY-based terminal session recorder

Uses pseudo-terminals to intercept and log all keystrokes during an
interactive terminal session.
"""

import pty
import os
import sys
import select
import tty
import termios
import time
import signal
import struct
import fcntl
from typing import List, Tuple, Optional, Callable

from .key_mapper import KeyMapper


class TerminalRecorder:
    """
    Records terminal sessions by intercepting input through a PTY.

    Usage:
        recorder = TerminalRecorder('output.keys', ['vim', 'test.txt'], options)
        recorder.record()
        keystrokes = recorder.get_keystrokes()
    """

    def __init__(
        self,
        output_file: str,
        command: List[str],
        options: Optional[dict] = None
    ):
        """
        Initialize the terminal recorder.

        Args:
            output_file: Path to save the .keys file
            command: Command to run (list of args)
            options: Recording options dict with keys:
                - auto_frame: bool - Add @frame after each key
                - frame_key: str - Hotkey to mark frames (e.g., 'C-g')
                - min_delay: int - Minimum delay in ms (default 50)
                - max_delay: int - Maximum delay in ms (default 2000)
                - cols: int - Terminal width
                - rows: int - Terminal height
        """
        self.output_file = output_file
        self.command = command
        self.options = options or {}

        # Recording state
        self.keystrokes: List[Tuple[float, str, bytes]] = []
        self.frame_markers: List[int] = []  # Indices where frames were marked
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

        # PTY state
        self._master_fd: Optional[int] = None
        self._child_pid: Optional[int] = None
        self._old_tty_attrs = None
        self._running = False

        # Key parsing
        self._key_mapper = KeyMapper()

        # Frame key detection
        self._frame_key = self.options.get('frame_key', 'C-g')

        # Max duration (default 5 minutes)
        self._max_duration = self.options.get('max_duration', 300)

    def record(self) -> None:
        """
        Start recording the terminal session.

        This method blocks until the session ends (command exits or Ctrl+D).
        """
        # Get terminal size
        cols = self.options.get('cols') or os.get_terminal_size().columns
        rows = self.options.get('rows') or os.get_terminal_size().lines

        # Save original terminal attributes
        if sys.stdin.isatty():
            self._old_tty_attrs = termios.tcgetattr(sys.stdin)

        try:
            # Set up signal handlers
            self._setup_signals()

            # Set terminal to raw mode
            if sys.stdin.isatty():
                tty.setraw(sys.stdin)

            # Fork PTY
            self._child_pid, self._master_fd = pty.fork()

            if self._child_pid == 0:
                # Child process - run the command
                os.environ['TERM'] = os.environ.get('TERM', 'xterm-256color')
                try:
                    os.execvp(self.command[0], self.command)
                except FileNotFoundError:
                    sys.stderr.write(f"Command not found: {self.command[0]}\n")
                    sys.exit(127)
            else:
                # Parent process - record I/O
                self._set_pty_size(cols, rows)
                self.start_time = time.time()
                self._running = True
                self._copy_with_logging()
                self.end_time = time.time()

        except Exception as e:
            # Re-raise after cleanup
            raise
        finally:
            self._restore_terminal()

    def _setup_signals(self) -> None:
        """Set up signal handlers for clean shutdown and resize."""
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
        signal.signal(signal.SIGWINCH, self._handle_resize)

    def _handle_interrupt(self, signum, frame) -> None:
        """Handle interrupt signals gracefully."""
        self._running = False

    def _handle_resize(self, signum, frame) -> None:
        """Handle terminal resize."""
        if self._master_fd is not None:
            try:
                size = os.get_terminal_size()
                self._set_pty_size(size.columns, size.lines)
            except OSError:
                pass

    def _set_pty_size(self, cols: int, rows: int) -> None:
        """Set the PTY window size."""
        if self._master_fd is not None:
            winsize = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(self._master_fd, termios.TIOCSWINSZ, winsize)

    def _copy_with_logging(self) -> None:
        """
        Main I/O loop: copy data between stdin/stdout and the PTY,
        logging all input with timestamps.
        """
        escape_timeout = 0.05  # 50ms timeout for escape sequences

        while self._running:
            # Check max duration
            if self._max_duration and self.start_time:
                elapsed = time.time() - self.start_time
                if elapsed >= self._max_duration:
                    # Write message to stderr (restore terminal first for clean output)
                    self._restore_terminal()
                    sys.stderr.write(
                        f"\nMax duration ({self._max_duration}s) reached. "
                        "Stopping recording.\n"
                    )
                    break
            try:
                # Set up select with timeout for escape handling
                timeout = escape_timeout if self._key_mapper.has_pending() else None
                r, _, _ = select.select(
                    [sys.stdin, self._master_fd],
                    [],
                    [],
                    timeout
                )

                # Handle timeout (flush pending escape)
                if not r and self._key_mapper.has_pending():
                    keys = self._key_mapper.flush()
                    self._log_keys(keys)
                    continue

                # Handle user input
                if sys.stdin in r:
                    try:
                        data = os.read(sys.stdin.fileno(), 1024)
                    except OSError:
                        break

                    if not data:
                        break

                    # Parse input and log keystrokes
                    keys = self._key_mapper.parse_input(data)
                    self._log_keys(keys)

                    # Forward to PTY
                    os.write(self._master_fd, data)

                # Handle PTY output
                if self._master_fd in r:
                    try:
                        data = os.read(self._master_fd, 1024)
                    except OSError:
                        break

                    if not data:
                        break

                    # Forward to user's terminal
                    os.write(sys.stdout.fileno(), data)

            except (OSError, IOError):
                break

        # Flush any remaining buffered input
        if self._key_mapper.has_pending():
            keys = self._key_mapper.flush()
            self._log_keys(keys)

    def _log_keys(self, keys: List[Tuple[str, bytes]]) -> None:
        """Log parsed keystrokes with timestamps."""
        current_time = time.time()

        for key_name, raw_bytes in keys:
            self.keystrokes.append((current_time, key_name, raw_bytes))

            # Check for frame marker
            if key_name == self._frame_key:
                self.frame_markers.append(len(self.keystrokes) - 1)

    def _restore_terminal(self) -> None:
        """Restore terminal to original state."""
        if self._old_tty_attrs is not None:
            try:
                termios.tcsetattr(
                    sys.stdin,
                    termios.TCSAFLUSH,
                    self._old_tty_attrs
                )
            except termios.error:
                pass

        # Close PTY master
        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass

    def get_keystrokes(self) -> List[Tuple[float, str, bytes]]:
        """
        Get the recorded keystrokes.

        Returns:
            List of (timestamp, key_name, raw_bytes) tuples
        """
        return self.keystrokes

    def get_frame_markers(self) -> List[int]:
        """
        Get indices of manual frame markers.

        Returns:
            List of keystroke indices where frames were marked
        """
        return self.frame_markers

    def get_duration(self) -> float:
        """Get the total recording duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
