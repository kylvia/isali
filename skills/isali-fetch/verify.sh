#!/usr/bin/env bash
# isali-fetch verify — 不调外网，只验代码结构 + 离线 HTML 解析
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"

echo "verifying isali-fetch..."

python3 -c "import ast; ast.parse(open('$DIR/scripts/main.py').read())" && echo "  ✓ main.py parses"
python3 -c "import ast; ast.parse(open('$DIR/scripts/fetchers.py').read())" && echo "  ✓ fetchers.py parses"

# --plan 识别 source 不抓取
OUT=$(PYTHONPATH="$ROOT/packages" python3 "$DIR/scripts/main.py" \
  https://mp.weixin.qq.com/s/xxxx --plan 2>&1)
echo "$OUT" | grep -q "source: wechat" && echo "  ✓ detects wechat source"

OUT=$(PYTHONPATH="$ROOT/packages" python3 "$DIR/scripts/main.py" \
  https://x.com/foo/status/1 --plan 2>&1)
echo "$OUT" | grep -q "source: x" && echo "  ✓ detects x source"

OUT=$(PYTHONPATH="$ROOT/packages" python3 "$DIR/scripts/main.py" \
  https://example.com --plan 2>&1)
echo "$OUT" | grep -q "source: web" && echo "  ✓ detects web source"

# 离线 HTML → MD 转换测试
PYTHONPATH="$ROOT/packages:$DIR/scripts" python3 -c "
from fetchers import html_to_md, parse_wechat
# 模拟简单公众号 html
sample = '''
<html><body>
var msg_title = \"测试标题\";
var nickname = \"测试号\";
var ct = \"1745500800\";
<div class=\"rich_media_content\" id=\"js_content\">
<p>正文第一段</p>
<h2>小标题</h2>
<p><strong>重点</strong>内容</p>
<img src=\"https://example.com/a.jpg\" />
</div><script>end</script>
</body></html>
'''
meta = parse_wechat(sample)
assert meta['title'] == '测试标题', f'title wrong: {meta[\"title\"]}'
assert meta['author'] == '测试号', f'author wrong: {meta[\"author\"]}'
assert meta['body_html']
md = html_to_md(meta['body_html'])
assert '正文第一段' in md
assert '## 小标题' in md
assert '**重点**' in md
assert '![](https://example.com/a.jpg)' in md
print('  ✓ offline parse + html_to_md works')
"

echo "isali-fetch OK"
