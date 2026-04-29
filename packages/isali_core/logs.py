"""isali logs — inspect audit log.

Usage:
    isali logs                          # today, all actions
    isali logs --days 7                 # last N days
    isali logs --action wechat_push     # filter by action
    isali logs --failed                 # only non-zero exits
    isali logs --last 10                # last N entries
    isali logs --json                   # raw jsonl
    isali logs --stats                  # group counts + totals
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

LOG_DIR = Path(os.environ.get('ISALI_LOG_DIR') or (Path.home() / '.isali' / 'logs'))


def _iter_entries(days: int, last: int = 0):
    if not LOG_DIR.exists():
        return
    today = datetime.today()
    entries = []
    for d in range(days):
        day = (today - timedelta(days=d)).strftime('%Y-%m-%d')
        path = LOG_DIR / f'{day}.jsonl'
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    entries.sort(key=lambda e: e.get('ts', ''))
    if last > 0:
        entries = entries[-last:]
    for e in entries:
        yield e


def _fmt_short(e: dict) -> str:
    ts = e.get('ts', '?')[:19]
    action = e.get('action', '?')
    exit_code = e.get('exit_code', e.get('ok'))
    mark = '✓' if (exit_code == 0 or exit_code is True) else '✗'
    dt = e.get('duration_sec', '')
    dt_str = f' {dt}s' if dt else ''
    extras = []
    for k in ('md', 'url', 'title', 'theme'):
        if k in e:
            v = str(e[k])
            if len(v) > 60:
                v = '...' + v[-57:]
            extras.append(f'{k}={v}')
    return f'{ts} {mark} {action}{dt_str}  ' + '  '.join(extras)


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(prog='isali logs', add_help=False)
    ap.add_argument('-h', '--help', action='store_true')
    ap.add_argument('--days', type=int, default=1)
    ap.add_argument('--action', default=None, help='filter by action name')
    ap.add_argument('--failed', action='store_true', help='only non-zero exits')
    ap.add_argument('--last', type=int, default=0, help='limit to last N entries')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--stats', action='store_true')
    args = ap.parse_args(argv)

    if args.help:
        print(__doc__.strip())
        return 0

    entries = list(_iter_entries(args.days))

    if args.action:
        entries = [e for e in entries if e.get('action') == args.action]
    if args.failed:
        entries = [e for e in entries
                   if (e.get('exit_code') not in (0, None) or e.get('ok') is False)]
    if args.last > 0:
        entries = entries[-args.last:]

    if args.stats:
        from collections import Counter
        actions = Counter(e.get('action', '?') for e in entries)
        ok = sum(1 for e in entries if e.get('exit_code') == 0 or e.get('ok') is True)
        total_dt = sum(e.get('duration_sec', 0) or 0 for e in entries)
        print(f'Range:   last {args.days} day(s)')
        print(f'Entries: {len(entries)} total, {ok} ok, {len(entries) - ok} failed')
        print(f'Duration: {total_dt:.1f}s cumulative')
        print(f'\nBy action:')
        for action, n in actions.most_common():
            print(f'  {n:4d}  {action}')
        return 0

    if args.json:
        for e in entries:
            print(json.dumps(e, ensure_ascii=False))
        return 0

    if not entries:
        print(f'(no log entries in last {args.days} day(s))', file=sys.stderr)
        return 0

    for e in entries:
        print(_fmt_short(e))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
