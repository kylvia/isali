#!/usr/bin/env python3
"""isali cover — generate a WeChat article cover.

Usage:
    isali cover --title TITLE [--subtitle SUB] [--bullets B1 B2 ...] [--style NAME] [--out PATH]
    isali cover --prompt "full prompt text" [--out PATH]
"""
import argparse
import json
import sys
import time
from pathlib import Path

# scripts/ is loaded via PYTHONPATH=packages so this works
sys.path.insert(0, str(Path(__file__).parent))
from generate import generate, load_preset, PRESETS_DIR  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(prog='isali cover')
    ap.add_argument('--title', default='')
    ap.add_argument('--subtitle', default='')
    ap.add_argument('--bullets', nargs='*', default=[], help='底部数据点（每项前会加 • ）')
    ap.add_argument('--style', default=None, help='preset name (minimal-tech / editorial / poster)')
    ap.add_argument('--prompt', default=None, help='跳过模板，直接用给定 prompt')
    ap.add_argument('--out', default=None, help='输出路径；未指定则用时间戳命名到 cwd')
    ap.add_argument('--list-presets', action='store_true')
    ap.add_argument('--plan', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--json', action='store_true', help='机器可读输出')
    args = ap.parse_args()

    if args.list_presets:
        for p in sorted(PRESETS_DIR.glob('*.txt')):
            print(p.stem)
        return 0

    if not args.title and not args.prompt:
        ap.error('must supply --title (or --prompt for direct mode)')

    out = args.out or f'./cover-{time.strftime("%Y%m%d-%H%M%S")}.png'

    try:
        result = generate(
            title=args.title,
            subtitle=args.subtitle,
            bullets=args.bullets,
            style=args.style,
            prompt=args.prompt,
            out_path=out,
            plan=args.plan,
            dry_run=args.dry_run,
        )
    except Exception as e:
        print(f'error: {e}', file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        action = result.get('action', '?')
        if action == 'plan':
            print(f'Plan:')
            print(f'  style: {result.get("style") or "(from profile)"}')
            print(f'  out:   {result.get("out")}')
            print(f'  prompt preview (first 200 chars):\n    {result["prompt"][:200]}...')
        elif action == 'dry-run':
            print(f'Dry-run:')
            print(f'  prompt length: {result["prompt_length"]} chars')
            print(f'  out:           {result["out"]}')
        else:
            print(f'✓ {result["duration_sec"]}s  {result["size_bytes"]} bytes  →  {result["path"]}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
