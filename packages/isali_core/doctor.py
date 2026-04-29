"""isali doctor — environment self-check.

Usage:
    isali doctor
    isali doctor --json
"""
import json
import shutil
import sys
from pathlib import Path

from . import harness, profile

CHECKS = []


def _check(name):
    def wrap(fn):
        CHECKS.append((name, fn))
        return fn
    return wrap


@_check('python >= 3.9')
def _chk_py():
    return sys.version_info >= (3, 9), f'Python {sys.version.split()[0]}'


@_check('profile loadable')
def _chk_profile():
    try:
        p = profile.load()
        return bool(p), f'{profile.path_info()}, {len(p)} top-level keys'
    except Exception as e:
        return False, f'error: {e}'


@_check('bun (wechat-post dependency)')
def _chk_bun():
    bun = shutil.which('bun')
    return bun is not None, bun or 'not found — install via: curl -fsSL https://bun.sh/install | bash'


@_check('vendored wechat-api.ts')
def _chk_baoyu():
    # Resolve to <isali_root>/skills/isali-wechat-post/scripts/wechat-api.ts
    here = Path(__file__).resolve()
    p = here.parents[2] / 'skills' / 'isali-wechat-post' / 'scripts' / 'wechat-api.ts'
    return p.exists(), str(p) if p.exists() else f'missing: {p} (reinstall isali)'


@_check('wechat credentials')
def _chk_wx():
    new = Path.home() / '.isali/wechat.env'
    legacy = Path.home() / '.baoyu-skills/.env'
    if new.exists():
        return True, str(new)
    if legacy.exists():
        return True, f'{legacy} (legacy path; consider moving to ~/.isali/wechat.env)'
    return False, 'not found — create ~/.isali/wechat.env with WECHAT_APP_ID + WECHAT_APP_SECRET'


@_check('isali writable log dir')
def _chk_logs():
    d = Path.home() / '.isali/logs'
    try:
        d.mkdir(parents=True, exist_ok=True)
        return True, str(d)
    except Exception as e:
        return False, f'error: {e}'


def main(argv: list) -> int:
    if '--help' in argv or '-h' in argv:
        print(__doc__.strip())
        return 0
    as_json = '--json' in argv
    results = []
    for name, fn in CHECKS:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, f'error: {e}'
        results.append({'name': name, 'ok': ok, 'detail': detail})

    if as_json:
        print(json.dumps({'checks': results, 'harness': harness.summary()},
                         ensure_ascii=False, indent=2))
    else:
        for r in results:
            mark = '✓' if r['ok'] else '✗'
            print(f'  {mark} {r["name"]}: {r["detail"]}')
        ok_count = sum(1 for r in results if r['ok'])
        print(f'\n{ok_count}/{len(results)} checks passed\n')
        print('harness:')
        for k, v in harness.summary().items():
            print(f'  {k}: {v}')

    return 0 if all(r['ok'] for r in results) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
