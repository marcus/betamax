"""
log.py - Standardized logging for Python scripts in betamax

Provides simple, hyper-concise logging functions for consistency with shell scripts.
"""

import sys
import os
from datetime import datetime


class LogLevel:
    """Log level constants."""
    DEBUG = 3
    INFO = 2
    WARNING = 1
    ERROR = 0


# Global log level (can be set via BETAMAX_LOG_LEVEL environment variable)
_log_level = LogLevel.INFO
if os.environ.get('BETAMAX_LOG_LEVEL') == 'debug':
    _log_level = LogLevel.DEBUG


def _should_log(level):
    """Check if message should be logged based on current level."""
    return level <= _log_level


def _get_timestamp():
    """Get current timestamp in ISO format."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _format_message(level_name, context, message):
    """Format a log message with timestamp and context."""
    timestamp = _get_timestamp()
    prefix = f"[{timestamp}] {level_name:<7} "
    if context:
        prefix += f"[{context}] "
    return prefix + message


def debug(message, context=None):
    """Log debug message (only when BETAMAX_LOG_LEVEL=debug)."""
    if _should_log(LogLevel.DEBUG):
        msg = _format_message("DEBUG", context, message)
        print(msg, file=sys.stderr)


def info(message, context=None):
    """Log info message."""
    if _should_log(LogLevel.INFO):
        msg = _format_message("INFO", context, message)
        print(msg, file=sys.stderr)


def warning(message, context=None):
    """Log warning message."""
    if _should_log(LogLevel.WARNING):
        msg = _format_message("WARNING", context, message)
        print(msg, file=sys.stderr)


def error(message, context=None):
    """Log error message."""
    if _should_log(LogLevel.ERROR):
        msg = _format_message("ERROR", context, message)
        print(msg, file=sys.stderr)


def enable_debug():
    """Enable debug logging."""
    global _log_level
    _log_level = LogLevel.DEBUG
    debug("Debug logging enabled")
