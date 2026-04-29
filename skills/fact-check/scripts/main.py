#!/usr/bin/env python3
"""fact-check linter — static scan for suspicious claims.

Does NOT use an LLM. Does NOT verify correctness.
It flags patterns that HUMANS (or Claude) should review:

  - Numeric claims (%, 排名, elo, 耗时, ...)
  - Weak-source markers ("Reddit 上"、"有人说"、"据说")
  - Unsourced direct quotes ("「...」" or '"..."' without a [link])
  - Superlative claims ("最快", "首个", "唯一")

Exit codes:
  0 — no issues flagged
  1 — issues found (hook will block or warn)
  2 — error (file not found / parse)

Usage:
  isali fact-check <md>             # human-readable
  isali fact-check <md> --json      # machine-readable
  isali fact-check <md> --strict    # any finding = exit 1
  isali fact-check <md> --warn-only # always exit 0
"""
import argparse
import json
import re
import sys
from pathlib import Path

NUMERIC_PATTERNS = [
    (r'\+?\d+(?:\.\d+)?\s*%', 'percentage'),
    (r'\+?\d{3,}(?:\.\d+)?\s*(?:分|elo|points?)', 'score'),
    (r'第\s*\d+\s*名|#\s*\d+|排名\s*第?\s*\d+', 'rank'),
    (r'\d+(?:\.\d+)?\s*(?:秒|分钟|小时|毫秒|ms|s|sec|min|hour)', 'duration'),
    (r'\d+(?:,\d{3})*\s*(?:人|万|亿|次)', 'headcount'),
]

WEAK_SOURCE_MARKERS = [
    'reddit 上', 'reddit上', '据说', '有人说', '听说', '传言',
    '好像', '似乎', '大概', '网上有人', '据传',
    'rumored', 'allegedly', 'reportedly', 'supposedly',
]

SUPERLATIVES = [
    '最快', '最强', '最好', '唯一', '首个', '第一次', '前所未有',
    '碾压', '吊打', '史上', '永远', '绝对',
    'fastest', 'first ever', 'strongest', 'unbeatable',
]


def lint(md_text: str) -> dict:
    lines = md_text.split('\n')
    findings = {'numeric': [], 'weak_sources': [], 'superlatives': [], 'unsourced_quotes': []}

    for i, line in enumerate(lines, 1):
        # skip YAML frontmatter & code blocks heuristically
        if line.startswith('---') or line.startswith('```'):
            continue

        # numeric claims
        for pat, kind in NUMERIC_PATTERNS:
            for m in re.finditer(pat, line):
                findings['numeric'].append({
                    'line': i, 'kind': kind, 'match': m.group(0), 'context': line.strip()[:120]
                })

        # weak source markers
        lower = line.lower()
        for marker in WEAK_SOURCE_MARKERS:
            if marker in lower:
                findings['weak_sources'].append({
                    'line': i, 'marker': marker, 'context': line.strip()[:120]
                })
                break

        # superlatives
        for sup in SUPERLATIVES:
            if sup in line:
                findings['superlatives'].append({
                    'line': i, 'term': sup, 'context': line.strip()[:120]
                })
                break

        # direct quotes without visible source link nearby
        for qm in re.finditer(r'「([^」]{4,})」|"([^"]{4,})"|"([^"]{4,})"', line):
            quote = next(g for g in qm.groups() if g)
            # heuristic: if same line or next line has a [link](url), skip
            window = '\n'.join(lines[max(0, i-1):min(len(lines), i+2)])
            if not re.search(r'\[[^\]]+\]\([^)]+\)|https?://', window):
                findings['unsourced_quotes'].append({
                    'line': i, 'quote': quote[:60], 'context': line.strip()[:120]
                })

    total = sum(len(v) for v in findings.values())
    return {'total_findings': total, 'findings': findings}


def main() -> int:
    ap = argparse.ArgumentParser(prog='isali fact-check')
    ap.add_argument('md', help='markdown file to lint')
    ap.add_argument('--json', action='store_true', help='JSON output')
    ap.add_argument('--strict', action='store_true', help='any finding = exit 1')
    ap.add_argument('--warn-only', action='store_true', help='always exit 0')
    ap.add_argument('--plan', action='store_true')
    args = ap.parse_args()

    path = Path(args.md).expanduser()
    if args.plan:
        print(f'Plan: lint {path}')
        return 0
    if not path.exists():
        print(f'error: {path} not found', file=sys.stderr)
        return 2

    result = lint(path.read_text())
    total = result['total_findings']

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        f = result['findings']
        print(f'fact-check lint: {path}')
        print(f'  numeric claims:    {len(f["numeric"]):>3} (need source verification)')
        print(f'  weak sources:      {len(f["weak_sources"]):>3} (e.g. "Reddit 上", "据说")')
        print(f'  superlatives:      {len(f["superlatives"]):>3} (e.g. "首个", "最快")')
        print(f'  unsourced quotes:  {len(f["unsourced_quotes"]):>3} (no visible [link] nearby)')
        print(f'  TOTAL:             {total:>3}')

        if total > 0:
            print('\nSample (up to 3 per category):')
            for cat, items in f.items():
                for it in items[:3]:
                    line = it.get('line')
                    ctx = it.get('context', '')
                    print(f'  [{cat:>16}] L{line}: {ctx}')

    if args.warn_only:
        return 0
    if args.strict:
        return 1 if total > 0 else 0
    # default: fail only if numeric + weak_sources both non-empty (real risk)
    if result['findings']['numeric'] and result['findings']['weak_sources']:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
