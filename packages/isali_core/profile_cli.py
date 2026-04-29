"""isali profile — manage profiles in ~/.isali/profiles/.

Usage:
    isali profile                       # same as `current`
    isali profile list                  # list available profiles
    isali profile current               # show currently active profile
    isali profile switch <name>         # copy profiles/<name>.yaml → profile.yaml
    isali profile show [<name>]        # print profile contents
    isali profile edit                  # open profile.yaml in $EDITOR
    isali profile diff <a> <b>          # diff two profiles
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import profile as profile_mod

ISALI_DIR = Path.home() / '.isali'
PROFILES_DIR = ISALI_DIR / 'profiles'
ACTIVE = ISALI_DIR / 'profile.yaml'


def _list() -> list:
    if not PROFILES_DIR.exists():
        return []
    return sorted(p.stem for p in PROFILES_DIR.glob('*.yaml'))


def _active_name() -> str:
    """Guess name of active profile by content match."""
    if not ACTIVE.exists():
        return '(none)'
    active_bytes = ACTIVE.read_bytes()
    for p in PROFILES_DIR.glob('*.yaml'):
        if p.read_bytes() == active_bytes:
            return p.stem
    return '(custom)'


def cmd_list(_args) -> int:
    names = _list()
    active = _active_name()
    if not names:
        print(f'(no profiles in {PROFILES_DIR})')
        return 1
    for name in names:
        mark = '*' if name == active else ' '
        print(f' {mark} {name}')
    return 0


def cmd_current(_args) -> int:
    print(f'active file: {ACTIVE if ACTIVE.exists() else "(none)"}')
    print(f'matches:     {_active_name()}')
    if os.environ.get('ISALI_PROFILE'):
        print(f'override:    ISALI_PROFILE={os.environ["ISALI_PROFILE"]}')
    return 0


def cmd_switch(args) -> int:
    src = PROFILES_DIR / f'{args.name}.yaml'
    if not src.exists():
        print(f'error: no such profile: {args.name}', file=sys.stderr)
        print(f'available: {", ".join(_list()) or "(none)"}', file=sys.stderr)
        return 1
    ISALI_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, ACTIVE)
    print(f'✓ switched to "{args.name}" ({ACTIVE})')
    return 0


def cmd_show(args) -> int:
    if args.name:
        src = PROFILES_DIR / f'{args.name}.yaml'
        if not src.exists():
            print(f'error: no such profile: {args.name}', file=sys.stderr)
            return 1
    else:
        src = ACTIVE if ACTIVE.exists() else profile_mod._DEFAULT
    print(f'# file: {src}')
    print(src.read_text())
    return 0


def cmd_edit(_args) -> int:
    editor = os.environ.get('EDITOR', 'nano')
    if not ACTIVE.exists():
        default = profile_mod._DEFAULT
        ISALI_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(default, ACTIVE)
    subprocess.call([editor, str(ACTIVE)])
    return 0


def cmd_diff(args) -> int:
    a = PROFILES_DIR / f'{args.a}.yaml'
    b = PROFILES_DIR / f'{args.b}.yaml'
    for p in (a, b):
        if not p.exists():
            print(f'error: {p.name} not found', file=sys.stderr)
            return 1
    subprocess.call(['diff', '-u', str(a), str(b)])
    return 0


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(prog='isali profile', add_help=False)
    ap.add_argument('-h', '--help', action='store_true')
    sub = ap.add_subparsers(dest='cmd')

    sub.add_parser('list', add_help=False)
    sub.add_parser('current', add_help=False)
    sw = sub.add_parser('switch', add_help=False)
    sw.add_argument('name')
    sh = sub.add_parser('show', add_help=False)
    sh.add_argument('name', nargs='?')
    sub.add_parser('edit', add_help=False)
    df = sub.add_parser('diff', add_help=False)
    df.add_argument('a')
    df.add_argument('b')

    args = ap.parse_args(argv)

    if args.help:
        print(__doc__.strip())
        return 0

    dispatch = {
        None: cmd_current,
        'current': cmd_current,
        'list': cmd_list,
        'switch': cmd_switch,
        'show': cmd_show,
        'edit': cmd_edit,
        'diff': cmd_diff,
    }
    return dispatch[args.cmd](args)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
