"""Harness capability detection.

Lets skills and CLIs know what runtime they're in, so they can:
- Ask user if interactive, use defaults if not
- Degrade gracefully if a tool is missing
- Choose non-interactive behavior in CI/cron
"""
import os
import sys


def has_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def is_in_claude_code() -> bool:
    """Running inside a Claude Code session?"""
    return (
        os.environ.get('CLAUDECODE') == '1'
        or 'CLAUDE_CODE_ENTRYPOINT' in os.environ
        or 'CLAUDE_SESSION_ID' in os.environ
    )


def is_non_interactive() -> bool:
    """CI / cron / webhook / scripted execution."""
    return (
        not has_tty()
        or os.environ.get('ISALI_NON_INTERACTIVE') == '1'
        or os.environ.get('CI') == 'true'
    )


def summary() -> dict:
    return {
        'tty': has_tty(),
        'claude_code': is_in_claude_code(),
        'non_interactive': is_non_interactive(),
        'platform': sys.platform,
        'python': sys.version.split()[0],
    }
