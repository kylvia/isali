#!/usr/bin/env bash
# isali-danger-page-to-markdown verify — offline structure + rendering checks.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "verifying isali-danger-page-to-markdown..."

# 1. 文件存在性
test -f "$DIR/SKILL.md" && echo "  ✓ SKILL.md present"
test -f "$DIR/scripts/main.py" && echo "  ✓ main.py present"
test -f "$DIR/scripts/html2md.py" && echo "  ✓ html2md.py present"
test -f "$DIR/scripts/adapters/generic.js" && echo "  ✓ generic adapter present"
test -f "$DIR/scripts/adapters/wechat.js" && echo "  ✓ wechat adapter present"
test -f "$DIR/scripts/adapters/x.js" && echo "  ✓ x adapter present"
test -d "$DIR/references" && echo "  ✓ references/ present"
test -d "$DIR/evals" && echo "  ✓ evals/ present"

# 2. Python 语法
python3 -c "import ast; ast.parse(open('$DIR/scripts/main.py').read())" && echo "  ✓ main.py parses"
python3 -c "import ast; ast.parse(open('$DIR/scripts/html2md.py').read())" && echo "  ✓ html2md.py parses"

# 3. adapters 用 node 语法检查（如果有 node）
if command -v node >/dev/null 2>&1; then
  node --check "$DIR/scripts/adapters/generic.js" && echo "  ✓ generic adapter syntactically valid"
  node --check "$DIR/scripts/adapters/wechat.js" && echo "  ✓ wechat adapter syntactically valid"
  node --check "$DIR/scripts/adapters/x.js" && echo "  ✓ x adapter syntactically valid"
else
  echo "  - skipping adapter syntax check (node not installed)"
fi

# 4. --plan 不调 relay，只解析 URL / adapter
OUT=$(python3 "$DIR/scripts/main.py" --plan https://x.com/foo/status/1234567890)
echo "$OUT" | grep -q '"adapter": "x"' && echo "  ✓ plan: detects x adapter"
echo "$OUT" | grep -q '"kind": "tweet"' && echo "  ✓ plan: detects tweet"

OUT=$(python3 "$DIR/scripts/main.py" --plan 'https://mp.weixin.qq.com/s/example')
echo "$OUT" | grep -q '"adapter": "wechat"' && echo "  ✓ plan: detects wechat adapter"
echo "$OUT" | grep -q '"kind": "wechat_article"' && echo "  ✓ plan: detects wechat article"

OUT=$(python3 "$DIR/scripts/main.py" --plan https://example.com/article)
echo "$OUT" | grep -q '"adapter": "generic"' && echo "  ✓ plan: detects generic adapter"

# 5. markdown 格式化（mock extract 结果，不调浏览器）
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
cat > "$TMPDIR/page.json" <<'JSON'
{
  "adapter": "generic",
  "kind": "article",
  "url": "https://example.com/article",
  "title": "Example Title",
  "author": {"name": "Ada"},
  "publishedAt": "2026-06-05",
  "bodyHtml": "<p>Hello <strong>world</strong>.</p><ul><li>One</li><li>Two</li></ul>",
  "media": [{"type": "photo", "url": "https://example.com/cover.jpg", "alt": ""}],
  "warnings": []
}
JSON
OUT_PATH="$TMPDIR/out.md"
python3 "$DIR/scripts/main.py" --from-json "$TMPDIR/page.json" -o "$OUT_PATH" >/dev/null
grep -q 'title: "Example Title"' "$OUT_PATH"
grep -q '# Example Title' "$OUT_PATH"
grep -q '\*\*world\*\*' "$OUT_PATH"
grep -q 'coverImage: "https://example.com/cover.jpg"' "$OUT_PATH"
echo "  ✓ page fixture renders markdown"

cat > "$TMPDIR/tweet.json" <<'JSON'
{
  "adapter": "x",
  "kind": "tweet",
  "tweetId": "111",
  "url": "https://x.com/foo/status/111",
  "author": {"name": "Foo Bar", "handle": "foo", "avatarUrl": null},
  "thread": [
    {"id":"111","url":"https://x.com/foo/status/111","text":"hello world","htmlText":"hello world","createdAt":"2026-04-30T08:00:00Z","isRoot":true,"media":[{"type":"photo","url":"https://example.com/a.jpg","alt":""}],"quotedTweet":null,"cardLink":null,"author":{"name":"Foo Bar","handle":"foo","avatarUrl":null}},
    {"id":"112","url":"https://x.com/foo/status/112","text":"second","htmlText":"second","createdAt":null,"isRoot":false,"media":[],"quotedTweet":null,"cardLink":null,"author":{"name":"Foo Bar","handle":"foo","avatarUrl":null}}
  ],
  "article": null,
  "warnings": []
}
JSON
python3 "$DIR/scripts/main.py" --from-json "$TMPDIR/tweet.json" -o "$OUT_PATH" >/dev/null
grep -q 'tweetCount: 2' "$OUT_PATH"
grep -q 'author: "Foo Bar (@foo)"' "$OUT_PATH"
grep -q '## 1' "$OUT_PATH"
grep -q '## 2' "$OUT_PATH"
grep -Fq '![](https://example.com/a.jpg)' "$OUT_PATH"
echo "  ✓ tweet fixture renders markdown"

python3 - <<PY
import sys, json
sys.path.insert(0, "$DIR/scripts")
import main as m

assert m.sanitize_slug("Hello World!") == "hello-world"
assert m.sanitize_slug("微信 封面图") == "微信-封面图"
assert m.sanitize_slug("") == "untitled"
print("  ✓ sanitize_slug edge cases pass")

assert m.choose_adapter("https://x.com/foo/status/1") == "x"
assert m.choose_adapter("https://mp.weixin.qq.com/s/example") == "wechat"
assert m.choose_adapter("https://example.com/a") == "generic"
print("  ✓ adapter selection helpers pass")
PY

echo "isali-danger-page-to-markdown OK"
