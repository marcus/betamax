"""Unit tests for decorations.py and ffmpeg_pipeline.py.

These tests focus on:
1. DecorationPipeline.build() output and filter chain syntax
2. Stream name management (_next_stream)
3. Dimension and speed validation
4. Error handling and edge cases
5. Validation functions
"""

import os
import sys
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.python.decorations import (
    _validate_hex_color,
    _validate_dimensions,
    _validate_output_path,
    _validate_border_radius,
    BAR_STYLES,
    DEFAULT_BAR_HEIGHT,
)
from lib.python.ffmpeg_pipeline import (
    DecorationPipeline,
    DecorationOptions,
    PipelineInput,
)


class TestHexColorValidation:
    """Unit tests for _validate_hex_color."""

    def test_valid_6_digit_with_hash(self):
        assert _validate_hex_color('#1e1e1e') == '#1e1e1e'
        assert _validate_hex_color('#FFFFFF') == '#FFFFFF'
        assert _validate_hex_color('#000000') == '#000000'

    def test_valid_6_digit_without_hash(self):
        assert _validate_hex_color('1e1e1e') == '#1e1e1e'
        assert _validate_hex_color('ffffff') == '#ffffff'

    def test_valid_3_digit_with_hash(self):
        assert _validate_hex_color('#fff') == '#fff'
        assert _validate_hex_color('#abc') == '#abc'

    def test_valid_3_digit_without_hash(self):
        assert _validate_hex_color('fff') == '#fff'

    def test_invalid_empty(self):
        with pytest.raises(ValueError, match='cannot be empty'):
            _validate_hex_color('')

    def test_invalid_wrong_length(self):
        with pytest.raises(ValueError, match='Invalid hex color length'):
            _validate_hex_color('#12')
        with pytest.raises(ValueError, match='Invalid hex color length'):
            _validate_hex_color('#1234')
        with pytest.raises(ValueError, match='Invalid hex color length'):
            _validate_hex_color('#12345')
        with pytest.raises(ValueError, match='Invalid hex color length'):
            _validate_hex_color('#1234567')

    def test_invalid_non_hex_chars(self):
        with pytest.raises(ValueError, match='non-hex characters'):
            _validate_hex_color('#gggggg')
        with pytest.raises(ValueError, match='non-hex characters'):
            _validate_hex_color('#zzzzzz')


class TestDimensionsValidation:
    """Unit tests for _validate_dimensions."""

    def test_valid_dimensions(self):
        assert _validate_dimensions(100, 'width') == 100
        assert _validate_dimensions(1, 'height') == 1
        assert _validate_dimensions(10000, 'size') == 10000

    def test_custom_bounds(self):
        assert _validate_dimensions(50, 'val', min_val=10, max_val=100) == 50

    def test_below_min(self):
        with pytest.raises(ValueError, match='must be between'):
            _validate_dimensions(0, 'width')
        with pytest.raises(ValueError, match='must be between'):
            _validate_dimensions(-1, 'height')

    def test_above_max(self):
        with pytest.raises(ValueError, match='must be between'):
            _validate_dimensions(10001, 'width')

    def test_wrong_type(self):
        with pytest.raises(TypeError, match='must be int'):
            _validate_dimensions('100', 'width')
        with pytest.raises(TypeError, match='must be int'):
            _validate_dimensions(100.5, 'height')


class TestOutputPathValidation:
    """Unit tests for _validate_output_path."""

    def test_valid_path(self):
        result = _validate_output_path('/tmp/test.png')
        assert os.path.isabs(result)

    def test_empty_path(self):
        with pytest.raises(ValueError, match='cannot be empty'):
            _validate_output_path('')

    def test_null_byte_injection(self):
        with pytest.raises(ValueError, match='null bytes'):
            _validate_output_path('/tmp/test\x00.png')

    def test_path_within_recording_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test.png')
            result = _validate_output_path(path, tmpdir)
            assert result.startswith(tmpdir)

    def test_path_outside_recording_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match='must be within'):
                _validate_output_path('/etc/passwd', tmpdir)


class TestBorderRadiusValidation:
    """Unit tests for _validate_border_radius."""

    def test_valid_radius(self):
        assert _validate_border_radius(10, 100, 100) == 10
        assert _validate_border_radius(50, 100, 100) == 50  # max allowed

    def test_zero_radius(self):
        assert _validate_border_radius(0, 100, 100) == 0

    def test_negative_radius(self):
        with pytest.raises(ValueError, match='cannot be negative'):
            _validate_border_radius(-1, 100, 100)

    def test_radius_exceeds_max(self):
        with pytest.raises(ValueError, match='exceeds max'):
            _validate_border_radius(51, 100, 100)  # max is 50
        with pytest.raises(ValueError, match='exceeds max'):
            _validate_border_radius(100, 100, 50)  # max is 25

    def test_wrong_type(self):
        with pytest.raises(TypeError, match='must be int'):
            _validate_border_radius('10', 100, 100)


class TestDecorationOptionsValidation:
    """Unit tests for DecorationOptions validation."""

    def test_default_options(self):
        opts = DecorationOptions()
        assert opts.window_bar_style is None
        assert opts.bar_color == '#1e1e1e'
        assert opts.bar_height == DEFAULT_BAR_HEIGHT
        assert opts.border_radius == 0
        assert opts.margin == 0
        assert opts.padding == 0
        assert opts.speed == 1.0
        assert opts.frame_delay_ms == 200

    def test_color_normalization(self):
        opts = DecorationOptions(bar_color='ffffff')
        assert opts.bar_color == '#ffffff'

    def test_negative_bar_height(self):
        with pytest.raises(ValueError, match='cannot be negative'):
            DecorationOptions(bar_height=-1)

    def test_negative_border_radius(self):
        with pytest.raises(ValueError, match='cannot be negative'):
            DecorationOptions(border_radius=-1)

    def test_negative_margin(self):
        with pytest.raises(ValueError, match='cannot be negative'):
            DecorationOptions(margin=-1)

    def test_negative_padding(self):
        with pytest.raises(ValueError, match='cannot be negative'):
            DecorationOptions(padding=-1)

    def test_zero_speed(self):
        with pytest.raises(ValueError, match='must be positive'):
            DecorationOptions(speed=0)

    def test_negative_speed(self):
        with pytest.raises(ValueError, match='must be positive'):
            DecorationOptions(speed=-1)

    def test_speed_too_high(self):
        with pytest.raises(ValueError, match='too high'):
            DecorationOptions(speed=101)

    def test_frame_delay_too_low(self):
        with pytest.raises(ValueError, match='too low'):
            DecorationOptions(frame_delay_ms=5)

    def test_frame_delay_too_high(self):
        with pytest.raises(ValueError, match='too high'):
            DecorationOptions(frame_delay_ms=20000)

    def test_valid_edge_speeds(self):
        DecorationOptions(speed=0.01)  # very slow
        DecorationOptions(speed=100)   # max allowed

    def test_valid_edge_delays(self):
        DecorationOptions(frame_delay_ms=10)    # min
        DecorationOptions(frame_delay_ms=10000) # max


class TestPipelineInput:
    """Unit tests for PipelineInput dataclass."""

    def test_basic_input(self):
        inp = PipelineInput(path='/tmp/test.png', index=0)
        assert inp.path == '/tmp/test.png'
        assert inp.index == 0
        assert inp.is_image is False

    def test_image_input(self):
        inp = PipelineInput(path='/tmp/bar.png', index=1, is_image=True)
        assert inp.is_image is True


class TestDecorationPipelineInit:
    """Unit tests for DecorationPipeline initialization."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_valid_init(self, temp_dir):
        opts = DecorationOptions()
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        assert pipeline.frame_width == 800
        assert pipeline.frame_height == 600
        assert pipeline.current_width == 800
        assert pipeline.current_height == 600
        assert pipeline._prev_stream == '[frames]'
        assert pipeline._stream_counter == 0

    def test_invalid_width(self, temp_dir):
        opts = DecorationOptions()
        with pytest.raises(ValueError):
            DecorationPipeline(0, 600, opts, temp_dir)

    def test_invalid_height(self, temp_dir):
        opts = DecorationOptions()
        with pytest.raises(ValueError):
            DecorationPipeline(800, 0, opts, temp_dir)

    def test_empty_recording_dir(self):
        opts = DecorationOptions()
        with pytest.raises(ValueError, match='cannot be empty'):
            DecorationPipeline(800, 600, opts, '')

    def test_nonexistent_recording_dir(self):
        opts = DecorationOptions()
        with pytest.raises(ValueError, match='does not exist'):
            DecorationPipeline(800, 600, opts, '/nonexistent/path')


class TestStreamNameManagement:
    """Unit tests for _next_stream method."""

    @pytest.fixture
    def pipeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            opts = DecorationOptions()
            yield DecorationPipeline(800, 600, opts, tmpdir)

    def test_sequential_stream_names(self, pipeline):
        s1 = pipeline._next_stream()
        s2 = pipeline._next_stream()
        s3 = pipeline._next_stream()

        assert s1 == '[s1]'
        assert s2 == '[s2]'
        assert s3 == '[s3]'

    def test_named_streams(self, pipeline):
        s1 = pipeline._next_stream('padded')
        s2 = pipeline._next_stream('withbar')

        assert s1 == '[padded]'
        assert s2 == '[withbar]'

    def test_counter_increments_for_named(self, pipeline):
        pipeline._next_stream('named')
        s2 = pipeline._next_stream()

        # Counter should have incremented even for named stream
        assert s2 == '[s2]'


class TestAddInput:
    """Unit tests for add_input method."""

    @pytest.fixture
    def pipeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            opts = DecorationOptions()
            yield DecorationPipeline(800, 600, opts, tmpdir)

    def test_add_single_input(self, pipeline):
        idx = pipeline.add_input('/tmp/test.png')
        assert idx == 0
        assert len(pipeline._inputs) == 1

    def test_add_multiple_inputs(self, pipeline):
        idx1 = pipeline.add_input('/tmp/test1.png')
        idx2 = pipeline.add_input('/tmp/test2.png', is_image=True)

        assert idx1 == 0
        assert idx2 == 1
        assert len(pipeline._inputs) == 2
        assert pipeline._inputs[1].is_image is True


class TestPipelineBuild:
    """Unit tests for DecorationPipeline.build() method."""

    @pytest.fixture
    def pipeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            opts = DecorationOptions()
            yield DecorationPipeline(800, 600, opts, tmpdir)

    def test_build_no_decorations(self, pipeline):
        input_args, filter_complex, output_stream = pipeline.build()

        assert input_args == []
        # Should contain palette generation
        assert 'palettegen' in filter_complex
        assert 'paletteuse' in filter_complex
        assert 'split' in filter_complex

    def test_build_output_stream_name(self, pipeline):
        _, _, output_stream = pipeline.build()

        # Output stream should not have brackets
        assert not output_stream.startswith('[')
        assert not output_stream.endswith(']')

    def test_filter_complex_semicolon_separated(self, pipeline):
        # Add padding to have multiple filter stages
        pipeline.options = DecorationOptions(padding=10)
        pipeline.add_padding()

        _, filter_complex, _ = pipeline.build()

        # Filter stages should be semicolon-separated
        assert ';' in filter_complex

    def test_speed_adjustment_in_filter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            opts = DecorationOptions(speed=2.0)
            pipeline = DecorationPipeline(800, 600, opts, tmpdir)

            _, filter_complex, _ = pipeline.build()

            # Should include setpts for speed adjustment
            assert 'setpts=PTS/2.0' in filter_complex


class TestFilterChainSyntax:
    """Unit tests verifying correct FFmpeg filter chain syntax."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_padding_filter_syntax(self, temp_dir):
        opts = DecorationOptions(padding=10, padding_color='#ff0000')
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        pipeline.add_padding()
        _, filter_complex, _ = pipeline.build()

        # Check pad filter format
        assert 'pad=w=820:h=620:x=10:y=10:color=#ff0000' in filter_complex

    def test_margin_filter_syntax(self, temp_dir):
        opts = DecorationOptions(margin=20, margin_color='#00ff00')
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        pipeline.add_margin()
        _, filter_complex, _ = pipeline.build()

        assert 'pad=w=840:h=640:x=20:y=20:color=#00ff00' in filter_complex

    def test_palette_filter_syntax(self, temp_dir):
        opts = DecorationOptions()
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        _, filter_complex, _ = pipeline.build()

        # Verify palette generation syntax
        assert 'palettegen=max_colors=256:stats_mode=diff:reserve_transparent=0' in filter_complex
        assert 'paletteuse=dither=bayer:bayer_scale=5' in filter_complex

    def test_stream_chaining(self, temp_dir):
        opts = DecorationOptions(padding=10, margin=20)
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        pipeline.add_padding()
        pipeline.add_margin()
        _, filter_complex, _ = pipeline.build()

        # Verify streams are properly chained (output of one is input to next)
        # The filter complex should have proper bracket notation
        assert '[frames]' in filter_complex or filter_complex.startswith('[')


class TestDimensionTracking:
    """Unit tests for dimension tracking through pipeline."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_padding_increases_dimensions(self, temp_dir):
        opts = DecorationOptions(padding=10)
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        initial_w, initial_h = pipeline.current_width, pipeline.current_height
        pipeline.add_padding()

        assert pipeline.current_width == initial_w + 20  # padding * 2
        assert pipeline.current_height == initial_h + 20

    def test_margin_increases_dimensions(self, temp_dir):
        opts = DecorationOptions(margin=15)
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        initial_w, initial_h = pipeline.current_width, pipeline.current_height
        pipeline.add_margin()

        assert pipeline.current_width == initial_w + 30
        assert pipeline.current_height == initial_h + 30

    def test_dimensions_unchanged_with_no_decorations(self, temp_dir):
        opts = DecorationOptions()
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        pipeline.add_padding()   # padding=0, no change
        pipeline.add_margin()    # margin=0, no change

        assert pipeline.current_width == 800
        assert pipeline.current_height == 600


class TestEdgeCases:
    """Unit tests for edge cases and boundary conditions."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_minimum_dimensions(self, temp_dir):
        opts = DecorationOptions()
        pipeline = DecorationPipeline(1, 1, opts, temp_dir)

        assert pipeline.frame_width == 1
        assert pipeline.frame_height == 1

    def test_maximum_dimensions(self, temp_dir):
        opts = DecorationOptions()
        pipeline = DecorationPipeline(10000, 10000, opts, temp_dir)

        assert pipeline.frame_width == 10000
        assert pipeline.frame_height == 10000

    def test_zero_padding_returns_false(self, temp_dir):
        opts = DecorationOptions(padding=0)
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        assert pipeline.add_padding() is False

    def test_zero_margin_returns_false(self, temp_dir):
        opts = DecorationOptions(margin=0)
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        assert pipeline.add_margin() is False

    def test_zero_border_radius_returns_false(self, temp_dir):
        opts = DecorationOptions(border_radius=0)
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        assert pipeline.add_border_radius() is False

    def test_none_window_bar_returns_false(self, temp_dir):
        opts = DecorationOptions(window_bar_style=None)
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        assert pipeline.add_window_bar() is False

    def test_window_bar_none_style_returns_false(self, temp_dir):
        opts = DecorationOptions(window_bar_style='none')
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        assert pipeline.add_window_bar() is False


class TestBarStyles:
    """Unit tests for BAR_STYLES configuration."""

    def test_colorful_style_config(self):
        style = BAR_STYLES['colorful']
        assert 'dots' in style
        assert len(style['dots']) == 3
        assert 'default_bg' in style

    def test_colorful_right_style_config(self):
        style = BAR_STYLES['colorful_right']
        assert style.get('align') == 'right'

    def test_rings_style_config(self):
        style = BAR_STYLES['rings']
        assert style.get('hollow') is True


class TestDecorationFilesTracking:
    """Unit tests for decoration files tracking and cleanup."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_decoration_files_initially_empty(self, temp_dir):
        opts = DecorationOptions()
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        assert pipeline.get_decoration_files() == []

    def test_cleanup_clears_list(self, temp_dir):
        opts = DecorationOptions()
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        # Manually add a file to track
        test_file = os.path.join(temp_dir, 'test.png')
        open(test_file, 'w').close()
        pipeline._decoration_files.append(test_file)

        pipeline.cleanup_decoration_files()

        assert pipeline._decoration_files == []
        assert not os.path.exists(test_file)

    def test_cleanup_handles_nonexistent_files(self, temp_dir):
        opts = DecorationOptions()
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        # Add nonexistent file to track
        pipeline._decoration_files.append('/nonexistent/file.png')

        # Should not raise
        pipeline.cleanup_decoration_files()
        assert pipeline._decoration_files == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
