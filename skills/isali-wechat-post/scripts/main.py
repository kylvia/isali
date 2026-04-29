#!/usr/bin/env python3
"""isali push — Push markdown to WeChat draft via vendored wechat-api.ts.

Usage:
    isali push <md_path> [--theme THEME] [--cover PATH] [--dry-run] [--plan]

Reads profile.wechat.default_theme as default.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from isali_core import harness, logger, profile

BAOYU_SCRIPT = Path(__file__).resolve().parent / 'wechat-api.ts'


def main() -> int:
    ap = argparse.ArgumentParser(prog='isali push', description='Push markdown to WeChat draft')
    ap.add_argument('md', help='path to markdown file')
    ap.add_argument('--theme', default=None, help='override profile theme')
    ap.add_argument('--cover', default=None, help='cover image path')
    ap.add_argument('--account', default=None, help='account alias (multi-account)')
    ap.add_argument('--title', default=None)
    ap.add_argument('--summary', default=None)
    ap.add_argument('--dry-run', action='store_true', help='render but do not publish')
    ap.add_argument('--plan', action='store_true', help='print plan and exit')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    md = Path(args.md).expanduser().resolve()
    if not md.exists():
        print(f'error: {md} not found', file=sys.stderr)
        return 1

    theme = args.theme or profile.get('wechat.default_theme', 'default')
    account = args.account or profile.get('wechat.account_alias')

    if args.plan:
        print('Plan:')
        print(f'  file:    {md}')
        print(f'  theme:   {theme}')
        print(f'  account: {account or "(default)"}')
        print(f'  cover:   {args.cover or "(from md frontmatter or first image)"}')
        print(f'  dry-run: {args.dry_run}')
        print(f'  script:  {BAOYU_SCRIPT}')
        return 0

    if not BAOYU_SCRIPT.exists():
        print(
            f'error: vendored wechat-api.ts not found at {BAOYU_SCRIPT}\n'
            f'fix: this file should ship with isali; reinstall via '
            f'`claude plugin install liao-techs/wechat-publisher`',
            file=sys.stderr,
        )
        return 2

    node_modules = BAOYU_SCRIPT.parent / 'node_modules'
    if not node_modules.is_dir():
        print(
            f'first-run: installing npm deps in {BAOYU_SCRIPT.parent} ...',
            file=sys.stderr,
        )
        rc = subprocess.call(['bun', 'install'], cwd=str(BAOYU_SCRIPT.parent))
        if rc != 0:
            print(f'error: bun install failed (rc={rc})', file=sys.stderr)
            return rc

    cmd = ['bun', str(BAOYU_SCRIPT), str(md), '--theme', theme]
    if args.cover:
        cmd += ['--cover', str(Path(args.cover).expanduser().resolve())]
    if account:
        cmd += ['--account', account]
    if args.title:
        cmd += ['--title', args.title]
    if args.summary:
        cmd += ['--summary', args.summary]
    if args.dry_run:
        cmd += ['--dry-run']

    if args.verbose:
        print(f'$ {" ".join(cmd)}', file=sys.stderr)

    t0 = time.time()
    rc = subprocess.call(cmd)
    dt = time.time() - t0

    logger.audit(
        'wechat_push',
        md=str(md),
        theme=theme,
        account=account,
        dry_run=args.dry_run,
        exit_code=rc,
        duration_sec=round(dt, 2),
        harness=harness.summary(),
    )

    return rc


if __name__ == '__main__':
    sys.exit(main())
