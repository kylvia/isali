# 输出格式

## 默认路径

```text
page-to-markdown/<adapter>/<slug>.md
```

`slug` 来自标题或 URL，保留中文、英文、数字、`_`、`-`，最多 120 字符。

## YAML Frontmatter

普通网页 / 公众号：

```yaml
---
url: "https://example.com/article"
requestedUrl: "https://example.com/article"
title: "Example Title"
author: "Ada"
publishedAt: "2026-06-05"
coverImage: "https://example.com/cover.jpg"
extractedVia: "browser-relay"
adapter: "generic"
extractedAt: "2026-06-05T08:00:00Z"
---
```

X thread：

```yaml
---
url: "https://x.com/foo/status/111"
requestedUrl: "https://x.com/foo/status/111"
author: "Foo Bar (@foo)"
authorName: "Foo Bar"
authorUsername: "foo"
tweetCount: 2
coverImage: "https://example.com/a.jpg"
extractedVia: "browser-relay"
adapter: "x"
extractedAt: "2026-06-05T08:00:00Z"
---
```

字段缺失时省略，不写 `null` 字符串。

## 正文

普通文章：

```markdown
# <title>

<body markdown>
```

X thread：

```markdown
## 1

<tweet text>

![](photo_url)

[查看推文](tweet_url)

## 2

<tweet text>
```

## 当前不支持

- 自动下载媒体到本地。
- 自动滚屏补全超长 thread。
- 跳过验证码、登录墙或权限墙。
