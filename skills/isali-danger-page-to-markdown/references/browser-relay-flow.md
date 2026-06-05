# browser-relay 调用细节

## 端点

固定 `http://127.0.0.1:18795`，可通过 `--relay-url` 覆盖。

## 关键 API

| 用途 | 方法 + 路径 | 备注 |
|---|---|---|
| 健康检查 | `GET /api/debug` | 确认 extension 是否连接 |
| 导航 | `POST /api/navigate` | body `{ url, tabId? }` |
| eval JS | `POST /api/eval` | body `{ expression, tabId? }`，返回 adapter JSON |

## 当前实现

`scripts/main.py` 的在线路径：

1. `GET /api/debug`
2. `POST /api/navigate`
3. sleep 1.5s 等待页面基础渲染
4. 读取 `scripts/adapters/<adapter>.js`
5. 注入表达式：

```js
(async () => {
  // adapter source
  return await window.__isaliExtract();
})()
```

## adapter 约定

每个 adapter 必须定义：

```js
window.__isaliExtract = async function __isaliExtract() {
  return {
    adapter: "generic",
    kind: "article",
    url: location.href,
    title: "...",
    author: { name: "...", handle: null, url: null },
    publishedAt: "...",
    bodyHtml: "...",
    media: [],
    warnings: []
  };
};
```

X adapter 可以返回 `kind: "tweet"` 并使用 `thread` 数组；`scripts/main.py` 会单独渲染 thread。

## 调试

```bash
curl http://127.0.0.1:18795/api/debug

python3 scripts/main.py --plan 'https://example.com/article'
python3 scripts/main.py --health
```
