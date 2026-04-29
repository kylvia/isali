# isali

> 你的个人 Claude harness 扩展包。
> 以 Claude 为大脑，以 skill 和 CLI 为手脚，以 profile 为配置。

---

## 是什么

isali 是一个**可扩展的 AI 工作流工具箱**。它在 Claude Code 之上加一层你自己的定制——把你每天用 AI 重复做的事（推公众号、生成封面、抓内容、事实核查）**沉淀为 skill 和 CLI**，让 Claude 调用更确定、更一致、更可审计。

**不绑领域**——内容创作、运维部署、前端原型、研究写作，都能扩进来。

---

## 设计哲学（三条北极星）

### 1. Context is precious
SKILL.md 短小精炼（≤10 行主流程），细节去 `references/`；profile 懒加载、存引用而非内容。

### 2. Hooks guarantee, skills advise
**不能漏的事**用 hook（PreToolUse/PostToolUse 确定性触发）；**需要判断的事**用 skill；**调偏好**用 profile。

### 3. Every skill must verify itself
每个 skill 必须有 `verify.sh` 和至少 1 个 eval case。没 verify 不合入。

---

## 快速开始

### 安装

```bash
# 已做过的话跳过
claude plugin marketplace add ~/isali
claude plugin install isali@isali

# MCP server（可选，让 Claude 直接调 isali tools 不走 Bash）
uv venv ~/.isali/venv --python 3.11
uv pip install --python ~/.isali/venv/bin/python "mcp[cli]"
claude mcp add isali ~/.isali/venv/bin/python --scope user -- \
    ~/isali/packages/isali_mcp/server.py
```

### 配置自己的 profile

```bash
# 编辑默认 profile（影响所有 isali 命令）
vim ~/.isali/profile.yaml

# 或用不同 profile 覆盖（如 liaox 品牌）
ISALI_PROFILE=~/.isali/profiles/liaox.yaml isali push my-article.md
```

### 环境自检

```bash
isali doctor
```

---

## 命令参考

| Command | 作用 |
|---|---|
| `isali doctor` | 环境/依赖/凭证自检 |
| `isali push <md>` | 推送 markdown 到微信公众号草稿箱（vendored 公众号 SDK） |
| `isali cover --title T --subtitle S --bullets ...` | 生成文章封面图（gpt-image-2） |
| `isali fetch <url>` | 抓网页/公众号→markdown |
| `isali fact-check <md>` | 静态事实核查 linter |
| `isali new-skill <name>` | 新 skill 脚手架 |
| `isali version` | 打印版本 |

所有命令支持：`--plan` `--dry-run` `--verbose` `--json`。

---

## 目录结构

```
isali/
├── CLAUDE.md                        # 项目宪法 + 开发约定
├── README.md
├── .claude-plugin/marketplace.json
│
├── bin/isali                        # 统一 CLI 入口
│
├── packages/
│   ├── isali_core/                  # 共享库
│   │   ├── profile.py               # profile 懒加载 + 点号路径
│   │   ├── harness.py               # 运行环境能力检测
│   │   ├── logger.py                # 审计日志
│   │   ├── doctor.py                # 环境自检
│   │   └── new_skill.py             # 脚手架
│   └── isali_mcp/
│       └── server.py                # MCP 包装（FastMCP）
│
├── skills/
│   ├── isali-wechat-post/           # 工具型
│   ├── isali-cover-gen/             # 工具型（3 套 preset）
│   ├── isali-fetch/                 # 工具型
│   └── fact-check/                  # 规范型 + 静态 linter
│
├── profiles/default.yaml            # 默认 profile 模板
├── hooks/                           # Claude Code hooks 示例
└── docs/
```

Skill 内部约定：
```
skills/<name>/
├── SKILL.md            # ≤10 行主流程 + 密集 trigger 关键词
├── references/         # 详细文档，按需 load
├── scripts/main.py     # CLI 入口（工具型）
├── verify.sh           # ★ 必填：自检
└── evals/case-01.yaml  # ★ 至少 1 个
```

---

## 如何加新 skill

```bash
isali new-skill isali-my-thing "Do something useful"
```

脚手架会生成 `SKILL.md` / `verify.sh` / `evals/case-01.yaml` 骨架。

然后：
1. 编辑 `SKILL.md`（触发词 + 主流程）
2. 实现 `scripts/main.py`（CLI 参数 + 真实逻辑）
3. 扩展 `verify.sh`（自检）
4. 加 entry 到 `bin/isali` 的 `COMMANDS` dict

---

## 如何加新 profile（换品牌/换角色）

```bash
# 1. 复制模板
cp ~/.isali/profiles/default.yaml ~/.isali/profiles/<brand>.yaml

# 2. 改 tone / cta / primary_color / tags
vim ~/.isali/profiles/<brand>.yaml

# 3. 激活（二选一）
#    临时：
ISALI_PROFILE=~/.isali/profiles/<brand>.yaml isali push ...
#    永久：
cp ~/.isali/profiles/<brand>.yaml ~/.isali/profile.yaml
```

所有 skill 自动读新 profile。

---

## 与 Claude Code 的关系

isali 是**你自己定制的 harness**，坐在 Claude Code 之上：

```
     你的意图（"帮我推公众号"）
               ↓
┌───────────────────────────────────┐
│  Claude Code (Anthropic 的 harness) │
│  ├── 自带 hooks / settings / skills │
│  └── 调用你的 isali tools           │
└───────────────────────────────────┘
               ↓
┌───────────────────────────────────┐
│  isali (你的 harness 扩展)          │
│  ├── skills/* (judgment)           │
│  ├── bin/isali (确定性 CLI)         │
│  ├── profile (what to use when)    │
│  └── MCP server (暴露 tools)        │
└───────────────────────────────────┘
               ↓
       公众号 SDK (vendored) / gpt-image-2 / urllib
```

---

## 关键设计点

- **统一 CLI**：一个 `isali` 命令根，子命令派发，像 `kubectl`
- **品牌抽离**：风格/CTA/颜色全在 profile，skill 纯通用
- **底层复用**：vendor JimLiu/baoyu-skills 的 4 个 TS 文件做公众号推送、不重写 browser-use（浏览器自动化），只做上层编排
- **Python 优先**：0 非标准依赖（MCP server 走独立 venv，opt-in）
- **可观测**：每次调用写 JSONL 到 `~/.isali/logs/`
- **非交互默认**：所有命令能在 cron/CI/webhook 里跑，失败非零退出

---

## FAQ

**Q: 和 baoyu-skills 什么关系？**
A: 我们 vendor 了 [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) 的 `baoyu-post-to-wechat` 4 个 TS 文件到 `skills/isali-wechat-post/scripts/`（见 `LICENSE.md`），不再依赖外部插件安装。`isali` 在这之上加 profile/hooks/fact-check 等编排能力。

**Q: 必须用 Claude Code 吗？**
A: skill 部分是 Claude Code 特化的。但 CLI (`isali *`) 纯 shell 可用——cron、脚本、CI 都行。

**Q: 想开源？**
A: 当前定位是"先个人用（Phase 1），稳定后再 GitHub（Phase 2）"。想提前开源也 ok，把 `~/.isali/` 里的个人数据清理掉即可。

**Q: 多人/多品牌/多公众号怎么管？**
A: 多个 profile 文件并存（`~/.isali/profiles/*.yaml`），用 `ISALI_PROFILE` 切换。多公众号账号走公众号 SDK 的多账户配置（`--account <alias>`）。

---

## 当前版本

`isali 0.1.0` — Phase 1（个人可用）。后续 roadmap：
- Phase 2：更多 skill（翻译 / 代码审查 / 部署辅助）；hooks 生态
- Phase 3：evals 自动化；skill 市场
