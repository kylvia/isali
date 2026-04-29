#!/usr/bin/env bash
# Skill verification — smoke test that push path works end-to-end.
# Uses --plan to avoid actual publish.
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"

echo "verifying isali-wechat-post..."

# 1. script exists and is a valid Python file
python3 -c "import ast; ast.parse(open('$DIR/scripts/main.py').read())" \
  && echo "  ✓ scripts/main.py parses"

# 2. can import profile/harness/logger
PYTHONPATH="$ROOT/packages" python3 -c "
from isali_core import profile, harness, logger
assert hasattr(profile, 'get')
assert hasattr(harness, 'summary')
assert hasattr(logger, 'audit')
print('  ✓ isali_core importable')
"

# 3. --plan works (no side effect)
SAMPLE="$(mktemp -t isali-sample-XXXXX).md"
cat > "$SAMPLE" <<'EOF'
---
title: test
---
# test
test body
EOF

PYTHONPATH="$ROOT/packages" python3 "$DIR/scripts/main.py" "$SAMPLE" --plan \
  | grep -q "Plan:" && echo "  ✓ --plan mode works"

rm -f "$SAMPLE"

echo "isali-wechat-post OK"
