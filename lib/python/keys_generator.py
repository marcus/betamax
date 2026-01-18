"""
keys_generator.py - Generate betamax .keys files from recorded sessions

Converts recorded keystrokes to the betamax .keys format with timing,
frame markers, and recording directives.
"""

from typing import List, Tuple, Optional
import os


class KeysGenerator:
    """
    Generates betamax .keys files from recorded keystrokes.

    Usage:
        generator = KeysGenerator(keystrokes, options)
        content = generator.generate()
        generator.save('output.keys')
    """

    def __init__(
        self,
        keystrokes: List[Tuple[float, str, bytes]],
        options: Optional[dict] = None
    ):
        """
        Initialize the keys generator.

        Args:
            keystrokes: List of (timestamp, key_name, raw_bytes) tuples
            options: Generation options dict with keys:
                - cols: int - Terminal width
                - rows: int - Terminal height
                - auto_frame: bool - Add @frame after each key
                - frame_markers: List[int] - Indices of manual frame markers
                - min_delay: int - Minimum delay in ms (default 50)
                - max_delay: int - Maximum delay in ms (default 2000)
                - fixed_delay: Optional[int] - Use fixed delay instead of measured
                - gif_output: Optional[str] - If set, wrap in @record directives
                - command: str - The command that was recorded
                - frame_key: str - The frame marker key (to filter from output)
        """
        self.keystrokes = keystrokes
        self.options = options or {}

        # Defaults
        self.cols = self.options.get('cols', 80)
        self.rows = self.options.get('rows', 24)
        self.auto_frame = self.options.get('auto_frame', False)
        self.frame_markers = set(self.options.get('frame_markers', []))
        self.min_delay = self.options.get('min_delay', 50)
        self.max_delay = self.options.get('max_delay', 2000)
        self.fixed_delay = self.options.get('fixed_delay')
        self.gif_output = self.options.get('gif_output')
        self.command = self.options.get('command', '')
        self.frame_key = self.options.get('frame_key', 'C-g')

    def generate(self) -> str:
        """
        Generate the .keys file content.

        Returns:
            String content of the .keys file
        """
        lines = []

        # Header comments
        lines.append('# Recorded with betamax record')
        if self.command:
            lines.append(f'# Command: {self.command}')
        if self.keystrokes:
            duration = self._calculate_duration()
            lines.append(f'# Duration: {duration:.1f}s')
            lines.append(f'# Keystrokes: {len(self.keystrokes)}')
        lines.append('')

        # Settings
        lines.append(f'@set:cols:{self.cols}')
        lines.append(f'@set:rows:{self.rows}')

        # Calculate default delay
        if self.fixed_delay:
            default_delay = self.fixed_delay
        else:
            default_delay = self._calculate_median_delay()
        lines.append(f'@set:delay:{default_delay}')
        lines.append('')

        # Start recording if GIF mode
        if self.gif_output:
            lines.append('@record:start')

        # Process keystrokes
        prev_time = None
        for i, (timestamp, key_name, raw_bytes) in enumerate(self.keystrokes):
            # Skip the frame marker key itself
            if key_name == self.frame_key and i in self.frame_markers:
                # Add frame marker but don't output the key
                lines.append('@frame')
                prev_time = timestamp
                continue

            # Calculate delay from previous keystroke
            if prev_time is not None and not self.fixed_delay:
                delay_ms = int((timestamp - prev_time) * 1000)

                # Apply clamping
                if delay_ms < self.min_delay:
                    delay_ms = 0  # No timing annotation needed
                elif delay_ms > self.max_delay:
                    delay_ms = self.max_delay

                # Use @sleep for very long delays (>= 500ms)
                if delay_ms >= 500:
                    lines.append(f'@sleep:{delay_ms}')
                    lines.append(key_name)
                elif delay_ms > 0 and delay_ms != default_delay:
                    # Use inline timing
                    lines.append(f'{key_name}@{delay_ms}')
                else:
                    lines.append(key_name)
            else:
                lines.append(key_name)

            prev_time = timestamp

            # Auto-frame mode
            if self.auto_frame:
                lines.append('@frame')

            # Manual frame marker
            if i in self.frame_markers:
                lines.append('@frame')

        # Stop recording if GIF mode
        if self.gif_output:
            lines.append(f'@record:stop:{self.gif_output}')

        return '\n'.join(lines) + '\n'

    def save(self, filepath: str) -> None:
        """
        Save the generated .keys content to a file.

        Args:
            filepath: Path to save the file
        """
        content = self.generate()

        # Ensure directory exists
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(filepath, 'w') as f:
            f.write(content)

    def _calculate_duration(self) -> float:
        """Calculate total recording duration in seconds."""
        if len(self.keystrokes) < 2:
            return 0.0
        return self.keystrokes[-1][0] - self.keystrokes[0][0]

    def _calculate_median_delay(self) -> int:
        """Calculate median delay between keystrokes for @set:delay."""
        if len(self.keystrokes) < 2:
            return 100  # Default

        delays = []
        prev_time = None
        for timestamp, _, _ in self.keystrokes:
            if prev_time is not None:
                delay_ms = int((timestamp - prev_time) * 1000)
                # Only include reasonable delays
                if self.min_delay <= delay_ms <= self.max_delay:
                    delays.append(delay_ms)
            prev_time = timestamp

        if not delays:
            return 100

        # Return median
        delays.sort()
        mid = len(delays) // 2
        if len(delays) % 2 == 0:
            return (delays[mid - 1] + delays[mid]) // 2
        return delays[mid]
