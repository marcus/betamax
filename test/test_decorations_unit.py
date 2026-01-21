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
    _validate_shadow_params,
    _calculate_shadow_canvas_size,
    generate_shadow,
    generate_shadow_pillow,
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


class TestShadowParamsValidation:
    """Unit tests for shadow parameter validation."""

    def test_valid_blur_radius(self):
        blur, _, _, _, _ = _validate_shadow_params(0, 0, 0, 0.5, '#000000')
        assert blur == 0

        blur, _, _, _, _ = _validate_shadow_params(15, 0, 0, 0.5, '#000000')
        assert blur == 15

        blur, _, _, _, _ = _validate_shadow_params(100, 0, 0, 0.5, '#000000')
        assert blur == 100

    def test_invalid_blur_radius(self):
        with pytest.raises(ValueError, match='blur_radius must be 0-100'):
            _validate_shadow_params(-1, 0, 0, 0.5, '#000000')
        with pytest.raises(ValueError, match='blur_radius must be 0-100'):
            _validate_shadow_params(101, 0, 0, 0.5, '#000000')

    def test_valid_offsets(self):
        _, ox, oy, _, _ = _validate_shadow_params(15, -200, 200, 0.5, '#000000')
        assert ox == -200
        assert oy == 200

        _, ox, oy, _, _ = _validate_shadow_params(15, 0, 0, 0.5, '#000000')
        assert ox == 0
        assert oy == 0

    def test_invalid_offsets(self):
        with pytest.raises(ValueError, match='offset_x must be -200 to 200'):
            _validate_shadow_params(15, -201, 0, 0.5, '#000000')
        with pytest.raises(ValueError, match='offset_x must be -200 to 200'):
            _validate_shadow_params(15, 201, 0, 0.5, '#000000')
        with pytest.raises(ValueError, match='offset_y must be -200 to 200'):
            _validate_shadow_params(15, 0, -201, 0.5, '#000000')
        with pytest.raises(ValueError, match='offset_y must be -200 to 200'):
            _validate_shadow_params(15, 0, 201, 0.5, '#000000')

    def test_valid_opacity(self):
        _, _, _, op, _ = _validate_shadow_params(15, 0, 0, 0.0, '#000000')
        assert op == 0.0

        _, _, _, op, _ = _validate_shadow_params(15, 0, 0, 0.4, '#000000')
        assert op == 0.4

        _, _, _, op, _ = _validate_shadow_params(15, 0, 0, 1.0, '#000000')
        assert op == 1.0

    def test_invalid_opacity(self):
        with pytest.raises(ValueError, match='opacity must be 0.0-1.0'):
            _validate_shadow_params(15, 0, 0, -0.1, '#000000')
        with pytest.raises(ValueError, match='opacity must be 0.0-1.0'):
            _validate_shadow_params(15, 0, 0, 1.1, '#000000')

    def test_color_validation(self):
        _, _, _, _, color = _validate_shadow_params(15, 0, 0, 0.5, '#000000')
        assert color == '#000000'

        _, _, _, _, color = _validate_shadow_params(15, 0, 0, 0.5, 'ffffff')
        assert color == '#ffffff'

        with pytest.raises(ValueError, match='non-hex'):
            _validate_shadow_params(15, 0, 0, 0.5, '#gggggg')

    def test_type_errors(self):
        with pytest.raises(TypeError, match='blur_radius must be int'):
            _validate_shadow_params('15', 0, 0, 0.5, '#000000')
        with pytest.raises(TypeError, match='offset_x must be int'):
            _validate_shadow_params(15, '0', 0, 0.5, '#000000')
        with pytest.raises(TypeError, match='opacity must be float'):
            _validate_shadow_params(15, 0, 0, '0.5', '#000000')


class TestShadowCanvasCalculation:
    """Unit tests for shadow canvas size calculation."""

    def test_basic_calculation(self):
        w, h, p = _calculate_shadow_canvas_size(100, 100, 15, 0, 8)
        # padding = 15*2 + max(0, 8) = 38
        assert p == 38
        assert w == 100 + 38 * 2  # 176
        assert h == 100 + 38 * 2  # 176

    def test_negative_offset(self):
        w, h, p = _calculate_shadow_canvas_size(100, 100, 10, -20, 0)
        # padding = 10*2 + max(20, 0) = 40
        assert p == 40
        assert w == 180
        assert h == 180

    def test_zero_blur(self):
        w, h, p = _calculate_shadow_canvas_size(100, 100, 0, 5, 5)
        # padding = 0*2 + max(5, 5) = 5
        assert p == 5
        assert w == 110
        assert h == 110


class TestShadowGeneration:
    """Unit tests for shadow generation."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_generate_shadow_pillow_basic(self, temp_dir):
        output = os.path.join(temp_dir, 'shadow.png')

        result = generate_shadow_pillow(
            width=100,
            height=100,
            output_path=output,
            blur_radius=15,
            offset_x=0,
            offset_y=8,
            opacity=0.4,
            color='#000000',
        )

        assert result is True
        assert os.path.exists(output)

        # Verify output is RGBA
        from PIL import Image
        img = Image.open(output)
        assert img.mode == 'RGBA'

        # Verify dimensions (100 + (15*2 + 8)*2 = 100 + 76 = 176)
        assert img.width == 176
        assert img.height == 176

    def test_generate_shadow_with_mask(self, temp_dir):
        # Create a simple corner mask first
        from PIL import Image
        mask_path = os.path.join(temp_dir, 'mask.png')
        mask = Image.new('L', (100, 100), 255)
        mask.save(mask_path)

        output = os.path.join(temp_dir, 'shadow.png')
        result = generate_shadow_pillow(
            width=100,
            height=100,
            output_path=output,
            blur_radius=10,
            offset_x=0,
            offset_y=5,
            opacity=0.5,
            color='#000000',
            source_mask_path=mask_path,
        )

        assert result is True
        assert os.path.exists(output)

    def test_generate_shadow_wrapper(self, temp_dir):
        output = os.path.join(temp_dir, 'shadow.png')

        result = generate_shadow(
            width=50,
            height=50,
            output_path=output,
            blur_radius=5,
            offset_x=2,
            offset_y=4,
            opacity=0.3,
            color='#333333',
        )

        assert result is True
        assert os.path.exists(output)

    def test_generate_shadow_various_blur(self, temp_dir):
        # Test with zero blur
        output = os.path.join(temp_dir, 'shadow_zero.png')
        result = generate_shadow(100, 100, output, blur_radius=0)
        assert result is True

        # Test with large blur
        output = os.path.join(temp_dir, 'shadow_large.png')
        result = generate_shadow(100, 100, output, blur_radius=50)
        assert result is True

    def test_generate_shadow_full_opacity(self, temp_dir):
        output = os.path.join(temp_dir, 'shadow.png')
        result = generate_shadow(100, 100, output, opacity=1.0)
        assert result is True

    def test_generate_shadow_with_offsets(self, temp_dir):
        output = os.path.join(temp_dir, 'shadow.png')
        result = generate_shadow(100, 100, output, offset_x=-10, offset_y=20)
        assert result is True

        from PIL import Image
        img = Image.open(output)
        # padding = 15*2 + max(10, 20) = 50
        assert img.width == 100 + 50 * 2
        assert img.height == 100 + 50 * 2


class TestDecorationOptionsShadowValidation:
    """Unit tests for DecorationOptions shadow validation."""

    def test_default_shadow_options(self):
        opts = DecorationOptions()
        assert opts.shadow_enabled is False
        assert opts.shadow_blur == 15
        assert opts.shadow_offset_x == 0
        assert opts.shadow_offset_y == 8
        assert opts.shadow_opacity == 0.4
        assert opts.shadow_color == '#000000'

    def test_shadow_enabled(self):
        opts = DecorationOptions(shadow_enabled=True)
        assert opts.shadow_enabled is True

    def test_shadow_blur_validation(self):
        DecorationOptions(shadow_blur=0)
        DecorationOptions(shadow_blur=100)

        with pytest.raises(ValueError, match='shadow_blur must be 0-100'):
            DecorationOptions(shadow_blur=-1)
        with pytest.raises(ValueError, match='shadow_blur must be 0-100'):
            DecorationOptions(shadow_blur=101)

    def test_shadow_offset_validation(self):
        DecorationOptions(shadow_offset_x=-200)
        DecorationOptions(shadow_offset_x=200)
        DecorationOptions(shadow_offset_y=-200)
        DecorationOptions(shadow_offset_y=200)

        with pytest.raises(ValueError, match='shadow_offset_x must be -200 to 200'):
            DecorationOptions(shadow_offset_x=-201)
        with pytest.raises(ValueError, match='shadow_offset_x must be -200 to 200'):
            DecorationOptions(shadow_offset_x=201)
        with pytest.raises(ValueError, match='shadow_offset_y must be -200 to 200'):
            DecorationOptions(shadow_offset_y=-201)
        with pytest.raises(ValueError, match='shadow_offset_y must be -200 to 200'):
            DecorationOptions(shadow_offset_y=201)

    def test_shadow_opacity_validation(self):
        DecorationOptions(shadow_opacity=0.0)
        DecorationOptions(shadow_opacity=1.0)

        with pytest.raises(ValueError, match='shadow_opacity must be 0.0-1.0'):
            DecorationOptions(shadow_opacity=-0.1)
        with pytest.raises(ValueError, match='shadow_opacity must be 0.0-1.0'):
            DecorationOptions(shadow_opacity=1.1)

    def test_shadow_color_normalization(self):
        opts = DecorationOptions(shadow_color='ff0000')
        assert opts.shadow_color == '#ff0000'


class TestAddShadowMethod:
    """Unit tests for DecorationPipeline.add_shadow() method."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_shadow_disabled_returns_false(self, temp_dir):
        opts = DecorationOptions(shadow_enabled=False)
        pipeline = DecorationPipeline(100, 100, opts, temp_dir)
        assert pipeline.add_shadow() is False
        assert pipeline.current_width == 100
        assert pipeline.current_height == 100

    def test_shadow_enabled_returns_true(self, temp_dir):
        opts = DecorationOptions(shadow_enabled=True, shadow_blur=15, shadow_offset_y=8)
        pipeline = DecorationPipeline(100, 100, opts, temp_dir)

        result = pipeline.add_shadow()

        assert result is True
        # padding = 15*2 + max(0, 8) = 38
        assert pipeline.current_width == 100 + 38 * 2
        assert pipeline.current_height == 100 + 38 * 2

    def test_shadow_creates_file(self, temp_dir):
        opts = DecorationOptions(shadow_enabled=True)
        pipeline = DecorationPipeline(100, 100, opts, temp_dir)

        pipeline.add_shadow()

        shadow_path = os.path.join(temp_dir, 'decoration_shadow.png')
        assert os.path.exists(shadow_path)
        assert shadow_path in pipeline.get_decoration_files()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
