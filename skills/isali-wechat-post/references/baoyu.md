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
