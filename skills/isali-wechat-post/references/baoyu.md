# 底层命令

`isali push` 是 `wechat-api.ts`（vendored from baoyu-skills, see `scripts/LICENSE.md`）的薄封装。真实命令：

```bash
bun <isali>/skills/isali-wechat-post/scripts/wechat-api.ts \
  <md_path> \
  --theme <theme> \
  --cover <cover_path>
```

> 首次运行 `isali push` 会自动在 `scripts/` 目录跑 `bun install` 拉 npm 依赖（baoyu-md / jimp / @jsquash/webp）。

常用参数（`isali push` 全部透传）：

- `--theme default|grace|simple|modern`
- `--color <name|hex>`（覆盖主题色）
- `--cover <path>`（封面图，未指定则从 MD frontmatter 或第一张内嵌图）
- `--title <str>`（覆盖 MD 里的标题）
- `--author <str>`
- `--summary <str>`（摘要，<= 128 字符）
- `--account <alias>`（多账号）
- `--no-cite`（关闭"外链自动转底部引用"）
- `--dry-run`（不实际发布，只看渲染）

## 凭证

`bun` 脚本读取 `~/.baoyu-skills/.env`，包含 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`。

## IP 白名单注意

报错 `40164: invalid ip <IP>, not in whitelist` 时——**权威 IP 以 40164 报错里的为准**，不是 `ipinfo.io` 返回的 CDN IP。去微信公众平台 → 基本配置 → IP 白名单加。

## 代理环境变量（已在 main.py 自动 normalize）

`isali push` 通过 `subprocess` 调起 `bun`。Bun ≥ 1.3 的 `fetch` 在 subprocess 链路下**只认小写** `https_proxy` / `http_proxy`，不认大写 `HTTPS_PROXY` / `HTTP_PROXY`。

历史症状：`Fetching access token...` 紧跟 `Error: The socket connection was closed unexpectedly.`，但同一个 `HTTPS_PROXY` 直接 `bun -e 'await fetch(...)'` 又能通。

`main.py` 在 spawn bun 之前会自动把这 4 对 proxy 变量同步成大小写双份（`_normalize_proxy_env`），所以**用户/上层 pipeline 只需要 export 大写或小写任意一组即可**，不再需要"4 个全 export"那种迷信操作。涉及变量：

- `HTTPS_PROXY` ↔ `https_proxy`
- `HTTP_PROXY` ↔ `http_proxy`
- `NO_PROXY` ↔ `no_proxy`
- `ALL_PROXY` ↔ `all_proxy`

已设的那一侧不会被覆写，只补另一侧。
