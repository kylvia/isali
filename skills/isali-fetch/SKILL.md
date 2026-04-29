---
name: isali-fetch
description: Fetch URL content and convert to markdown. Handles WeChat (mp.weixin.qq.com) with UA-spoofing, generic webpages, and X/Twitter (requires cookie). Output structured markdown with title/author/date metadata. Triggers 关键词 "抓文章", "抓网页", "fetch url", "下载公众号", "保存为 markdown", "公众号正文", "把网页变成 md", "fetch article".
harness:
  requires: [Bash]
  graceful_degradation: true
---

# isali-fetch

## 主流程

1. 识别 URL 来源类型（wechat / web / x）
2. 用对应策略抓取（公众号走 UA 伪装 + 正则；通用走 urllib）
3. HTML → Markdown（保留标题层级、图片、链接）
4. 输出到 stdout 或 `--out` 指定文件

## 调用方式

```bash
isali fetch https://mp.weixin.qq.com/s/xxx              # stdout
isali fetch <url> --out article.md                      # 保存
isali fetch <url> --json                                # JSON 含 metadata
isali fetch <url> --plan                                # 只识别源不抓取
```

## 详细参考

- 支持的源 + 策略差异 → `references/sources.md`
- 公众号解析细节（正则/字段）→ `references/wechat-detail.md`
- X/Twitter 的 cookie 配置 → `references/x-auth.md`

## 自查

- [ ] 公众号抓取成功 = 返回 title/author/date/body 非空
- [ ] 通用网页抓取 = 至少有 body
- [ ] 请求带合理 UA，避免被基础反爬拦截
- [ ] 网络失败返回非零 exit
