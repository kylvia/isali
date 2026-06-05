---
name: isali-danger-page-to-markdown
description: Convert browser-rendered pages to markdown by driving the user's local Chrome via browser-relay. Supports generic articles, WeChat public articles, and X/Twitter tweets/articles through DOM adapters. Triggers 关键词 "网页转 markdown", "page to markdown", "公众号转 markdown", "微信文章转 markdown", "推文转 markdown", "X to markdown", "保存网页", "browser-relay 抓网页", "isali-danger-page".
harness:
  requires: [Bash]
  graceful_degradation: true
---

# isali-danger-page-to-markdown

通过 browser-relay 控制用户本地 Chrome（已登录态）读取渲染后的 DOM，把网页正文转成 Markdown。

叫 `danger` 是因为它不是站点官方 API：DOM 结构可能变化，自动化访问可能触发风控，抽取结果也可能不完整。默认不逆向私有接口，不抽 cookie，不绕过登录态限制。

## 支持范围

| adapter | 适用 URL | 抽取内容 |
|---|---|---|
| `generic` | 普通网页 / 博客 / 新闻站 | 标题、作者、发布时间、正文 HTML、首图 |
| `wechat` | `mp.weixin.qq.com` 公众号文章 | 标题、公众号名、发布时间、正文、封面/首图 |
| `x` | `x.com` / `twitter.com` | tweet/thread、X Article、图片 poster |

## 主流程（5 步）

1. **健康检查**：`GET 127.0.0.1:18795/api/debug` 确认 browser-relay + Chrome extension 在线。
2. **选择 adapter**：根据 URL host 自动选择 `generic` / `wechat` / `x`，也可用 `--adapter` 强制指定。
3. **导航页面**：`POST /api/navigate` 把目标 tab 跳到 URL，等待页面渲染。
4. **DOM 抽取**：`POST /api/eval` 注入 `scripts/adapters/<adapter>.js`，返回统一 JSON。
5. **Markdown 输出**：`scripts/html2md.py` 将正文 HTML 转 markdown，加 YAML frontmatter 后写文件。

## 调用方式

```bash
# 预览将使用哪个 adapter，不打开浏览器
python3 scripts/main.py --plan 'https://mp.weixin.qq.com/s/example'

# 主入口：通过 browser-relay 抓取并写入默认目录 ./page-to-markdown/<adapter>/<slug>.md
python3 scripts/main.py 'https://example.com/article'

# 指定输出文件
python3 scripts/main.py 'https://example.com/article' -o out.md

# 只输出抽取 JSON
python3 scripts/main.py 'https://example.com/article' --json

# 从已抽取 JSON 离线渲染 markdown
python3 scripts/main.py --from-json fixture.json -o out.md

# 检查 browser-relay
python3 scripts/main.py --health
```

## 详细参考

- 风险声明 → `references/disclaimer.md`
- DOM adapter 策略 → `references/dom-extraction.md`
- 输出格式 → `references/output-format.md`
- browser-relay 调用细节 → `references/browser-relay-flow.md`

## 与 X 专用工具的关系

早期版本只做 `isali-danger-x-to-markdown`，后来扩展为统一的 page adapter 架构。

| 维度 | 旧 X 专用 | 当前 page-to-markdown |
|---|---|---|
| 数据源 | X DOM | 多站点 DOM adapter |
| 入口 | `scripts/main.py` + `x_extract.js` | `scripts/main.py` + `scripts/adapters/*.js` |
| 默认目录 | `x-to-markdown/...` | `page-to-markdown/<adapter>/...` |
| 适用 | X tweet/thread | 普通网页、公众号、X |

## 自查

- [ ] `verify.sh` 离线通过，不依赖真实浏览器。
- [ ] relay 不通时返回非零，且不自动 fallback 到逆向 API。
- [ ] adapter 返回统一 JSON：`adapter/kind/url/title/bodyHtml/media/warnings` 或 X thread/article 结构。
- [ ] 文档没有承诺尚未实现的媒体下载、滚屏补全或 cookie 抽取。
- [ ] 失败 exit code 非 0，并在 stderr 给出可读错误。
