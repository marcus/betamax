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

    # Terminal noise: escape sequence parts that aren't user input
    # These are responses FROM the terminal, not user keystrokes
    TERMINAL_NOISE_KEYS = {'M-[', 'M-]', 'M-\\', 'M-P'}

    # Keys that should be aggregated when repeated (navigation, editing)
    AGGREGATABLE_KEYS = {
        'Up', 'Down', 'Left', 'Right',
        'S-Up', 'S-Down', 'S-Left', 'S-Right',
        'C-Up', 'C-Down', 'C-Left', 'C-Right',
        'M-Up', 'M-Down', 'M-Left', 'M-Right',
        'PPage', 'NPage', 'Home', 'End',
        'BSpace', 'DC', 'Space', 'Tab', 'BTab',
        'Enter',
    }

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
                - aggregate: bool - Aggregate consecutive identical keys (default True)
                - aggregate_threshold: int - Max delay (ms) between keys to aggregate (default 200)
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

        # Aggregation settings
        self.aggregate = self.options.get('aggregate', True)
        self.aggregate_threshold = self.options.get('aggregate_threshold', 200)

        # Filter and cache user keystrokes (excludes terminal noise)
        self._user_keystrokes = None

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
            lines.append(f'# Keystrokes: {self.count_user_keystrokes()}')
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

        # Process filtered keystrokes (terminal noise removed)
        user_keystrokes = self._get_user_keystrokes()

        # Aggregate keystrokes if enabled
        if self.aggregate:
            aggregated = self._aggregate_keystrokes(user_keystrokes)
        else:
            # Convert to same format as aggregated (count=1 for each)
            aggregated = [
                (orig_idx, timestamp, key_name, raw_bytes, 1, timestamp)
                for orig_idx, timestamp, key_name, raw_bytes in user_keystrokes
            ]

        prev_time = None
        for orig_idx, first_timestamp, key_name, raw_bytes, count, last_timestamp in aggregated:
            # Skip the frame marker key itself (use original index for frame_markers check)
            if key_name == self.frame_key and orig_idx in self.frame_markers:
                # Add frame marker but don't output the key
                lines.append('@frame')
                prev_time = last_timestamp
                continue

            # Calculate delay from previous keystroke
            if prev_time is not None and not self.fixed_delay:
                delay_ms = int((first_timestamp - prev_time) * 1000)

                # Apply clamping
                if delay_ms < self.min_delay:
                    delay_ms = 0  # No timing annotation needed
                elif delay_ms > self.max_delay:
                    delay_ms = self.max_delay

                # Format key output (with count if aggregated)
                key_output = f'{key_name} {count}' if count > 1 else key_name

                # Use @sleep for very long delays (>= 500ms)
                if delay_ms >= 500:
                    lines.append(f'@sleep:{delay_ms}')
                    lines.append(key_output)
                elif delay_ms > 0 and delay_ms != default_delay:
                    # Use inline timing (only for single keys, aggregated use separate line)
                    if count > 1:
                        lines.append(f'@sleep:{delay_ms}' if delay_ms >= 500 else f'# delay:{delay_ms}ms')
                        lines.append(key_output)
                    else:
                        lines.append(f'{key_name}@{delay_ms}')
                else:
                    lines.append(key_output)
            else:
                key_output = f'{key_name} {count}' if count > 1 else key_name
                lines.append(key_output)

            prev_time = last_timestamp

            # Auto-frame mode (only once per aggregated group)
            if self.auto_frame:
                lines.append('@frame')

        # Stop recording if GIF mode
        if self.gif_output:
            lines.append(f'@record:stop:{self.gif_output}')

        return '\n'.join(lines) + '\n'

    def _aggregate_keystrokes(
        self,
        keystrokes: List[Tuple[int, float, str, bytes]]
    ) -> List[Tuple[int, float, str, bytes, int, float]]:
        """
        Aggregate consecutive identical keys into groups.

        Only aggregates keys in AGGREGATABLE_KEYS that occur within
        aggregate_threshold milliseconds of each other.

        Args:
            keystrokes: List of (orig_idx, timestamp, key_name, raw_bytes) tuples

        Returns:
            List of (orig_idx, first_timestamp, key_name, raw_bytes, count, last_timestamp) tuples
        """
        if not keystrokes:
            return []

        result = []
        current_key = None
        current_count = 0
        current_first_idx = None
        current_first_timestamp = None
        current_last_timestamp = None
        current_raw_bytes = None
        prev_timestamp = None

        for orig_idx, timestamp, key_name, raw_bytes in keystrokes:
            # Check if this key can be aggregated with the previous one
            can_aggregate = (
                current_key == key_name
                and key_name in self.AGGREGATABLE_KEYS
                and prev_timestamp is not None
            )

            if can_aggregate:
                # Check timing threshold
                delay_ms = int((timestamp - prev_timestamp) * 1000)
                can_aggregate = delay_ms <= self.aggregate_threshold

            if can_aggregate:
                # Continue aggregating
                current_count += 1
                current_last_timestamp = timestamp
            else:
                # Flush previous group if exists
                if current_key is not None:
                    result.append((
                        current_first_idx,
                        current_first_timestamp,
                        current_key,
                        current_raw_bytes,
                        current_count,
                        current_last_timestamp
                    ))

                # Start new group
                current_key = key_name
                current_count = 1
                current_first_idx = orig_idx
                current_first_timestamp = timestamp
                current_last_timestamp = timestamp
                current_raw_bytes = raw_bytes

            prev_timestamp = timestamp

        # Flush last group
        if current_key is not None:
            result.append((
                current_first_idx,
                current_first_timestamp,
                current_key,
                current_raw_bytes,
                current_count,
                current_last_timestamp
            ))

        return result

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
        """Calculate median delay between user keystrokes for @set:delay."""
        user_keystrokes = self._get_user_keystrokes()
        if len(user_keystrokes) < 2:
            return 100  # Default

        delays = []
        prev_time = None
        for _, timestamp, _, _ in user_keystrokes:
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

    def _get_user_keystrokes(self) -> List[Tuple[int, float, str, bytes]]:
        """
        Filter and return only user keystrokes, excluding terminal noise.

        Terminal responses (device attributes, capability queries) arrive as
        bursts of characters with no delay. This method filters them out to
        return only actual user input.

        Returns:
            List of (original_index, timestamp, key_name, raw_bytes) tuples
        """
        if self._user_keystrokes is not None:
            return self._user_keystrokes

        if not self.keystrokes:
            self._user_keystrokes = []
            return self._user_keystrokes

        filtered = []
        prev_time = None
        in_terminal_response = False

        for i, (timestamp, key_name, raw_bytes) in enumerate(self.keystrokes):
            # Calculate delay from previous keystroke
            delay_ms = 0
            if prev_time is not None:
                delay_ms = int((timestamp - prev_time) * 1000)

            # Detect terminal response sequences (arrive in rapid bursts)
            # M-[ starts CSI, M-] starts OSC, M-P starts DCS - all are terminal responses
            if key_name in ('M-[', 'M-]', 'M-P'):
                in_terminal_response = True
                prev_time = timestamp
                continue

            # End terminal response on significant delay (>20ms = user typing)
            if delay_ms > 20:
                in_terminal_response = False

            # Skip terminal noise keys (OSC, DCS, ST introducers)
            if key_name in self.TERMINAL_NOISE_KEYS:
                prev_time = timestamp
                continue

            # Skip keys that are part of a terminal response (CSI parameters)
            # These arrive in rapid bursts with <5ms between them
            if in_terminal_response and delay_ms < 5:
                prev_time = timestamp
                continue

            # This is a user keystroke - include it with original index
            filtered.append((i, timestamp, key_name, raw_bytes))
            prev_time = timestamp

        self._user_keystrokes = filtered
        return self._user_keystrokes

    def count_user_keystrokes(self) -> int:
        """
        Count actual user keystrokes, filtering out terminal noise.

        Returns:
            Number of user keystrokes (excluding terminal responses)
        """
        return len(self._get_user_keystrokes())
