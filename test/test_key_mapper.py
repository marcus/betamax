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


class TestUTF8Characters:
    """Test UTF-8 multi-byte character handling."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_2byte_utf8(self):
        # 'é' (U+00E9) is 2-byte UTF-8: 0xC3 0xA9
        result = self.mapper.parse_input('é'.encode('utf-8'))
        assert result == [('é', b'\xc3\xa9')]

    def test_3byte_utf8(self):
        # '€' (U+20AC) is 3-byte UTF-8: 0xE2 0x82 0xAC
        result = self.mapper.parse_input('€'.encode('utf-8'))
        assert result == [('€', b'\xe2\x82\xac')]

    def test_4byte_utf8(self):
        # '😀' (U+1F600) is 4-byte UTF-8: 0xF0 0x9F 0x98 0x80
        result = self.mapper.parse_input('😀'.encode('utf-8'))
        assert result == [('😀', b'\xf0\x9f\x98\x80')]

    def test_incomplete_utf8_waits(self):
        # Send first byte of 2-byte UTF-8 'é' only
        result = self.mapper.parse_input(b'\xc3')
        assert result == []
        assert self.mapper.has_pending()
        # Complete the sequence
        result = self.mapper.parse_input(b'\xa9')
        assert result == [('é', b'\xc3\xa9')]

    def test_invalid_utf8_as_hex(self):
        # Invalid UTF-8 continuation byte without start byte
        result = self.mapper.parse_input(b'\x80')
        assert result == [('0x80', b'\x80')]


class TestModifierArrowKeys:
    """Test Shift/Alt modifier arrow key mapping."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_shift_arrows(self):
        assert self.mapper.parse_input(b'\x1b[1;2A') == [('S-Up', b'\x1b[1;2A')]
        assert self.mapper.parse_input(b'\x1b[1;2B') == [('S-Down', b'\x1b[1;2B')]
        assert self.mapper.parse_input(b'\x1b[1;2C') == [('S-Right', b'\x1b[1;2C')]
        assert self.mapper.parse_input(b'\x1b[1;2D') == [('S-Left', b'\x1b[1;2D')]

    def test_alt_arrows(self):
        assert self.mapper.parse_input(b'\x1b[1;3A') == [('M-Up', b'\x1b[1;3A')]
        assert self.mapper.parse_input(b'\x1b[1;3B') == [('M-Down', b'\x1b[1;3B')]
        assert self.mapper.parse_input(b'\x1b[1;3C') == [('M-Right', b'\x1b[1;3C')]
        assert self.mapper.parse_input(b'\x1b[1;3D') == [('M-Left', b'\x1b[1;3D')]

    def test_ctrl_shift_arrows(self):
        assert self.mapper.parse_input(b'\x1b[1;6A') == [('C-S-Up', b'\x1b[1;6A')]
        assert self.mapper.parse_input(b'\x1b[1;6B') == [('C-S-Down', b'\x1b[1;6B')]
        assert self.mapper.parse_input(b'\x1b[1;6C') == [('C-S-Right', b'\x1b[1;6C')]
        assert self.mapper.parse_input(b'\x1b[1;6D') == [('C-S-Left', b'\x1b[1;6D')]

    def test_alt_shift_arrows(self):
        assert self.mapper.parse_input(b'\x1b[1;4A') == [('M-S-Up', b'\x1b[1;4A')]
        assert self.mapper.parse_input(b'\x1b[1;4B') == [('M-S-Down', b'\x1b[1;4B')]
        assert self.mapper.parse_input(b'\x1b[1;4C') == [('M-S-Right', b'\x1b[1;4C')]
        assert self.mapper.parse_input(b'\x1b[1;4D') == [('M-S-Left', b'\x1b[1;4D')]


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_empty_input(self):
        result = self.mapper.parse_input(b'')
        assert result == []

    def test_unknown_escape_sequence(self):
        # Unknown/malformed CSI sequence - treated as M-[ (Alt+bracket) then rest
        result = self.mapper.parse_input(b'\x1b[99X')
        # ESC+[ is parsed as Alt+[ since '[' is printable
        assert result[0] == ('M-[', b'\x1b[')
        # Remaining '99X' parsed as individual printable chars
        assert ('9', b'9') in result
        assert ('X', b'X') in result

    def test_alt_special_keys(self):
        # Alt+Enter: ESC followed by CR - parsed separately (CR not printable)
        result = self.mapper.parse_input(b'\x1b\r')
        assert result == [('Escape', b'\x1b'), ('Enter', b'\r')]

        # Alt+Tab: ESC followed by Tab - parsed separately (Tab not printable)
        result = self.mapper.parse_input(b'\x1b\t')
        assert result == [('Escape', b'\x1b'), ('Tab', b'\t')]


class TestCtrlFunctionKeys:
    """Test Ctrl+Function key mapping."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_ctrl_f1(self):
        result = self.mapper.parse_input(b'\x1b[1;5P')
        assert result == [('C-F1', b'\x1b[1;5P')]

    def test_ctrl_f2(self):
        result = self.mapper.parse_input(b'\x1b[1;5Q')
        assert result == [('C-F2', b'\x1b[1;5Q')]

    def test_ctrl_f5(self):
        result = self.mapper.parse_input(b'\x1b[15;5~')
        assert result == [('C-F5', b'\x1b[15;5~')]

    def test_ctrl_f12(self):
        result = self.mapper.parse_input(b'\x1b[24;5~')
        assert result == [('C-F12', b'\x1b[24;5~')]


class TestAltFunctionKeys:
    """Test Alt+Function key mapping."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_alt_f1(self):
        result = self.mapper.parse_input(b'\x1b[1;3P')
        assert result == [('M-F1', b'\x1b[1;3P')]

    def test_alt_f5(self):
        result = self.mapper.parse_input(b'\x1b[15;3~')
        assert result == [('M-F5', b'\x1b[15;3~')]

    def test_alt_f12(self):
        result = self.mapper.parse_input(b'\x1b[24;3~')
        assert result == [('M-F12', b'\x1b[24;3~')]


class TestShiftFunctionKeys:
    """Test Shift+Function key mapping."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_shift_f1(self):
        result = self.mapper.parse_input(b'\x1b[1;2P')
        assert result == [('S-F1', b'\x1b[1;2P')]

    def test_shift_f5(self):
        result = self.mapper.parse_input(b'\x1b[15;2~')
        assert result == [('S-F5', b'\x1b[15;2~')]


class TestBracketedPaste:
    """Test bracketed paste mode markers."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_paste_start(self):
        result = self.mapper.parse_input(b'\x1b[200~')
        assert result == [('PasteStart', b'\x1b[200~')]

    def test_paste_end(self):
        result = self.mapper.parse_input(b'\x1b[201~')
        assert result == [('PasteEnd', b'\x1b[201~')]

    def test_paste_with_content(self):
        result = self.mapper.parse_input(b'\x1b[200~hello\x1b[201~')
        assert result[0] == ('PasteStart', b'\x1b[200~')
        assert result[-1] == ('PasteEnd', b'\x1b[201~')


class TestApplicationKeypad:
    """Test application keypad mode sequences."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_keypad_numbers(self):
        assert self.mapper.parse_input(b'\x1bOp') == [('KP0', b'\x1bOp')]
        assert self.mapper.parse_input(b'\x1bOq') == [('KP1', b'\x1bOq')]
        assert self.mapper.parse_input(b'\x1bOy') == [('KP9', b'\x1bOy')]

    def test_keypad_operators(self):
        assert self.mapper.parse_input(b'\x1bOk') == [('KP+', b'\x1bOk')]
        assert self.mapper.parse_input(b'\x1bOm') == [('KP-', b'\x1bOm')]
        assert self.mapper.parse_input(b'\x1bOj') == [('KP*', b'\x1bOj')]
        assert self.mapper.parse_input(b'\x1bOo') == [('KP/', b'\x1bOo')]

    def test_keypad_enter(self):
        result = self.mapper.parse_input(b'\x1bOM')
        assert result == [('KPEnter', b'\x1bOM')]


class TestFocusEvents:
    """Test focus event sequences."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_focus_in(self):
        result = self.mapper.parse_input(b'\x1b[I')
        assert result == [('FocusIn', b'\x1b[I')]

    def test_focus_out(self):
        result = self.mapper.parse_input(b'\x1b[O')
        assert result == [('FocusOut', b'\x1b[O')]


class TestNavigationWithModifiers:
    """Test navigation keys with modifiers."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_ctrl_page_up(self):
        result = self.mapper.parse_input(b'\x1b[5;5~')
        assert result == [('C-PPage', b'\x1b[5;5~')]

    def test_ctrl_home(self):
        result = self.mapper.parse_input(b'\x1b[1;5H')
        assert result == [('C-Home', b'\x1b[1;5H')]

    def test_shift_end(self):
        result = self.mapper.parse_input(b'\x1b[1;2F')
        assert result == [('S-End', b'\x1b[1;2F')]


class TestCtrlAltArrows:
    """Test Ctrl+Alt arrow key mapping."""

    def setup_method(self):
        self.mapper = KeyMapper()

    def test_ctrl_alt_arrows(self):
        assert self.mapper.parse_input(b'\x1b[1;7A') == [('C-M-Up', b'\x1b[1;7A')]
        assert self.mapper.parse_input(b'\x1b[1;7B') == [('C-M-Down', b'\x1b[1;7B')]
        assert self.mapper.parse_input(b'\x1b[1;7C') == [('C-M-Right', b'\x1b[1;7C')]
        assert self.mapper.parse_input(b'\x1b[1;7D') == [('C-M-Left', b'\x1b[1;7D')]


class TestResponseFiltering:
    """Test KeyMapper with response filtering enabled."""

    def test_filter_responses_disabled_by_default(self):
        mapper = KeyMapper()
        # CPR should not be filtered by default
        result = mapper.parse_input(b'\x1b[24;80R')
        # Without filtering, this gets parsed as M-[ and then individual chars
        assert len(result) > 0

    def test_filter_responses_enabled(self):
        mapper = KeyMapper(filter_responses=True)
        # CPR should be filtered
        result = mapper.parse_input(b'\x1b[24;80R')
        assert result == []

    def test_filter_keeps_user_input(self):
        mapper = KeyMapper(filter_responses=True)
        # Mix of CPR and user input
        result = mapper.parse_input(b'hello\x1b[24;80Rworld')
        key_names = [r[0] for r in result]
        assert 'h' in key_names
        assert 'e' in key_names
        assert 'l' in key_names
        assert 'o' in key_names
        assert 'w' in key_names
        assert 'r' in key_names
        assert 'd' in key_names


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
