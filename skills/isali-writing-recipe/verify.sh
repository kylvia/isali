#!/usr/bin/env bash
# isali-writing-recipe verify — offline structure checks for a prompt-driven skill.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "verifying isali-writing-recipe..."

test -f "$DIR/SKILL.md" && echo "  ✓ SKILL.md present"
test -f "$DIR/references/intake-7q.md" && echo "  ✓ intake reference present"
test -f "$DIR/references/material-precheck.md" && echo "  ✓ material precheck reference present"
test -f "$DIR/references/recipes/README.md" && echo "  ✓ recipes index present"
test -f "$DIR/evals/case-01.yaml" && echo "  ✓ eval case present"

grep -q '^name: isali-writing-recipe$' "$DIR/SKILL.md"
grep -q '配方卡输出 schema' "$DIR/SKILL.md"
grep -q 'references/intake-7q.md' "$DIR/SKILL.md"
grep -q 'references/material-precheck.md' "$DIR/SKILL.md"
grep -q 'references/recipes/README.md' "$DIR/SKILL.md"
echo "  ✓ SKILL.md contract checks pass"

grep -q 'Q1. 文章类型' "$DIR/references/intake-7q.md"
grep -q 'Q7. 争议级别' "$DIR/references/intake-7q.md"
grep -q '任意一项不达标' "$DIR/references/material-precheck.md"
grep -q 'pain-point-tutorial' "$DIR/references/recipes/README.md"
grep -q 'news-takeaway-with-twist' "$DIR/references/recipes/README.md"
echo "  ✓ reference content checks pass"

python3 - "$DIR" <<'PY'
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
index = root / "references" / "recipes" / "README.md"
text = index.read_text(encoding="utf-8")
missing = []
for link in re.findall(r"\(([^)]+\.md)\)", text):
    target = (index.parent / link).resolve()
    if not target.exists():
        missing.append(link)
if missing:
    raise SystemExit(f"missing recipe links: {missing}")
PY
echo "  ✓ recipe links resolve"

grep -q 'pain-point-tutorial' "$DIR/evals/case-01.yaml"
grep -q 'news-takeaway-with-twist' "$DIR/evals/case-01.yaml"
grep -q 'must_refuse_draft' "$DIR/evals/case-01.yaml"
echo "  ✓ eval expectations present"

echo "isali-writing-recipe OK"
