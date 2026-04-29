#!/usr/bin/env python3
"""Stop hook: remind to sediment session thinking into vault/claude/.

Fires on Claude Code Stop event. Reads stdin JSON from the harness.

Logic:
  - If the conversation was substantive (vault files modified, isali calls made,
    or files created outside vault/claude/), but claude/ has no note dated today
    → emit a systemMessage reminding to write a thinking-assets note.
  - If claude/ already has today's note, silent OK.
  - If conversation was trivial (no modifications), silent OK.

Thresholds (tunable via env):
  ISALI_SEDIMENT_MIN_ACTIVITY (default 5)  — combined signal threshold
"""
import json
import os
import sys
import time
from pathlib import Path

VAULT = Path(os.environ.get('ISALI_VAULT') or (Path.home() / 'Documents' / 'Obsidian Vault'))
CLAUDE_DIR = VAULT / 'claude'
ISALI_LOG_DIR = Path(os.environ.get('ISALI_LOG_DIR') or (Path.home() / '.isali' / 'logs'))
MIN_ACTIVITY = int(os.environ.get('ISALI_SEDIMENT_MIN_ACTIVITY', '5'))


def _today() -> str:
    return time.strftime('%Y-%m-%d')


def _files_modified_today(root: Path, exclude_claude: bool = True) -> int:
    """Count .md files modified within last 24h."""
    if not root.exists():
        return 0
    cutoff = time.time() - 86400
    count = 0
    for p in root.rglob('*.md'):
        if exclude_claude and '/claude/' in str(p):
            continue
        if '/.obsidian/' in str(p):
            continue
        try:
            if p.stat().st_mtime > cutoff:
                count += 1
        except OSError:
            pass
    return count


def _sediment_notes_today() -> int:
    if not CLAUDE_DIR.exists():
        return 0
    prefix = _today()
    return len(list(CLAUDE_DIR.glob(f'{prefix}-*.md')))


def _isali_calls_today() -> int:
    log = ISALI_LOG_DIR / f'{_today()}.jsonl'
    if not log.exists():
        return 0
    try:
        return sum(1 for line in log.read_text().splitlines() if line.strip())
    except OSError:
        return 0


def main() -> int:
    # Harness sends JSON on stdin; we don't need it for decisions, but read it to be polite
    try:
        sys.stdin.read()
    except Exception:
        pass

    modified = _files_modified_today(VAULT)
    isali_calls = _isali_calls_today()
    sediment = _sediment_notes_today()
    activity = modified + isali_calls

    # Always silent if already sedimented today
    if sediment > 0:
        return 0
    # Silent if trivial session
    if activity < MIN_ACTIVITY:
        return 0

    msg = (
        f'📝 本次会话有活动（{modified} 个 vault 文件修改 + {isali_calls} 次 isali 调用）'
        f'但 claude/ 今天没有沉淀笔记。'
        f'\n建议让 Claude 整理思考资产到 '
        f'~/Documents/Obsidian\\ Vault/claude/{_today()}-<topic>.md'
        f'（只记分析/决策/设计，不记流水账）。'
    )
    print(json.dumps({'systemMessage': msg}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
