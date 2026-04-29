#!/usr/bin/env python3
"""isali fetch — fetch URL content → markdown.

Usage:
    isali fetch <url> [--out FILE] [--json] [--plan]
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fetchers import fetch_and_convert, detect_source  # noqa: E402

from isali_core import logger  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(prog='isali fetch')
    ap.add_argument('url', help='URL to fetch')
    ap.add_argument('--out', help='save markdown to this file (default: stdout)')
    ap.add_argument('--json', action='store_true', help='output JSON with metadata')
    ap.add_argument('--plan', action='store_true', help='only detect source, do not fetch')
    ap.add_argument('--cookie', action='append', default=[],
                    help='optional k=v cookie (repeatable)')
    args = ap.parse_args()

    if args.plan:
        print('Plan:')
        print(f'  url:    {args.url}')
        print(f'  source: {detect_source(args.url)}')
        print(f'  out:    {args.out or "stdout"}')
        print(f'  format: {"json" if args.json else "markdown"}')
        return 0

    cookies = {}
    for c in args.cookie:
        if '=' in c:
            k, v = c.split('=', 1)
            cookies[k] = v

    t0 = time.time()
    result = fetch_and_convert(args.url, cookies=cookies or None)
    dt = time.time() - t0

    logger.audit(
        'fetch',
        url=args.url,
        source=result.get('source'),
        duration_sec=round(dt, 2),
        ok='error' not in result,
        error=result.get('error'),
    )

    if 'error' in result:
        print(f'error: {result["error"]}', file=sys.stderr)
        return 2

    if args.json:
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = result['markdown']

    if args.out:
        Path(args.out).write_text(output)
        print(f'✓ saved {len(output)} chars → {args.out} ({dt:.1f}s)', file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == '__main__':
    sys.exit(main())
