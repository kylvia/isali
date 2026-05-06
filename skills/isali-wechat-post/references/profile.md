# Profile 字段映射

## 核心模型：一个 profile = 一种声音

isali profile 的设计本意：**一个 profile 文件 = 一种身份 / 一种声音 / 一种写作风格**。CLI 把"profile 名字"做成一等公民概念，不需要手动改 env var。

```bash
isali profile list                  # 列出 ~/.isali/profiles/ 下所有风格
isali profile current               # 当前激活是哪个
isali profile switch <name>         # 激活：copy ~/.isali/profiles/<name>.yaml → ~/.isali/profile.yaml
isali profile show <name>           # 看某风格详情
isali profile show                  # 看当前激活的内容
isali profile edit                  # 用 $EDITOR 编辑当前激活 profile
isali profile diff <name1> <name2>  # 比对两种风格
```

文件解析顺序（packages/isali_core/profile.py）：

1. `$ISALI_PROFILE`（env override，临时单次切换用）
2. `~/.isali/profile.yaml`（`isali profile switch` 持久化激活后的内容）
3. fallback：repo 内的 `profiles/default.yaml`（兜底身份，**不承载具体风格**）

日常用 `isali profile switch` 就够了；只在 CI / 一次性脚本里临时切才用 `ISALI_PROFILE=...` env。

新建一种风格 = 复制 `profiles/_template.yaml` 到 `~/.isali/profiles/<风格名>.yaml` 改字段值，再 `isali profile switch <风格名>`。

## 字段映射

| Profile 字段 | 用途 |
|---|---|
| `wechat.default_theme` | `baoyu --theme` 默认主题（default/grace/simple/modern） |
| `wechat.account_alias` | 多账号时选哪个（baoyu 多账号） |
| `content.tone` | 写作语气一句话总括 |
| `content.length_target` | 目标字数范围 |
| `content.primary_color` | 文章内主色调（引用框、小标题） |
| `content.tags` | 文末话题标签 |
| `content.style.*` | 写作风格 9 维度结构化指令清单（详见下方） |
| `cta` | 文章结尾导流（如有） |
| `cover.aspect_ratio` | 封面比例 |
| `cover.style_preset` | 封面风格预设 |
| `cover.brand_color` | 封面色 |

字段为空时的兜底：
- theme: `default`
- tone / style.*: 未设置 → 不做风格约束
- tags / cta: 未设置 → 不加

## `content.style` 字段详解

`content.tone` 是**一句话**风格标签（适合给人看），`content.style.*` 是 9 维度**结构化指令清单**（适合喂给 subagent 当起草约束）。两者并用：tone 给方向，style 给落点。

| 字段 | 拆解问题 |
|---|---|
| `style.core_view` | 核心观点提炼：从素材里挑"那一句话"的方法 + 通常出现位置 |
| `style.persuasion` | 说服策略：类比 / 数据 / 故事 / 引经据典 的主用类型与比例 |
| `style.emotion_trigger` | 情绪触发点：高频词 / 句式（"其实"/"说穿了"/反问 等） |
| `style.sentence` | 金句构造：句长偏好 / 排比 / 对仗 / 反问的使用尺度 |
| `style.emotion_curve` | 情感曲线：平→高→平 / 冷→热 / 一直冷静 |
| `style.argumentation` | 论证方式：演绎（总→分）/ 归纳（分→总）/ 对比（A vs B） |
| `style.perspective` | 视角：人称、是否切换、何时拉远何时拉近 |
| `style.language` | 语言风格：书面 vs 口语、文白夹杂、网络梗尺度 |
| `style.hook` | 钩子设计：标题 / 开头 / 段间 各自模式 |

完整示例见 `profiles/_template.yaml`。

## 建一个新的风格 profile（仿作者 / 新建公司号子风格）

1. 抓 3 篇代表作（browser-relay → `/api/snapshot` 或 `isali fetch <url>`）
2. `cp profiles/_template.yaml ~/.isali/profiles/<风格名>.yaml`
3. 让 AI 按 9 维度逐项填 `content.style.*`（值用 YAML `|` 多行块写自然语言指令，不用关键词列表）
4. `isali profile switch <风格名>`
5. 验：`isali profile current` 确认 + 让 AI 用这套 profile 先模仿写 200 字，**抓到神韵**才起草正文
6. 不抓神韵 → `isali profile edit` 调字段，不要硬写

## 反模式（不要这么做）

- ❌ 把某种具体作者风格填进 `default.yaml` 的 `content.style.*` —— default 是兜底身份，会污染所有非显式切风格的场景
- ❌ 一个 profile 文件里塞多种风格（用 if/else 在字段里拼）—— profile 不该有条件分支
- ❌ 为单篇文章建一个 profile —— profile 是稳态的"声音"，单篇决策走 pipeline 的"配方预检"
