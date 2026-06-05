# DOM 抽取策略

## 入口

adapter 位于 `scripts/adapters/`，每个文件定义：

```js
window.__isaliExtract = async function __isaliExtract() { ... };
```

`scripts/main.py` 通过 browser-relay `/api/eval` 注入 adapter，并把返回 JSON 渲染为 markdown。

## 统一结果结构

普通文章 / 公众号：

```ts
type PageExtractResult = {
  adapter: "generic" | "wechat";
  kind: "article" | "unknown";
  url: string;
  title: string | null;
  author: { name: string; handle?: string | null; url?: string | null } | null;
  publishedAt: string | null;
  bodyHtml: string;
  media: Array<{ type: "photo"; url: string; alt?: string }>;
  warnings: string[];
};
```

X tweet/thread：

```ts
type XExtractResult = {
  adapter: "x";
  kind: "tweet" | "article" | "unknown";
  tweetId: string | null;
  url: string;
  author: { name: string; handle: string; avatarUrl: string | null } | null;
  thread: TweetNode[];
  article: { title: string; html: string } | null;
  warnings: string[];
};
```

## adapter 选择

| URL | adapter |
|---|---|
| `x.com` / `twitter.com` | `x` |
| `mp.weixin.qq.com` | `wechat` |
| 其他 | `generic` |

也可通过 `--adapter generic|wechat|x` 强制指定。

## generic adapter

策略：

1. 读取 `og:title` / `h1` / `document.title`。
2. 读取 `article:author` / `author` / `[rel=author]`。
3. 候选正文优先级：`[itemprop=articleBody]`、`article[role=main]`、`main article`、`article`、`main`、`body`。
4. 按段落文本密度选最佳节点。
5. 移除脚本、导航、广告、表单、iframe、inline style/class/data。
6. 将相对链接和图片 URL 解析为绝对 URL。

## wechat adapter

策略：

1. 标题：`#activity-name` / `h1.rich_media_title`。
2. 作者：`#js_name` / `.rich_media_meta_nickname`。
3. 时间：`#publish_time` / `em.rich_media_meta_text`。
4. 正文：`#js_content` / `.rich_media_content`。
5. 图片：`data-src` 归一化为 `src`。
6. 检测 `#js_verify` 等异常页，返回 warning 而不是假装成功。

## x adapter

保留早期 X DOM 抽取逻辑：

- tweet 容器：`article[data-testid="tweet"]`
- 正文：`[data-testid="tweetText"]`
- 图片：`[data-testid="tweetPhoto"] img`
- 时间：`time[datetime]`
- 长文：`[data-testid="article-body"]`

X DOM 变化频繁，抽取失败时优先更新 `scripts/adapters/x.js`，不要在 `main.py` 里堆站点特例。
