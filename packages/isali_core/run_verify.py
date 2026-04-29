"""isali run-verify — run all skill verify.sh scripts and aggregate.

Usage:
    isali run-verify                # all skills
    isali run-verify <name>         # one skill
    isali run-verify --json         # machine-readable
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = ROOT / 'skills'


def _skills() -> list:
    return sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / 'verify.sh').exists())


def _run_one(skill_path: Path) -> dict:
    verify = skill_path / 'verify.sh'
    t0 = time.time()
    proc = subprocess.run([str(verify)], capture_output=True, text=True)
    dt = time.time() - t0
    return {
        'skill': skill_path.name,
        'exit_code': proc.returncode,
        'duration_sec': round(dt, 2),
        'stdout': proc.stdout,
        'stderr': proc.stderr,
        'ok': proc.returncode == 0,
    }


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(prog='isali run-verify', add_help=False)
    ap.add_argument('-h', '--help', action='store_true')
    ap.add_argument('name', nargs='?', help='specific skill name (default: all)')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)

    if args.help:
        print(__doc__.strip())
        return 0

    if args.name:
        target = SKILLS_DIR / args.name
        if not target.exists():
            print(f'error: skill "{args.name}" not found', file=sys.stderr)
            return 1
        targets = [target]
    else:
        targets = _skills()

    if not targets:
        print('(no skills with verify.sh)', file=sys.stderr)
        return 0

    results = []
    for t in targets:
        if not args.json:
            print(f'▶ {t.name}', flush=True)
        results.append(_run_one(t))

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print()
        print('=' * 50)
        for r in results:
            mark = '✓' if r['ok'] else '✗'
            print(f'  {mark} {r["skill"]:<22}  {r["duration_sec"]:>5}s  exit={r["exit_code"]}')
            if not r['ok'] and r['stderr']:
                for line in r['stderr'].splitlines()[:3]:
                    print(f'      {line}')
        ok = sum(1 for r in results if r['ok'])
        print('=' * 50)
        print(f'{ok}/{len(results)} passed')

    return 0 if all(r['ok'] for r in results) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
