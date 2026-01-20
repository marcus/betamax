#!/usr/bin/env python3
"""Tests for response_filter.py - terminal response filtering."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from lib.python.response_filter import ResponseFilter, filter_terminal_responses


class TestCursorPositionReports:
    """Test filtering of cursor position report sequences."""

    def setup_method(self):
        self.filter = ResponseFilter()

    def test_simple_cpr(self):
        """Filter ESC[row;colR cursor position reports."""
        data = b'\x1b[24;80R'
        result = self.filter.filter(data)
        assert result == b''

    def test_cpr_with_surrounding_data(self):
        """CPR in middle of user input."""
        data = b'hello\x1b[10;20Rworld'
        result = self.filter.filter(data)
        assert result == b'helloworld'

    def test_multiple_cprs(self):
        """Multiple CPRs in one stream."""
        data = b'\x1b[1;1R\x1b[24;80R\x1b[5;10R'
        result = self.filter.filter(data)
        assert result == b''


class TestDeviceAttributeResponses:
    """Test filtering of device attribute responses."""

    def setup_method(self):
        self.filter = ResponseFilter()

    def test_primary_da(self):
        """Filter primary DA response ESC[?...c."""
        data = b'\x1b[?64;1;2;6;9;15;18;21;22c'
        result = self.filter.filter(data)
        assert result == b''

    def test_secondary_da(self):
        """Filter secondary DA response ESC[>...c."""
        data = b'\x1b[>0;136;0c'
        result = self.filter.filter(data)
        assert result == b''

    def test_tertiary_da(self):
        """Filter tertiary DA response ESC[=...c."""
        data = b'\x1b[=1;2;3c'
        result = self.filter.filter(data)
        assert result == b''


class TestOSCResponses:
    """Test filtering of OSC (Operating System Command) responses."""

    def setup_method(self):
        self.filter = ResponseFilter()

    def test_osc_with_bel(self):
        """Filter OSC response with BEL terminator."""
        data = b'\x1b]11;rgb:0000/0000/0000\x07'
        result = self.filter.filter(data)
        assert result == b''

    def test_osc_with_st(self):
        """Filter OSC response with ST (ESC\\) terminator."""
        data = b'\x1b]11;rgb:ffff/ffff/ffff\x1b\\'
        result = self.filter.filter(data)
        assert result == b''

    def test_osc_color_query(self):
        """Filter color query response."""
        data = b'\x1b]4;1;rgb:cd/00/00\x07'
        result = self.filter.filter(data)
        assert result == b''


class TestDECRPM:
    """Test filtering of DECRPM (DEC Report Mode) responses."""

    def setup_method(self):
        self.filter = ResponseFilter()

    def test_decrpm(self):
        """Filter DECRPM response ESC[?N;M$y."""
        data = b'\x1b[?2026;2$y'
        result = self.filter.filter(data)
        assert result == b''

    def test_decrpm_with_user_input(self):
        """DECRPM mixed with user input."""
        data = b'vim\x1b[?2026;1$y:q!\r'
        result = self.filter.filter(data)
        assert result == b'vim:q!\r'


class TestDSRResponses:
    """Test filtering of DSR (Device Status Report) responses."""

    def setup_method(self):
        self.filter = ResponseFilter()

    def test_dsr_ok(self):
        """Filter DSR OK response."""
        data = b'\x1b[0n'
        result = self.filter.filter(data)
        assert result == b''

    def test_dsr_error(self):
        """Filter DSR error response."""
        data = b'\x1b[3n'
        result = self.filter.filter(data)
        assert result == b''


class TestXTWINOPS:
    """Test filtering of XTWINOPS responses."""

    def setup_method(self):
        self.filter = ResponseFilter()

    def test_xtwinops_size(self):
        """Filter XTWINOPS text area size response."""
        data = b'\x1b[8;24;80t'
        result = self.filter.filter(data)
        assert result == b''

    def test_xtwinops_generic(self):
        """Filter generic XTWINOPS response."""
        data = b'\x1b[4;480;640t'
        result = self.filter.filter(data)
        assert result == b''


class TestDebugLogging:
    """Test debug logging functionality."""

    def test_debug_logs_filtered(self):
        """Debug mode logs what was filtered."""
        filter = ResponseFilter(debug=True)
        data = b'\x1b[24;80R'
        filter.filter(data)
        log = filter.get_filtered_log()
        assert len(log) == 1
        assert log[0][0] == 'CPR'
        assert log[0][1] == b'\x1b[24;80R'

    def test_filter_with_log(self):
        """filter_with_log returns both filtered data and log."""
        filter = ResponseFilter()
        data = b'hello\x1b[1;1Rworld'
        result, log = filter.filter_with_log(data)
        assert result == b'helloworld'
        assert len(log) == 1
        assert log[0][0] == 'CPR'

    def test_clear_log(self):
        """clear_log empties the log."""
        filter = ResponseFilter(debug=True)
        filter.filter(b'\x1b[1;1R')
        filter.clear_log()
        assert filter.get_filtered_log() == []


class TestConvenienceFunction:
    """Test the convenience function."""

    def test_filter_terminal_responses(self):
        """filter_terminal_responses convenience function works."""
        data = b'user\x1b[24;80Rinput'
        result = filter_terminal_responses(data)
        assert result == b'userinput'


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_input(self):
        """Empty input returns empty."""
        filter = ResponseFilter()
        assert filter.filter(b'') == b''

    def test_no_responses(self):
        """Input with no responses passes through."""
        filter = ResponseFilter()
        data = b'hello world\x1b[Aup arrow'
        result = filter.filter(data)
        assert result == data

    def test_partial_sequence_not_filtered(self):
        """Incomplete sequences are not filtered."""
        filter = ResponseFilter()
        # Just ESC[ without the rest
        data = b'\x1b['
        result = filter.filter(data)
        assert result == b'\x1b['


class TestMixedResponses:
    """Test filtering multiple response types in one stream."""

    def setup_method(self):
        self.filter = ResponseFilter()

    def test_multiple_response_types(self):
        """Multiple different response types filtered."""
        data = b'\x1b[24;80R\x1b[?64;1c\x1b]11;rgb:0000/0000/0000\x07'
        result = self.filter.filter(data)
        assert result == b''

    def test_responses_with_user_input(self):
        """Complex mix of responses and user input."""
        data = (
            b'vim file.txt\r'
            b'\x1b[?64;1c'  # DA response
            b'i'  # user insert mode
            b'\x1b[24;80R'  # CPR
            b'hello'  # user typing
            b'\x1b[0n'  # DSR
            b'\x1b:wq\r'  # user save and quit
        )
        result = self.filter.filter(data)
        assert result == b'vim file.txt\rihello\x1b:wq\r'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
