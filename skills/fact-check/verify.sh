#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"

echo "verifying fact-check..."

test -f "$DIR/SKILL.md" && echo "  ✓ SKILL.md exists"
head -1 "$DIR/SKILL.md" | grep -q "^---$" && echo "  ✓ frontmatter present"
grep -q "Triggers" "$DIR/SKILL.md" && echo "  ✓ triggers declared"
grep -q "## 流程\|## Flow\|## 主流程" "$DIR/SKILL.md" && echo "  ✓ flow section present"

# 静态 linter 代码可解析
python3 -c "import ast; ast.parse(open('$DIR/scripts/main.py').read())" && echo "  ✓ linter parses"

# 造一个带可疑声明的 md，linter 必须能识别
SAMPLE=$(mktemp -t fact-check-test-XXXXX).md
cat > "$SAMPLE" <<'EOF'
# 测试文章

GPT-Image-2 据说比前代快 50%，碾压所有对手。

Reddit 上有人说这是首个会思考的模型。

Arena 榜单 +241 分。
EOF

PYTHONPATH="$ROOT/packages" python3 "$DIR/scripts/main.py" "$SAMPLE" --json --warn-only > /tmp/_fc.json
python3 -c "
import json
d = json.load(open('/tmp/_fc.json'))
f = d['findings']
assert len(f['numeric']) >= 2, f'expected numeric claims, got {f[\"numeric\"]}'
assert len(f['weak_sources']) >= 2, f'expected weak sources, got {f[\"weak_sources\"]}'
assert len(f['superlatives']) >= 1, f'expected superlatives, got {f[\"superlatives\"]}'
print('  ✓ linter identifies numeric/weak-source/superlatives claims')
"
rm -f "$SAMPLE" /tmp/_fc.json

echo "fact-check OK"
