#!/usr/bin/env bash
# isali-cover-gen verification — 无 API 调用，只验代码结构和 prompt 构建
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"

echo "verifying isali-cover-gen..."

# 1. Python 代码能 parse
python3 -c "import ast; ast.parse(open('$DIR/scripts/generate.py').read())" && echo "  ✓ generate.py parses"
python3 -c "import ast; ast.parse(open('$DIR/scripts/main.py').read())" && echo "  ✓ main.py parses"

# 2. 三个 preset 齐全
for p in minimal-tech editorial poster; do
  test -f "$DIR/presets/$p.txt" || { echo "  ✗ missing preset: $p"; exit 1; }
done
echo "  ✓ 3 presets present"

# 3. --list-presets 能工作
PYTHONPATH="$ROOT/packages" python3 "$DIR/scripts/main.py" --list-presets | grep -q minimal-tech \
  && echo "  ✓ --list-presets works"

# 4. --plan 能构建 prompt 但不调 API
OUT=$(PYTHONPATH="$ROOT/packages" python3 "$DIR/scripts/main.py" \
  --title "Test" --subtitle "副标题" --bullets "A" "B" --plan 2>&1)
echo "$OUT" | grep -q "prompt preview" && echo "  ✓ --plan builds prompt without API call"

# 5. --dry-run 能构建 prompt 并返回长度
OUT=$(PYTHONPATH="$ROOT/packages" python3 "$DIR/scripts/main.py" \
  --title "Test" --dry-run --json 2>&1)
echo "$OUT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); assert d['action']=='dry-run' and d['prompt_length']>0" \
  && echo "  ✓ --dry-run returns structured result"

echo "isali-cover-gen OK"
