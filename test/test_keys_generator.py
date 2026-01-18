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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
