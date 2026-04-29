# Profile 字段映射

从 `~/.isali/profile.yaml` 读取的字段，以及 skill/CLI 如何使用。

| Profile 字段 | 用途 |
|---|---|
| `wechat.default_theme` | `baoyu --theme` 默认主题（default/grace/simple/modern） |
| `wechat.account_alias` | 多账号时选哪个（baoyu 多账号） |
| `content.tone` | 写作时语气约束 |
| `content.length_target` | 目标字数范围 |
| `content.primary_color` | 文章内主色调（引用框、小标题） |
| `content.tags` | 文末话题标签 |
| `cta` | 文章结尾导流（如有） |
| `cover.aspect_ratio` | 封面比例 |
| `cover.brand_color` | 封面色 |

所有字段为空时，skill 使用**合理默认**：
- theme: `default`
- tone: 未设置 → 不做风格约束
- tags: 未设置 → 不加
- cta: 空数组 → 不加导流段
