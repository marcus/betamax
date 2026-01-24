"""Functional tests for decoration rendering pipeline.

Tests cover:
1. Integration tests that generate actual decoration images
2. Combined decorations (window_bar + border_radius + margin)
3. FFmpeg pipeline filter chain building
4. Decoration file cleanup
5. Pillow/ImageMagick fallback behavior
"""

import os
import sys
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.python.decorations import (
    generate_window_bar,
    generate_corner_mask,
    generate_shadow,
    get_available_backend,
    _check_pillow,
    _check_imagemagick,
    generate_window_bar_pillow,
    generate_window_bar_imagemagick,
    generate_corner_mask_pillow,
    generate_corner_mask_imagemagick,
)
from lib.python.ffmpeg_pipeline import (
    DecorationPipeline,
    DecorationOptions,
)


class TestBackendDetection:
    """Tests for Pillow/ImageMagick backend detection and fallback."""

    def test_get_available_backend(self):
        """Backend detection returns pillow, imagemagick, or None."""
        backend = get_available_backend()
        assert backend in ('pillow', 'imagemagick', None)

    def test_pillow_preferred_over_imagemagick(self):
        """Pillow is preferred when both are available."""
        # If Pillow is available, it should be returned
        if _check_pillow():
            assert get_available_backend() == 'pillow'

    def test_fallback_to_imagemagick(self):
        """Falls back to ImageMagick when Pillow unavailable."""
        with patch('lib.python.decorations._check_pillow', return_value=False):
            if _check_imagemagick():
                assert get_available_backend() == 'imagemagick'

    def test_returns_none_when_no_backend(self):
        """Returns None when neither backend available."""
        with patch('lib.python.decorations._check_pillow', return_value=False):
            with patch('lib.python.decorations._check_imagemagick', return_value=False):
                assert get_available_backend() is None


class TestWindowBarGeneration:
    """Integration tests for window bar image generation."""

    @pytest.fixture
    def temp_dir(self):
        """Create temp directory for test outputs."""
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_generate_window_bar_colorful(self, temp_dir):
        """Generate colorful style window bar."""
        output_path = os.path.join(temp_dir, 'bar.png')
        result = generate_window_bar(800, output_path, style='colorful')

        # Skip if no backend
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        assert result is True
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_generate_window_bar_rings(self, temp_dir):
        """Generate rings style window bar."""
        output_path = os.path.join(temp_dir, 'bar_rings.png')
        result = generate_window_bar(800, output_path, style='rings')

        if get_available_backend() is None:
            pytest.skip("No image backend available")

        assert result is True
        assert os.path.exists(output_path)

    def test_generate_window_bar_colorful_right(self, temp_dir):
        """Generate colorful_right style window bar."""
        output_path = os.path.join(temp_dir, 'bar_right.png')
        result = generate_window_bar(800, output_path, style='colorful_right')

        if get_available_backend() is None:
            pytest.skip("No image backend available")

        assert result is True
        assert os.path.exists(output_path)

    def test_generate_window_bar_custom_color(self, temp_dir):
        """Generate window bar with custom background color."""
        output_path = os.path.join(temp_dir, 'bar_custom.png')
        result = generate_window_bar(800, output_path, style='colorful', bg_color='#282a36')

        if get_available_backend() is None:
            pytest.skip("No image backend available")

        assert result is True
        assert os.path.exists(output_path)

    def test_generate_window_bar_custom_height(self, temp_dir):
        """Generate window bar with custom height."""
        output_path = os.path.join(temp_dir, 'bar_tall.png')
        result = generate_window_bar(800, output_path, style='colorful', bar_height=50)

        if get_available_backend() is None:
            pytest.skip("No image backend available")

        assert result is True
        assert os.path.exists(output_path)


class TestCornerMaskGeneration:
    """Integration tests for corner mask image generation."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_generate_corner_mask(self, temp_dir):
        """Generate corner mask with radius."""
        output_path = os.path.join(temp_dir, 'mask.png')
        result = generate_corner_mask(800, 600, output_path, radius=10)

        if get_available_backend() is None:
            pytest.skip("No image backend available")

        assert result is True
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_generate_corner_mask_various_radii(self, temp_dir):
        """Test different corner radii."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        for radius in [5, 10, 20, 50]:
            output_path = os.path.join(temp_dir, f'mask_{radius}.png')
            result = generate_corner_mask(200, 200, output_path, radius=radius)
            assert result is True
            assert os.path.exists(output_path)


class TestPipelineFilterChain:
    """Tests for FFmpeg filter chain building."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        # Create a dummy frame file
        frame_path = os.path.join(d, 'frame_00000.png')
        open(frame_path, 'w').close()
        yield d
        shutil.rmtree(d)

    def test_pipeline_init(self, temp_dir):
        """Pipeline initializes with valid params."""
        opts = DecorationOptions()
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        assert pipeline.frame_width == 800
        assert pipeline.frame_height == 600
        assert pipeline.current_width == 800
        assert pipeline.current_height == 600

    def test_pipeline_dimensions_updated_by_decorations(self, temp_dir):
        """Dimensions increase as decorations are added."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(
            window_bar_style='colorful',
            bar_height=30,
            padding=10,
            margin=20,
        )
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        initial_width = pipeline.current_width
        initial_height = pipeline.current_height

        # Add padding
        pipeline.add_padding()
        assert pipeline.current_width == initial_width + 20  # padding * 2
        assert pipeline.current_height == initial_height + 20

        # Add window bar
        pipeline.add_window_bar()
        assert pipeline.current_height == initial_height + 20 + 30  # padding + bar

        # Add margin
        pipeline.add_margin()
        assert pipeline.current_width == initial_width + 20 + 40  # padding + margin * 2

    def test_pipeline_no_decorations(self, temp_dir):
        """Pipeline with no decorations produces minimal filter."""
        opts = DecorationOptions()  # All defaults, no decorations
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        # None of these should add filters
        assert pipeline.add_padding() is False
        assert pipeline.add_margin() is False
        assert pipeline.add_window_bar() is False
        assert pipeline.add_border_radius() is False

    def test_pipeline_filter_stages_populated(self, temp_dir):
        """Filter stages list grows as decorations added."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(
            window_bar_style='colorful',
            padding=10,
        )
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        initial_stages = len(pipeline._filter_stages)

        pipeline.add_padding()
        assert len(pipeline._filter_stages) > initial_stages

        stages_after_padding = len(pipeline._filter_stages)
        pipeline.add_window_bar()
        assert len(pipeline._filter_stages) > stages_after_padding


class TestCombinedDecorations:
    """Tests for multiple decorations applied together."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        frame_path = os.path.join(d, 'frame_00000.png')
        open(frame_path, 'w').close()
        yield d
        shutil.rmtree(d)

    def test_all_decorations_combined(self, temp_dir):
        """Test window_bar + border_radius + padding + margin together."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(
            window_bar_style='colorful',
            bar_color='#282a36',
            bar_height=30,
            border_radius=8,
            padding=10,
            padding_color='#1e1e1e',
            margin=20,
            margin_color='#000000',
        )
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        # Apply all decorations in correct order
        assert pipeline.add_padding() is True
        assert pipeline.add_window_bar() is True
        assert pipeline.add_border_radius() is True
        assert pipeline.add_margin() is True

        # Verify final dimensions
        # Original: 800x600
        # After padding: 820x620 (+20 each)
        # After window_bar: 820x650 (+30 height)
        # After margin: 860x690 (+40 each)
        assert pipeline.current_width == 860
        assert pipeline.current_height == 690

    def test_decoration_files_created(self, temp_dir):
        """Decoration images are created in recording_dir."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(
            window_bar_style='colorful',
            border_radius=8,
        )
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        pipeline.add_window_bar()
        pipeline.add_border_radius()

        # Check decoration files were created
        assert os.path.exists(os.path.join(temp_dir, 'decoration_bar.png'))
        assert os.path.exists(os.path.join(temp_dir, 'decoration_mask.png'))

    def test_decoration_files_tracked(self, temp_dir):
        """Decoration files are tracked for cleanup."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(
            window_bar_style='colorful',
            border_radius=8,
        )
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        pipeline.add_window_bar()
        pipeline.add_border_radius()

        # Verify files are tracked
        assert len(pipeline._decoration_files) == 2
        for f in pipeline._decoration_files:
            assert os.path.exists(f)


class TestDecorationCleanup:
    """Tests for decoration file cleanup."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        frame_path = os.path.join(d, 'frame_00000.png')
        open(frame_path, 'w').close()
        yield d
        shutil.rmtree(d)

    def test_cleanup_removes_decoration_files(self, temp_dir):
        """cleanup_decoration_files removes generated images."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(
            window_bar_style='colorful',
            border_radius=8,
        )
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        pipeline.add_window_bar()
        pipeline.add_border_radius()

        # Verify files exist
        bar_path = os.path.join(temp_dir, 'decoration_bar.png')
        mask_path = os.path.join(temp_dir, 'decoration_mask.png')
        assert os.path.exists(bar_path)
        assert os.path.exists(mask_path)

        # Cleanup
        pipeline.cleanup_decoration_files()

        # Verify files removed
        assert not os.path.exists(bar_path)
        assert not os.path.exists(mask_path)

    def test_cleanup_handles_missing_files(self, temp_dir):
        """cleanup_decoration_files handles already-deleted files."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(window_bar_style='colorful')
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        pipeline.add_window_bar()

        # Manually delete the file
        bar_path = os.path.join(temp_dir, 'decoration_bar.png')
        os.remove(bar_path)

        # Cleanup should not raise
        pipeline.cleanup_decoration_files()


class TestDecorationOptionsValidation:
    """Tests for DecorationOptions dataclass validation."""

    def test_speed_bounds(self):
        """Speed validates within bounds."""
        # Valid speeds
        DecorationOptions(speed=0.25)
        DecorationOptions(speed=1.0)
        DecorationOptions(speed=4.0)

        # Invalid speeds
        with pytest.raises(ValueError):
            DecorationOptions(speed=0)
        with pytest.raises(ValueError):
            DecorationOptions(speed=-1)

    def test_frame_delay_bounds(self):
        """Frame delay validates within bounds."""
        DecorationOptions(frame_delay_ms=10)
        DecorationOptions(frame_delay_ms=10000)

        with pytest.raises(ValueError):
            DecorationOptions(frame_delay_ms=5)
        with pytest.raises(ValueError):
            DecorationOptions(frame_delay_ms=20000)


class TestPillowBackend:
    """Tests specific to Pillow backend."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_pillow_generates_valid_png(self, temp_dir):
        """Pillow generates valid PNG files."""
        if not _check_pillow():
            pytest.skip("Pillow not available")

        output_path = os.path.join(temp_dir, 'pillow_bar.png')
        result = generate_window_bar_pillow(800, output_path, style='colorful')

        assert result is True
        assert os.path.exists(output_path)

        # Verify it's a valid PNG by reading with Pillow
        from PIL import Image
        img = Image.open(output_path)
        assert img.size == (800, 30)  # Default bar height
        assert img.mode == 'RGBA'

    def test_pillow_corner_mask_grayscale(self, temp_dir):
        """Pillow corner mask is grayscale (L mode)."""
        if not _check_pillow():
            pytest.skip("Pillow not available")

        output_path = os.path.join(temp_dir, 'pillow_mask.png')
        result = generate_corner_mask_pillow(200, 200, output_path, radius=20)

        assert result is True

        from PIL import Image
        img = Image.open(output_path)
        assert img.size == (200, 200)
        assert img.mode == 'L'  # Grayscale for alpha mask


class TestImageMagickBackend:
    """Tests specific to ImageMagick backend."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_imagemagick_generates_valid_png(self, temp_dir):
        """ImageMagick generates valid PNG files."""
        if not _check_imagemagick():
            pytest.skip("ImageMagick not available")

        output_path = os.path.join(temp_dir, 'im_bar.png')
        result = generate_window_bar_imagemagick(800, output_path, style='colorful')

        assert result is True
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_imagemagick_timeout_handling(self, temp_dir):
        """ImageMagick handles timeouts gracefully."""
        if not _check_imagemagick():
            pytest.skip("ImageMagick not available")

        # Normal operation should not timeout
        output_path = os.path.join(temp_dir, 'timeout_test.png')
        result = generate_window_bar_imagemagick(800, output_path)
        assert result is True


class TestShadowPipeline:
    """Functional tests for shadow decoration pipeline."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        frame_path = os.path.join(d, 'frame_00000.png')
        open(frame_path, 'w').close()
        yield d
        shutil.rmtree(d)

    def test_shadow_disabled_no_effect(self, temp_dir):
        """Shadow disabled has no effect on dimensions."""
        opts = DecorationOptions(shadow_enabled=False)
        pipeline = DecorationPipeline(100, 100, opts, temp_dir)

        result = pipeline.add_shadow()

        assert result is False
        assert pipeline.current_width == 100
        assert pipeline.current_height == 100
        assert len(pipeline._decoration_files) == 0

    def test_shadow_enabled_increases_dimensions(self, temp_dir):
        """Shadow enabled increases dimensions by blur spread + offset."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(
            shadow_enabled=True,
            shadow_blur=15,
            shadow_offset_x=0,
            shadow_offset_y=8,
        )
        pipeline = DecorationPipeline(100, 100, opts, temp_dir)

        result = pipeline.add_shadow()

        assert result is True
        # Per-side: w = 100+30+30=160, h = 100+30+38=168
        assert pipeline.current_width == 160
        assert pipeline.current_height == 168

    def test_shadow_creates_decoration_file(self, temp_dir):
        """Shadow creates decoration_shadow.png file."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(shadow_enabled=True)
        pipeline = DecorationPipeline(100, 100, opts, temp_dir)

        pipeline.add_shadow()

        shadow_path = os.path.join(temp_dir, 'decoration_shadow.png')
        assert os.path.exists(shadow_path)
        assert shadow_path in pipeline._decoration_files

    def test_shadow_with_all_decorations(self, temp_dir):
        """Shadow works with all other decorations combined."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(
            window_bar_style='colorful',
            bar_height=30,
            padding=10,
            border_radius=8,
            margin=20,
            shadow_enabled=True,
            shadow_blur=15,
            shadow_offset_y=8,
        )
        pipeline = DecorationPipeline(800, 600, opts, temp_dir)

        # Apply all decorations in order
        assert pipeline.add_padding() is True
        assert pipeline.add_window_bar() is True
        assert pipeline.add_border_radius() is True
        assert pipeline.add_margin() is True
        assert pipeline.add_shadow() is True

        # Verify decoration files created
        assert os.path.exists(os.path.join(temp_dir, 'decoration_bar.png'))
        assert os.path.exists(os.path.join(temp_dir, 'decoration_mask.png'))
        assert os.path.exists(os.path.join(temp_dir, 'decoration_shadow.png'))

        # Verify final dimensions
        # Original: 800x600
        # After padding: 820x620 (+20)
        # After window_bar: 820x650 (+30 height)
        # After margin: 860x690 (+40)
        # After shadow (per-side): 860+30+30=920, 690+30+38=758
        assert pipeline.current_width == 920
        assert pipeline.current_height == 758

    def test_shadow_filter_chain_syntax(self, temp_dir):
        """Shadow adds correct filters to filter chain."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(shadow_enabled=True, shadow_blur=10)
        pipeline = DecorationPipeline(100, 100, opts, temp_dir)

        pipeline.add_shadow()
        _, filter_complex, _ = pipeline.build()

        # Should contain loop for shadow image
        assert 'loop=loop=-1:size=1' in filter_complex
        # Should contain overlay filter for compositing
        assert 'overlay=' in filter_complex

    def test_shadow_with_rounded_corners_uses_mask(self, temp_dir):
        """Shadow uses corner mask when border_radius is set."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(
            border_radius=10,
            shadow_enabled=True,
            shadow_blur=10,
        )
        pipeline = DecorationPipeline(100, 100, opts, temp_dir)

        # Add rounded corners first (creates mask)
        pipeline.add_border_radius()
        mask_path = os.path.join(temp_dir, 'decoration_mask.png')
        assert os.path.exists(mask_path)

        # Add shadow (should use the mask for shadow shape)
        result = pipeline.add_shadow()
        assert result is True

        # Verify shadow file created
        shadow_path = os.path.join(temp_dir, 'decoration_shadow.png')
        assert os.path.exists(shadow_path)

    def test_shadow_negative_offset(self, temp_dir):
        """Shadow handles negative offsets correctly."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(
            shadow_enabled=True,
            shadow_blur=10,
            shadow_offset_x=-15,
            shadow_offset_y=5,
        )
        pipeline = DecorationPipeline(100, 100, opts, temp_dir)

        result = pipeline.add_shadow()

        assert result is True
        # Per-side: w = 100+35+20=155, h = 100+20+25=145
        assert pipeline.current_width == 155
        assert pipeline.current_height == 145

    def test_shadow_cleanup(self, temp_dir):
        """Shadow file is cleaned up with other decorations."""
        if get_available_backend() is None:
            pytest.skip("No image backend available")

        opts = DecorationOptions(shadow_enabled=True)
        pipeline = DecorationPipeline(100, 100, opts, temp_dir)

        pipeline.add_shadow()

        shadow_path = os.path.join(temp_dir, 'decoration_shadow.png')
        assert os.path.exists(shadow_path)

        pipeline.cleanup_decoration_files()

        assert not os.path.exists(shadow_path)


class TestShadowImageGeneration:
    """Functional tests for shadow image generation."""

    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_shadow_is_rgba(self, temp_dir):
        """Generated shadow image is RGBA format."""
        if not _check_pillow():
            pytest.skip("Pillow not available")

        output_path = os.path.join(temp_dir, 'shadow.png')
        result = generate_shadow(100, 100, output_path)

        assert result is True

        from PIL import Image
        img = Image.open(output_path)
        assert img.mode == 'RGBA'

    def test_shadow_has_transparency(self, temp_dir):
        """Shadow image has transparent background."""
        if not _check_pillow():
            pytest.skip("Pillow not available")

        output_path = os.path.join(temp_dir, 'shadow.png')
        generate_shadow(100, 100, output_path, blur_radius=10, opacity=0.5)

        from PIL import Image
        img = Image.open(output_path)

        # Check corners are transparent (alpha = 0)
        alpha = img.split()[3]
        corner_alpha = alpha.getpixel((0, 0))
        assert corner_alpha == 0  # Corners should be fully transparent

    def test_shadow_color_applied(self, temp_dir):
        """Shadow uses specified color."""
        if not _check_pillow():
            pytest.skip("Pillow not available")

        output_path = os.path.join(temp_dir, 'red_shadow.png')
        generate_shadow(100, 100, output_path, color='#ff0000', blur_radius=5, opacity=1.0)

        from PIL import Image
        img = Image.open(output_path)

        # Check center pixel has red color
        r, g, b, a = img.getpixel((img.width // 2, img.height // 2))
        assert r == 255
        assert g == 0
        assert b == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
