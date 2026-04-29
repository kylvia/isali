"""Structured audit log.

Every CLI/skill invocation can call audit() to write a JSON line to
~/.isali/logs/YYYY-MM-DD.jsonl — cheap, append-only, diffable.
"""
import json
import os
import time
from pathlib import Path

LOG_DIR = Path(os.environ.get('ISALI_LOG_DIR') or (Path.home() / '.isali' / 'logs'))


def audit(action: str, **fields):
    """Write one JSON line. Fields get merged with timestamp + action."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    day = time.strftime('%Y-%m-%d')
    path = LOG_DIR / f'{day}.jsonl'
    entry = {
        'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'action': action,
        **fields,
    }
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
