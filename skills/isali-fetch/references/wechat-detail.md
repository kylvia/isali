# 公众号抓取细节

## 解析的字段

| 字段 | 正则 | 备注 |
|---|---|---|
| title | `var msg_title = '...'` / `<h1 id="activity-name">...</h1>` | |
| author | `var nickname = '...'` | |
| date | `var ct = "<unix_ts>"` | 转本地时间 YYYY-MM-DD HH:MM |
| body | `<div class="rich_media_content" id="js_content">...</div>` | 直到下一个 `<script` |

## body 转 Markdown 的处理

- `<h1>`..`<h6>` → `#`..`######` 保留层级
- `<img src|data-src>` → `![](url)`
- `<p>` / `<div>` / `<section>` → 换行
- `<li>` → `- `
- `<b>` / `<strong>` → `**`
- `<a href="">` → `[text](url)`
- HTML entities: `&nbsp; &amp; &lt; &gt; &quot;` 等自动替换

## 已知限制

- **视频**：公众号内嵌视频是 iframe，提取不到源地址
- **音频**：同上
- **小程序卡片**：提取不到内容，只能看到占位标签
- **图片防盗链**：公众号图片通过 data-src 懒加载，我们提取后 URL 直接在浏览器能看，但嵌入别的站点会被拦截
- **外部链接**：公众号会把所有外链转成 `mp.weixin.qq.com/safe?url=...`，我们不做还原（保留原样）

## 典型输出

```markdown
# 文章标题

> 公众号名 · 2026-04-24 12:00

正文第一段...

## 小标题

正文第二段...

![](https://mmbiz.qpic.cn/mmbiz_png/xxx)

---

source: https://mp.weixin.qq.com/s/xxx
```
