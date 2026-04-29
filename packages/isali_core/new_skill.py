"""isali new-skill — scaffold a new skill with correct structure.

Enforces the convention: SKILL.md ≤ 10 lines main flow,
required verify.sh, evals/ dir, references/ dir.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = ROOT / 'skills'

SKILL_MD_TEMPLATE = '''---
name: {name}
description: {desc}. Triggers: "{trigger1}", "{trigger2}".
harness:
  requires: []
  graceful_degradation: true
---

# {name}

## 用途
TODO: 一句话说清这个 skill 干什么。

## 调用方式
TODO: 用户说什么时触发，传什么参数。

## 执行流程
1. 读 profile: `from isali_core import profile; tone = profile.get('content.tone')`
2. 调用 `scripts/<main>.py` 做实际工作
3. 把输出交回给用户

## 细节参考
- API/凭证配置 → `references/setup.md`
- 具体参数 → `references/options.md`

## 检查清单
- [ ] 所有数字/断言可追溯到一手源
- [ ] 输出符合 profile 风格
- [ ] 非交互模式有合理默认
'''

VERIFY_SH_TEMPLATE = '''#!/usr/bin/env bash
# Skill verification.
# Exit 0 if skill is healthy; non-zero if something's wrong.
set -e

echo "verifying {name}..."

# TODO: replace with real checks
# e.g. test that the script runs with dry-run flag
# python3 scripts/main.py --dry-run || exit 1

echo "  ✓ dry-run smoke test"
echo "{name} OK"
'''

EVAL_CASE_TEMPLATE = '''# Eval case — inputs and expected behavior
name: basic
description: TODO
input:
  # prompt / file / args that skill receives
expected:
  # what output or side-effect is correct
  # - contains: "some text"
  # - file_exists: path/to/output
'''


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ('-h', '--help'):
        print('Usage: isali new-skill <name> [description]')
        return 1

    name = argv[0]
    if not name.startswith('isali-') and not name.replace('-', '').isalpha():
        print(f'invalid skill name: {name} (use lowercase-with-dashes)', file=sys.stderr)
        return 1

    desc = argv[1] if len(argv) > 1 else f'TODO: describe {name}'
    trigger1 = argv[2] if len(argv) > 2 else name
    trigger2 = argv[3] if len(argv) > 3 else name.replace('-', ' ')

    target = SKILLS_DIR / name
    if target.exists():
        print(f'skill already exists: {target}', file=sys.stderr)
        return 1

    (target / 'references').mkdir(parents=True)
    (target / 'scripts').mkdir()
    (target / 'evals').mkdir()

    (target / 'SKILL.md').write_text(SKILL_MD_TEMPLATE.format(
        name=name, desc=desc, trigger1=trigger1, trigger2=trigger2))

    verify = target / 'verify.sh'
    verify.write_text(VERIFY_SH_TEMPLATE.format(name=name))
    verify.chmod(0o755)

    (target / 'evals' / 'case-01.yaml').write_text(EVAL_CASE_TEMPLATE)

    print(f'✓ scaffolded {name}')
    print(f'  edit: {target}/SKILL.md')
    print(f'  edit: {target}/verify.sh')
    print(f'  add:  {target}/scripts/<main>.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
