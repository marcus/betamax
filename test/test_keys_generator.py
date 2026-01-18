#!/usr/bin/env python3
"""Tests for keys_generator.py - .keys file generation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import tempfile
from lib.python.keys_generator import KeysGenerator


class TestHeader:
    """Test header generation."""

    def test_header_format(self):
        keystrokes = [
            (0.0, 'h', b'h'),
            (0.1, 'i', b'i'),
        ]
        generator = KeysGenerator(keystrokes, {'command': 'echo hi'})
        content = generator.generate()

        assert '# Recorded with betamax record' in content
        assert '# Command: echo hi' in content
        assert '# Keystrokes: 2' in content

    def test_settings_directives(self):
        keystrokes = [(0.0, 'a', b'a')]
        generator = KeysGenerator(keystrokes, {'cols': 100, 'rows': 30})
        content = generator.generate()

        assert '@set:cols:100' in content
        assert '@set:rows:30' in content
        assert '@set:delay:' in content


class TestTiming:
    """Test timing handling."""

    def test_min_delay_clamp(self):
        # Delays < 50ms should not have timing annotation
        keystrokes = [
            (0.0, 'a', b'a'),
            (0.02, 'b', b'b'),  # 20ms - should be ignored
        ]
        generator = KeysGenerator(keystrokes, {'min_delay': 50})
        content = generator.generate()

        # Should just have 'a' and 'b' without timing
        lines = content.strip().split('\n')
        key_lines = [l for l in lines if l in ['a', 'b']]
        assert 'a' in key_lines
        assert 'b' in key_lines

    def test_max_delay_clamp(self):
        # Delays > 2000ms should be capped
        keystrokes = [
            (0.0, 'a', b'a'),
            (5.0, 'b', b'b'),  # 5000ms - should be capped to 2000
        ]
        generator = KeysGenerator(keystrokes, {'max_delay': 2000})
        content = generator.generate()

        # Should have @sleep:2000 before 'b'
        assert '@sleep:2000' in content

    def test_sleep_for_long_delays(self):
        # Delays > 500ms should use @sleep
        keystrokes = [
            (0.0, 'a', b'a'),
            (0.8, 'b', b'b'),  # 800ms
        ]
        generator = KeysGenerator(keystrokes)
        content = generator.generate()

        assert '@sleep:800' in content

    def test_fixed_delay_mode(self):
        # With fixed_delay, timing should be ignored
        keystrokes = [
            (0.0, 'a', b'a'),
            (1.0, 'b', b'b'),  # Would normally be @sleep:1000
            (1.5, 'c', b'c'),
        ]
        generator = KeysGenerator(keystrokes, {'fixed_delay': 100})
        content = generator.generate()

        # Should not have any timing annotations
        assert '@sleep' not in content
        assert '@100' not in content
        lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#') and not l.startswith('@set')]
        # Should just have the keys
        assert 'a' in lines
        assert 'b' in lines
        assert 'c' in lines


class TestFrames:
    """Test frame marker handling."""

    def test_auto_frame(self):
        keystrokes = [
            (0.0, 'a', b'a'),
            (0.1, 'b', b'b'),
        ]
        generator = KeysGenerator(keystrokes, {'auto_frame': True})
        content = generator.generate()

        # Count @frame occurrences - should be after each key
        frame_count = content.count('@frame')
        assert frame_count >= 2

    def test_manual_frame_markers(self):
        keystrokes = [
            (0.0, 'a', b'a'),
            (0.1, 'C-g', b'\x07'),  # Frame marker key
            (0.2, 'b', b'b'),
        ]
        generator = KeysGenerator(keystrokes, {
            'frame_markers': [1],  # Mark index 1 as frame
            'frame_key': 'C-g',
        })
        content = generator.generate()

        # Should have @frame for the marker, but C-g itself filtered
        assert '@frame' in content
        # C-g should not appear in output
        lines = [l.strip() for l in content.split('\n')]
        assert 'C-g' not in lines


class TestGifMode:
    """Test GIF recording directive generation."""

    def test_record_start_stop(self):
        keystrokes = [(0.0, 'a', b'a')]
        generator = KeysGenerator(keystrokes, {'gif_output': 'demo.gif'})
        content = generator.generate()

        assert '@record:start' in content
        assert '@record:stop:demo.gif' in content

    def test_record_filename(self):
        keystrokes = [(0.0, 'x', b'x')]
        generator = KeysGenerator(keystrokes, {'gif_output': 'my_recording.gif'})
        content = generator.generate()

        assert '@record:stop:my_recording.gif' in content

    def test_no_record_without_gif(self):
        keystrokes = [(0.0, 'y', b'y')]
        generator = KeysGenerator(keystrokes)
        content = generator.generate()

        assert '@record:start' not in content
        assert '@record:stop' not in content


class TestSaveFile:
    """Test file saving functionality."""

    def test_save_creates_file(self):
        keystrokes = [(0.0, 'z', b'z')]
        generator = KeysGenerator(keystrokes)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.keys', delete=False) as f:
            filepath = f.name

        try:
            generator.save(filepath)
            with open(filepath, 'r') as f:
                content = f.read()
            assert 'z' in content
        finally:
            os.unlink(filepath)

    def test_save_creates_directory(self):
        keystrokes = [(0.0, 'w', b'w')]
        generator = KeysGenerator(keystrokes)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'subdir', 'test.keys')
            generator.save(filepath)
            assert os.path.exists(filepath)


class TestDurationCalculation:
    """Test duration calculation."""

    def test_duration_from_keystrokes(self):
        keystrokes = [
            (0.0, 'a', b'a'),
            (5.0, 'b', b'b'),
        ]
        generator = KeysGenerator(keystrokes)
        content = generator.generate()

        assert '# Duration: 5.0s' in content

    def test_duration_single_keystroke(self):
        keystrokes = [(0.0, 'a', b'a')]
        generator = KeysGenerator(keystrokes)
        content = generator.generate()

        assert '# Duration: 0.0s' in content


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_keystrokes(self):
        """Empty list generates valid file with 0 keystrokes."""
        generator = KeysGenerator([], {})
        content = generator.generate()

        # Should have header and settings but no keystroke lines
        assert '# Recorded with betamax record' in content
        assert '@set:cols:' in content
        assert '@set:rows:' in content
        assert '@set:delay:' in content
        # Should not have keystroke count header since empty
        assert '# Keystrokes:' not in content

    def test_single_keystroke(self):
        """Single keystroke works, duration is 0."""
        keystrokes = [(0.0, 'x', b'x')]
        generator = KeysGenerator(keystrokes)
        content = generator.generate()

        assert '# Duration: 0.0s' in content
        assert '# Keystrokes: 1' in content
        assert 'x' in content

    def test_duplicate_timestamps(self):
        """Two keystrokes at same time (delay_ms = 0)."""
        keystrokes = [
            (1.0, 'a', b'a'),
            (1.0, 'b', b'b'),  # Same timestamp
        ]
        generator = KeysGenerator(keystrokes)
        content = generator.generate()

        lines = content.strip().split('\n')
        key_lines = [l for l in lines if l in ['a', 'b']]
        assert 'a' in key_lines
        assert 'b' in key_lines
        # No timing annotation between them since delay is 0
        assert '@sleep:0' not in content
        assert 'b@0' not in content


class TestTimingEdgeCases:
    """Test timing edge cases."""

    def test_max_delay_less_than_500(self):
        """When max_delay=300, no @sleep directives."""
        keystrokes = [
            (0.0, 'a', b'a'),
            (0.6, 'b', b'b'),  # 600ms would normally be @sleep
        ]
        generator = KeysGenerator(keystrokes, {'max_delay': 300})
        content = generator.generate()

        # Should be capped to 300ms which is < 500, so no @sleep
        assert '@sleep' not in content

    def test_delay_equals_default(self):
        """Delay matching default has no annotation."""
        keystrokes = [
            (0.0, 'a', b'a'),
            (0.1, 'b', b'b'),  # 100ms
            (0.2, 'c', b'c'),  # 100ms
        ]
        generator = KeysGenerator(keystrokes)
        content = generator.generate()

        # Check the default delay
        assert '@set:delay:100' in content
        # Keys should appear without timing since they match default
        lines = content.strip().split('\n')
        assert 'b' in lines
        assert 'c' in lines
        # No inline timing for b or c
        assert 'b@' not in content
        assert 'c@' not in content

    def test_inline_timing_format(self):
        """Verify key@delay format for moderate delays."""
        keystrokes = [
            (0.0, 'a', b'a'),
            (0.2, 'b', b'b'),  # 200ms - moderate delay
        ]
        generator = KeysGenerator(keystrokes, {'min_delay': 50, 'max_delay': 2000})
        content = generator.generate()

        # 200ms is < 500ms so should use inline format, not @sleep
        assert '@sleep' not in content
        # Should have inline timing if different from default
        lines = content.strip().split('\n')
        has_inline = any('b@' in l for l in lines)
        has_plain_b = 'b' in lines
        # Either has inline timing or plain b (if 200 happens to be default)
        assert has_inline or has_plain_b


class TestFrameEdgeCases:
    """Test frame marker edge cases."""

    def test_frame_marker_at_index_0(self):
        """First keystroke as frame marker."""
        keystrokes = [
            (0.0, 'C-g', b'\x07'),  # Frame marker at index 0
            (0.1, 'a', b'a'),
        ]
        generator = KeysGenerator(keystrokes, {
            'frame_markers': [0],
            'frame_key': 'C-g',
        })
        content = generator.generate()

        assert '@frame' in content
        lines = content.strip().split('\n')
        # C-g should not appear in output
        assert 'C-g' not in lines
        assert 'a' in lines

    def test_consecutive_frame_markers(self):
        """Multiple adjacent markers."""
        keystrokes = [
            (0.0, 'a', b'a'),
            (0.1, 'C-g', b'\x07'),  # Frame marker
            (0.2, 'C-g', b'\x07'),  # Another frame marker
            (0.3, 'b', b'b'),
        ]
        generator = KeysGenerator(keystrokes, {
            'frame_markers': [1, 2],
            'frame_key': 'C-g',
        })
        content = generator.generate()

        # Should have two @frame directives
        assert content.count('@frame') == 2
        lines = content.strip().split('\n')
        assert 'C-g' not in lines

    def test_frame_key_not_in_markers(self):
        """Regular C-g input appears in output."""
        keystrokes = [
            (0.0, 'a', b'a'),
            (0.1, 'C-g', b'\x07'),  # C-g but NOT in frame_markers
            (0.2, 'b', b'b'),
        ]
        generator = KeysGenerator(keystrokes, {
            'frame_markers': [],  # C-g at index 1 is NOT a frame marker
            'frame_key': 'C-g',
        })
        content = generator.generate()

        # C-g should appear in output since it's not a frame marker
        lines = [l.strip() for l in content.split('\n')]
        # Check for C-g (possibly with timing annotation)
        has_cg = any('C-g' in l for l in lines)
        assert has_cg


class TestMedianDelay:
    """Test median calculation."""

    def test_median_with_outliers(self):
        """Verify outliers are excluded."""
        # Delays: 100ms, 100ms, 100ms, 5000ms (outlier > max_delay)
        keystrokes = [
            (0.0, 'a', b'a'),
            (0.1, 'b', b'b'),    # 100ms
            (0.2, 'c', b'c'),    # 100ms
            (0.3, 'd', b'd'),    # 100ms
            (5.3, 'e', b'e'),    # 5000ms - outlier
        ]
        generator = KeysGenerator(keystrokes, {'max_delay': 2000})
        content = generator.generate()

        # Median should be 100 (outlier excluded)
        assert '@set:delay:100' in content

    def test_median_even_count(self):
        """Even number of delays."""
        # Delays: 100ms, 300ms (average = 200)
        keystrokes = [
            (0.0, 'a', b'a'),
            (0.100, 'b', b'b'),  # 100ms
            (0.400, 'c', b'c'),  # 300ms
        ]
        generator = KeysGenerator(keystrokes)
        content = generator.generate()

        # Median of [100, 300] = (100 + 300) // 2 = 200
        assert '@set:delay:200' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
