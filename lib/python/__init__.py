"""
betamax.lib.python - Python modules for interactive terminal recording

This package provides:
- recorder: PTY-based terminal session recording
- key_mapper: Escape sequence to betamax key name conversion
- keys_generator: Generate .keys files from recorded sessions
"""

from .recorder import TerminalRecorder
from .key_mapper import KeyMapper
from .keys_generator import KeysGenerator

__all__ = ['TerminalRecorder', 'KeyMapper', 'KeysGenerator']
