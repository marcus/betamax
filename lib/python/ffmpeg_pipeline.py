"""
ffmpeg_pipeline.py - Unified decoration compositing pipeline for GIF generation

Builds FFmpeg filter chains that combine multiple decoration layers:
1. Base frames (from termshot)
2. Window bar (macOS-style)
3. Rounded corners (alpha mask)
4. Margin/padding

Order matters: bar extends height, then corners apply, then margin wraps.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from .decorations import (
    generate_window_bar,
    generate_corner_mask,
    DEFAULT_BAR_HEIGHT,
    _validate_hex_color,
    _validate_dimensions,
    _validate_border_radius,
    _validate_output_path,
)


@dataclass
class DecorationOptions:
    """Configuration for GIF decorations."""
    # Window bar
    window_bar_style: Optional[str] = None  # colorful, colorful_right, rings, none
    bar_color: str = '#1e1e1e'
    bar_height: int = DEFAULT_BAR_HEIGHT

    # Rounded corners
    border_radius: int = 0

    # Margin/padding
    margin: int = 0
    margin_color: str = '#000000'
    padding: int = 0
    padding_color: str = '#1e1e1e'

    # Playback
    speed: float = 1.0
    frame_delay_ms: int = 200

    def __post_init__(self):
        """Validate all options after initialization."""
        # Validate colors
        self.bar_color = _validate_hex_color(self.bar_color)
        self.margin_color = _validate_hex_color(self.margin_color)
        self.padding_color = _validate_hex_color(self.padding_color)

        # Validate numeric values
        if self.bar_height < 0:
            raise ValueError(f'bar_height cannot be negative: {self.bar_height}')
        if self.border_radius < 0:
            raise ValueError(f'border_radius cannot be negative: {self.border_radius}')
        if self.margin < 0:
            raise ValueError(f'margin cannot be negative: {self.margin}')
        if self.padding < 0:
            raise ValueError(f'padding cannot be negative: {self.padding}')

        # Validate speed
        if self.speed <= 0:
            raise ValueError(f'speed must be positive: {self.speed}')
        if self.speed > 100:
            raise ValueError(f'speed too high: {self.speed} (max 100)')

        # Validate frame delay
        if self.frame_delay_ms < 10:
            raise ValueError(f'frame_delay_ms too low: {self.frame_delay_ms} (min 10)')
        if self.frame_delay_ms > 10000:
            raise ValueError(f'frame_delay_ms too high: {self.frame_delay_ms} (max 10000)')


@dataclass
class PipelineInput:
    """Input specification for a stream."""
    path: str
    index: int
    is_image: bool = False  # True for decoration images (need loop)


class DecorationPipeline:
    """
    Builds FFmpeg commands for compositing decorations onto GIF frames.

    Usage:
        pipeline = DecorationPipeline(width=800, height=600, options=opts)
        pipeline.add_window_bar('/tmp/bar.png')
        pipeline.add_border_radius('/tmp/mask.png')
        pipeline.add_margin()

        inputs, filter_complex = pipeline.build()
        # Use inputs and filter_complex with ffmpeg
    """

    def __init__(
        self,
        frame_width: int,
        frame_height: int,
        options: DecorationOptions,
        recording_dir: str,
    ):
        # Validate dimensions
        _validate_dimensions(frame_width, 'frame_width')
        _validate_dimensions(frame_height, 'frame_height')

        # Validate recording_dir exists
        if not recording_dir:
            raise ValueError('recording_dir cannot be empty')
        if not os.path.isdir(recording_dir):
            raise ValueError(f'recording_dir does not exist: {recording_dir}')

        self.frame_width = frame_width
        self.frame_height = frame_height
        self.options = options
        self.recording_dir = os.path.abspath(recording_dir)

        # Track current dimensions (changes as decorations add height/width)
        self.current_width = frame_width
        self.current_height = frame_height

        # Build state
        self._inputs: List[PipelineInput] = []
        self._filter_stages: List[str] = []
        self._stream_counter = 0
        self._prev_stream = '[frames]'
        self._decoration_files: List[str] = []

    def _next_stream(self, name: str = None) -> str:
        """Get next unique stream name."""
        self._stream_counter += 1
        if name:
            return f'[{name}]'
        return f'[s{self._stream_counter}]'

    def add_input(self, path: str, is_image: bool = False) -> int:
        """Add an input file and return its index."""
        idx = len(self._inputs)
        self._inputs.append(PipelineInput(path=path, index=idx, is_image=is_image))
        return idx

    def add_window_bar(self) -> bool:
        """
        Add window bar decoration.

        Generates bar image and adds filter to composite at top.
        Returns True on success.
        """
        if not self.options.window_bar_style:
            return False
        if self.options.window_bar_style == 'none':
            return False

        bar_path = os.path.join(self.recording_dir, 'decoration_bar.png')

        if not generate_window_bar(
            width=self.current_width,
            output_path=bar_path,
            style=self.options.window_bar_style,
            bg_color=self.options.bar_color,
            bar_height=self.options.bar_height,
        ):
            return False

        self._decoration_files.append(bar_path)
        bar_idx = self.add_input(bar_path, is_image=True)
        bar_stream = f'[{bar_idx}:v]'

        # Pad the frames to add space at top for bar
        bar_height = self.options.bar_height
        padded = self._next_stream('padded')
        self._filter_stages.append(
            f'{self._prev_stream}pad=w={self.current_width}:h={self.current_height + bar_height}:x=0:y={bar_height}:color={self.options.bar_color}{padded}'
        )
        self._prev_stream = padded

        # Loop the bar image and overlay at top
        bar_loop = self._next_stream('bar')
        result = self._next_stream('withbar')
        self._filter_stages.append(f'{bar_stream}loop=loop=-1:size=1{bar_loop}')
        self._filter_stages.append(f'{self._prev_stream}{bar_loop}overlay=0:0{result}')
        self._prev_stream = result

        self.current_height += bar_height
        return True

    def add_border_radius(self) -> bool:
        """
        Add rounded corners.

        Generates corner mask and applies alpha merge.
        Returns True on success.
        """
        if self.options.border_radius <= 0:
            return False

        # Validate radius against current dimensions
        _validate_border_radius(
            self.options.border_radius,
            self.current_width,
            self.current_height
        )

        mask_path = os.path.join(self.recording_dir, 'decoration_mask.png')

        if not generate_corner_mask(
            width=self.current_width,
            height=self.current_height,
            output_path=mask_path,
            radius=self.options.border_radius,
        ):
            return False

        self._decoration_files.append(mask_path)
        mask_idx = self.add_input(mask_path, is_image=True)
        mask_stream = f'[{mask_idx}:v]'

        # Convert to RGBA format before alphamerge (required for proper alpha handling)
        rgba_stream = self._next_stream('rgba')
        self._filter_stages.append(f'{self._prev_stream}format=rgba{rgba_stream}')

        # Loop the mask and apply alphamerge
        mask_loop = self._next_stream('mask')
        result = self._next_stream('rounded')
        self._filter_stages.append(f'{mask_stream}loop=loop=-1:size=1{mask_loop}')
        self._filter_stages.append(f'{rgba_stream}{mask_loop}alphamerge{result}')
        self._prev_stream = result
        return True

    def add_padding(self) -> bool:
        """Add inner padding around content."""
        if self.options.padding <= 0:
            return False

        p = self.options.padding
        result = self._next_stream('padded_inner')
        self._filter_stages.append(
            f'{self._prev_stream}pad=w={self.current_width + p * 2}:h={self.current_height + p * 2}:x={p}:y={p}:color={self.options.padding_color}{result}'
        )
        self._prev_stream = result
        self.current_width += p * 2
        self.current_height += p * 2
        return True

    def add_margin(self) -> bool:
        """Add outer margin around the composition."""
        if self.options.margin <= 0:
            return False

        m = self.options.margin
        result = self._next_stream('margined')
        self._filter_stages.append(
            f'{self._prev_stream}pad=w={self.current_width + m * 2}:h={self.current_height + m * 2}:x={m}:y={m}:color={self.options.margin_color}{result}'
        )
        self._prev_stream = result
        self.current_width += m * 2
        self.current_height += m * 2
        return True

    def build(self) -> Tuple[List[str], str, str]:
        """
        Build the FFmpeg arguments.

        Returns:
            Tuple of (input_args, filter_complex, output_stream_name)

        The filter_complex includes palette generation for GIF output.
        """
        # Build input arguments
        input_args = []
        for inp in self._inputs:
            if inp.is_image:
                input_args.extend(['-i', inp.path])
            else:
                input_args.extend(['-i', inp.path])

        # Add palette generation at the end
        final_stream = self._prev_stream

        # Apply speed adjustment
        if self.options.speed != 1.0:
            speed_result = self._next_stream('sped')
            self._filter_stages.append(
                f'{final_stream}setpts=PTS/{self.options.speed}{speed_result}'
            )
            final_stream = speed_result

        # Split for palette generation
        split_a = self._next_stream('pa')
        split_b = self._next_stream('pb')
        self._filter_stages.append(f'{final_stream}split{split_a}{split_b}')

        # Generate palette
        palette = self._next_stream('pal')
        self._filter_stages.append(
            f'{split_a}palettegen=max_colors=256:stats_mode=diff:reserve_transparent=0{palette}'
        )

        # Apply palette
        output = self._next_stream('out')
        self._filter_stages.append(
            f'{split_b}{palette}paletteuse=dither=bayer:bayer_scale=5{output}'
        )

        filter_complex = ';'.join(self._filter_stages)
        return input_args, filter_complex, output.strip('[]')

    def get_decoration_files(self) -> List[str]:
        """Get list of generated decoration files for cleanup."""
        return self._decoration_files


def build_gif_command(
    frame_pattern: str,
    output_path: str,
    options: DecorationOptions,
    recording_dir: str,
    frame_count: int,
) -> Tuple[List[str], List[str]]:
    """
    Build complete FFmpeg command for GIF generation with decorations.

    Args:
        frame_pattern: Path pattern for frames (e.g., '/tmp/frame_%05d.png')
        output_path: Output GIF path
        options: Decoration options
        recording_dir: Directory for temporary decoration files
        frame_count: Number of frames (for dimension detection)

    Returns:
        Tuple of (FFmpeg command args, list of temp decoration files to cleanup)
    """
    # Get frame dimensions from first frame
    first_frame = frame_pattern % 0
    if not os.path.exists(first_frame):
        first_frame = frame_pattern.replace('%05d', '00000')

    # Use ffprobe to get dimensions
    import subprocess
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height', '-of', 'csv=p=0',
             first_frame],
            capture_output=True, text=True, timeout=10
        )
    except FileNotFoundError:
        raise RuntimeError('ffprobe not found. Please install FFmpeg.')
    except subprocess.TimeoutExpired:
        raise RuntimeError(f'ffprobe timed out reading {first_frame}')

    if result.returncode != 0:
        raise RuntimeError(f'Failed to get frame dimensions: {result.stderr}')

    dims = result.stdout.strip().split(',')
    frame_width, frame_height = int(dims[0]), int(dims[1])

    # Build pipeline (DecorationOptions validates speed in __post_init__)
    pipeline = DecorationPipeline(
        frame_width=frame_width,
        frame_height=frame_height,
        options=options,
        recording_dir=recording_dir,
    )

    # Calculate effective frame delay with speed
    delay_cs = max(2, options.frame_delay_ms // 10)
    effective_delay = delay_cs / options.speed
    # Ensure reasonable bounds for frame rate
    effective_delay = max(1, min(effective_delay, 1000))
    effective_rate = 100 / effective_delay

    # Add frames as first input (with framerate)
    cmd = ['ffmpeg', '-y', '-framerate', '1', '-i', frame_pattern]

    # Add padding first (inside of rounded corners)
    pipeline.add_padding()

    # Add window bar (before rounded corners so corners apply to bar too)
    pipeline.add_window_bar()

    # Add rounded corners
    pipeline.add_border_radius()

    # Add outer margin last
    pipeline.add_margin()

    # Build filter complex
    # Start with the frames stream
    frames_filter = f'[0:v]settb=1,setpts=N*{effective_delay}/100/TB[frames]'

    input_args, filter_complex, output_stream = pipeline.build()

    # Combine frame setup with decoration filters
    full_filter = f'{frames_filter};{filter_complex}'

    # Build final command
    cmd.extend(input_args)
    cmd.extend([
        '-filter_complex', full_filter,
        '-map', f'[{output_stream}]',
        '-r', str(effective_rate),
        output_path
    ])

    return cmd, pipeline.get_decoration_files()


if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) < 2:
        print('Usage: ffmpeg_pipeline.py <command> [args]')
        print('Commands:')
        print('  build <frame_pattern> <output> <recording_dir> <options_json>')
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'build':
        frame_pattern = sys.argv[2]
        output = sys.argv[3]
        recording_dir = sys.argv[4]
        opts_json = sys.argv[5] if len(sys.argv) > 5 else '{}'

        opts_dict = json.loads(opts_json)
        options = DecorationOptions(
            window_bar_style=opts_dict.get('window_bar'),
            bar_color=opts_dict.get('bar_color', '#1e1e1e'),
            border_radius=opts_dict.get('border_radius', 0),
            margin=opts_dict.get('margin', 0),
            margin_color=opts_dict.get('margin_color', '#000000'),
            padding=opts_dict.get('padding', 0),
            padding_color=opts_dict.get('padding_color', '#1e1e1e'),
            speed=opts_dict.get('speed', 1.0),
            frame_delay_ms=opts_dict.get('gif_delay', 200),
        )

        try:
            ffmpeg_cmd, temp_files = build_gif_command(
                frame_pattern, output, options, recording_dir, 1
            )
            print(' '.join(ffmpeg_cmd))
        except Exception as e:
            print(f'Error: {e}', file=sys.stderr)
            sys.exit(1)

    else:
        print(f'Unknown command: {cmd}', file=sys.stderr)
        sys.exit(1)
