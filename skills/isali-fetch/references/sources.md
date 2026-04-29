# 支持的源 + 策略

| 域名 | source 标签 | 策略 | 可用 |
|---|---|---|---|
| `mp.weixin.qq.com` | `wechat` | UA 伪装 + 正则提取 `rich_media_content` | ✅ |
| `x.com` / `twitter.com` | `x` | 需要 `auth_token` + `ct0` cookie | ⚠️ 需配置 |
| 其它 | `web` | 通用 urllib，HTML→Markdown | ✅ |

## 为什么公众号需要 UA 伪装

微信对非浏览器 UA 会返回"环境异常，完成验证后即可继续访问"的拦截页。默认 `WebFetch` 或裸 `curl` 都会中招，我们的 UA 设为标准 Chrome 指纹即可绕过。

## 通用 web 抓取的限制

- 不执行 JavaScript（纯静态 HTML）
- SPA（React/Vue 纯前端渲染）的页面可能拿不到正文
- 对这类页面，推荐用 `browser-use` 的浏览器模式而非 fetch

## X/Twitter 为什么麻烦

X 把未登录用户访问公开推文也**限速 + 部分隐藏**（尤其视频无法播放、媒体模糊）。要拿到干净内容需要 `auth_token` + `ct0` cookie。

- cookie 如何获取 → `references/x-auth.md`
- 拿到后通过 `--cookie auth_token=XXX --cookie ct0=YYY` 传入
