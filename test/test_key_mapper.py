#!/usr/bin/env python3
"""Tests for key_mapper.py - escape sequence to key name conversion."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from lib.python.key_mapper import KeyMapper


class TestArrowKeys:
    """Test arrow key mapping."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_up_arrow(self):
        result = self.mapper.parse_input(b'\x1b[A')
        assert result == [('Up', b'\x1b[A')]

    def test_down_arrow(self):
        result = self.mapper.parse_input(b'\x1b[B')
        assert result == [('Down', b'\x1b[B')]

    def test_right_arrow(self):
        result = self.mapper.parse_input(b'\x1b[C')
        assert result == [('Right', b'\x1b[C')]

    def test_left_arrow(self):
        result = self.mapper.parse_input(b'\x1b[D')
        assert result == [('Left', b'\x1b[D')]


class TestFunctionKeys:
    """Test function key mapping."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_f1(self):
        result = self.mapper.parse_input(b'\x1bOP')
        assert result == [('F1', b'\x1bOP')]

    def test_f2(self):
        result = self.mapper.parse_input(b'\x1bOQ')
        assert result == [('F2', b'\x1bOQ')]

    def test_f3(self):
        result = self.mapper.parse_input(b'\x1bOR')
        assert result == [('F3', b'\x1bOR')]

    def test_f4(self):
        result = self.mapper.parse_input(b'\x1bOS')
        assert result == [('F4', b'\x1bOS')]

    def test_f5(self):
        result = self.mapper.parse_input(b'\x1b[15~')
        assert result == [('F5', b'\x1b[15~')]

    def test_f10(self):
        result = self.mapper.parse_input(b'\x1b[21~')
        assert result == [('F10', b'\x1b[21~')]

    def test_f12(self):
        result = self.mapper.parse_input(b'\x1b[24~')
        assert result == [('F12', b'\x1b[24~')]


class TestControlKeys:
    """Test control key mapping."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_ctrl_a(self):
        result = self.mapper.parse_input(b'\x01')
        assert result == [('C-a', b'\x01')]

    def test_ctrl_c(self):
        result = self.mapper.parse_input(b'\x03')
        assert result == [('C-c', b'\x03')]

    def test_ctrl_z(self):
        result = self.mapper.parse_input(b'\x1a')
        assert result == [('C-z', b'\x1a')]

    def test_ctrl_d(self):
        result = self.mapper.parse_input(b'\x04')
        assert result == [('C-d', b'\x04')]


class TestSpecialKeys:
    """Test special key mapping."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_escape_with_timeout(self):
        # Send escape, then flush (simulating timeout)
        self.mapper.parse_input(b'\x1b')
        result = self.mapper.flush()
        assert result == [('Escape', b'\x1b')]

    def test_backspace(self):
        result = self.mapper.parse_input(b'\x7f')
        assert result == [('BSpace', b'\x7f')]

    def test_enter_cr(self):
        result = self.mapper.parse_input(b'\r')
        assert result == [('Enter', b'\r')]

    def test_tab(self):
        result = self.mapper.parse_input(b'\t')
        assert result == [('Tab', b'\t')]

    def test_space(self):
        result = self.mapper.parse_input(b' ')
        assert result == [('Space', b' ')]

    def test_backtab(self):
        result = self.mapper.parse_input(b'\x1b[Z')
        assert result == [('BTab', b'\x1b[Z')]


class TestAltKeys:
    """Test Alt/Meta key mapping."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_alt_a(self):
        result = self.mapper.parse_input(b'\x1ba')
        assert result == [('M-a', b'\x1ba')]

    def test_alt_x(self):
        result = self.mapper.parse_input(b'\x1bx')
        assert result == [('M-x', b'\x1bx')]


class TestNavigationKeys:
    """Test navigation key mapping."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_home(self):
        result = self.mapper.parse_input(b'\x1b[H')
        assert result == [('Home', b'\x1b[H')]

    def test_home_alt(self):
        result = self.mapper.parse_input(b'\x1bOH')
        assert result == [('Home', b'\x1bOH')]

    def test_end(self):
        result = self.mapper.parse_input(b'\x1b[F')
        assert result == [('End', b'\x1b[F')]

    def test_page_up(self):
        result = self.mapper.parse_input(b'\x1b[5~')
        assert result == [('PPage', b'\x1b[5~')]

    def test_page_down(self):
        result = self.mapper.parse_input(b'\x1b[6~')
        assert result == [('NPage', b'\x1b[6~')]

    def test_insert(self):
        result = self.mapper.parse_input(b'\x1b[2~')
        assert result == [('IC', b'\x1b[2~')]

    def test_delete(self):
        result = self.mapper.parse_input(b'\x1b[3~')
        assert result == [('DC', b'\x1b[3~')]


class TestCtrlArrowKeys:
    """Test Ctrl+Arrow key mapping."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_ctrl_up(self):
        result = self.mapper.parse_input(b'\x1b[1;5A')
        assert result == [('C-Up', b'\x1b[1;5A')]

    def test_ctrl_down(self):
        result = self.mapper.parse_input(b'\x1b[1;5B')
        assert result == [('C-Down', b'\x1b[1;5B')]

    def test_ctrl_right(self):
        result = self.mapper.parse_input(b'\x1b[1;5C')
        assert result == [('C-Right', b'\x1b[1;5C')]

    def test_ctrl_left(self):
        result = self.mapper.parse_input(b'\x1b[1;5D')
        assert result == [('C-Left', b'\x1b[1;5D')]


class TestPrintableChars:
    """Test printable character handling."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_lowercase_letters(self):
        result = self.mapper.parse_input(b'abc')
        assert result == [('a', b'a'), ('b', b'b'), ('c', b'c')]

    def test_uppercase_letters(self):
        result = self.mapper.parse_input(b'ABC')
        assert result == [('A', b'A'), ('B', b'B'), ('C', b'C')]

    def test_numbers(self):
        result = self.mapper.parse_input(b'123')
        assert result == [('1', b'1'), ('2', b'2'), ('3', b'3')]

    def test_symbols(self):
        result = self.mapper.parse_input(b'!@#')
        assert result == [('!', b'!'), ('@', b'@'), ('#', b'#')]


class TestMixedInput:
    """Test mixed input sequences."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_text_with_arrow(self):
        result = self.mapper.parse_input(b'hello\x1b[Aworld')
        expected = [
            ('h', b'h'), ('e', b'e'), ('l', b'l'), ('l', b'l'), ('o', b'o'),
            ('Up', b'\x1b[A'),
            ('w', b'w'), ('o', b'o'), ('r', b'r'), ('l', b'l'), ('d', b'd'),
        ]
        assert result == expected

    def test_text_with_enter(self):
        result = self.mapper.parse_input(b'cmd\r')
        assert result == [('c', b'c'), ('m', b'm'), ('d', b'd'), ('Enter', b'\r')]


class TestBuffering:
    """Test incomplete sequence buffering."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_incomplete_escape_waits(self):
        # Just escape - should be buffered
        result = self.mapper.parse_input(b'\x1b')
        assert result == []
        assert self.mapper.has_pending()

    def test_complete_after_more_data(self):
        # Send escape
        self.mapper.parse_input(b'\x1b')
        # Send rest of arrow key
        result = self.mapper.parse_input(b'[A')
        assert result == [('Up', b'\x1b[A')]

    def test_flush_incomplete(self):
        self.mapper.parse_input(b'\x1b')
        result = self.mapper.flush()
        assert result == [('Escape', b'\x1b')]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
