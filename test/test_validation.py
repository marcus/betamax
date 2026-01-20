"""Tests for input validation in decorations and ffmpeg_pipeline."""

import os
import pytest
import sys
import tempfile

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.python.decorations import (
    _validate_hex_color,
    _validate_dimensions,
    _validate_border_radius,
    _validate_output_path,
)
from lib.python.ffmpeg_pipeline import DecorationOptions


class TestHexColorValidation:
    """Tests for _validate_hex_color."""

    def test_valid_6_digit_with_hash(self):
        assert _validate_hex_color('#ff0000') == '#ff0000'

    def test_valid_6_digit_without_hash(self):
        assert _validate_hex_color('ff0000') == '#ff0000'

    def test_valid_3_digit_with_hash(self):
        assert _validate_hex_color('#f00') == '#f00'

    def test_valid_3_digit_without_hash(self):
        assert _validate_hex_color('f00') == '#f00'

    def test_empty_raises(self):
        with pytest.raises(ValueError, match='cannot be empty'):
            _validate_hex_color('')

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError, match='Invalid hex color length'):
            _validate_hex_color('#ff00')  # 4 digits

    def test_invalid_chars_raises(self):
        with pytest.raises(ValueError, match='non-hex characters'):
            _validate_hex_color('#gggggg')


class TestDimensionsValidation:
    """Tests for _validate_dimensions."""

    def test_valid_dimension(self):
        assert _validate_dimensions(100, 'width') == 100

    def test_min_value(self):
        assert _validate_dimensions(1, 'width') == 1

    def test_max_value(self):
        assert _validate_dimensions(10000, 'width') == 10000

    def test_below_min_raises(self):
        with pytest.raises(ValueError, match='must be between'):
            _validate_dimensions(0, 'width')

    def test_above_max_raises(self):
        with pytest.raises(ValueError, match='must be between'):
            _validate_dimensions(10001, 'width')

    def test_non_int_raises(self):
        with pytest.raises(TypeError, match='must be int'):
            _validate_dimensions(100.5, 'width')


class TestBorderRadiusValidation:
    """Tests for _validate_border_radius."""

    def test_valid_radius(self):
        assert _validate_border_radius(10, 100, 100) == 10

    def test_max_radius(self):
        assert _validate_border_radius(50, 100, 100) == 50

    def test_negative_raises(self):
        with pytest.raises(ValueError, match='cannot be negative'):
            _validate_border_radius(-1, 100, 100)

    def test_exceeds_max_raises(self):
        with pytest.raises(ValueError, match='exceeds max'):
            _validate_border_radius(51, 100, 100)

    def test_uses_smaller_dimension(self):
        # max = min(200, 100) // 2 = 50
        assert _validate_border_radius(50, 200, 100) == 50
        with pytest.raises(ValueError, match='exceeds max'):
            _validate_border_radius(51, 200, 100)


class TestOutputPathValidation:
    """Tests for _validate_output_path."""

    def test_valid_absolute_path(self):
        result = _validate_output_path('/tmp/test.png')
        assert result == '/tmp/test.png'

    def test_null_byte_raises(self):
        with pytest.raises(ValueError, match='null bytes'):
            _validate_output_path('/tmp/test\x00.png')

    def test_empty_raises(self):
        with pytest.raises(ValueError, match='cannot be empty'):
            _validate_output_path('')

    def test_within_recording_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test.png')
            result = _validate_output_path(path, tmpdir)
            assert result == path

    def test_outside_recording_dir_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match='must be within'):
                _validate_output_path('/etc/passwd', tmpdir)


class TestDecorationOptionsValidation:
    """Tests for DecorationOptions validation in __post_init__."""

    def test_valid_defaults(self):
        opts = DecorationOptions()
        assert opts.bar_color == '#1e1e1e'
        assert opts.speed == 1.0

    def test_invalid_bar_color_raises(self):
        with pytest.raises(ValueError, match='Invalid hex color'):
            DecorationOptions(bar_color='invalid')

    def test_invalid_margin_color_raises(self):
        with pytest.raises(ValueError, match='Invalid hex color'):
            DecorationOptions(margin_color='xyz')

    def test_negative_bar_height_raises(self):
        with pytest.raises(ValueError, match='cannot be negative'):
            DecorationOptions(bar_height=-1)

    def test_negative_border_radius_raises(self):
        with pytest.raises(ValueError, match='cannot be negative'):
            DecorationOptions(border_radius=-1)

    def test_negative_margin_raises(self):
        with pytest.raises(ValueError, match='cannot be negative'):
            DecorationOptions(margin=-1)

    def test_negative_padding_raises(self):
        with pytest.raises(ValueError, match='cannot be negative'):
            DecorationOptions(padding=-1)

    def test_zero_speed_raises(self):
        with pytest.raises(ValueError, match='must be positive'):
            DecorationOptions(speed=0)

    def test_negative_speed_raises(self):
        with pytest.raises(ValueError, match='must be positive'):
            DecorationOptions(speed=-1)

    def test_speed_too_high_raises(self):
        with pytest.raises(ValueError, match='too high'):
            DecorationOptions(speed=101)

    def test_frame_delay_too_low_raises(self):
        with pytest.raises(ValueError, match='too low'):
            DecorationOptions(frame_delay_ms=5)

    def test_frame_delay_too_high_raises(self):
        with pytest.raises(ValueError, match='too high'):
            DecorationOptions(frame_delay_ms=20000)
