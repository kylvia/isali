# isali —— Claude harness 扩展包

> 你的个人 AI 工作流 harness。以 Claude 为大脑，以 skill 和 CLI 为手脚，以 profile 为配置。

## 设计宪法（三条北极星）

### 1. Context is precious
- SKILL.md ≤ 10 行主流程，细节全部去 `references/`
- 所有配置 **just-in-time 加载**，不在启动时预载
- profile 里存**引用**（路径/URL/ID），不存大块文本

### 2. Hooks guarantee, skills advise
- 不能漏的事 → **hook**（`hooks/*.yaml`）
- 需要 judgment 的事 → **skill**（`skills/*/SKILL.md`）
- 调整风格/偏好 → **profile**（`~/.isali/profile.yaml`）

### 3. Every skill must verify itself
- `skills/<name>/verify.sh` 是必填
- `skills/<name>/evals/` 至少 1 个 case
- 没 verify 不合入

## 开发约定

- **Python 3.9+**，默认 0 非标准依赖（PyYAML 有最好，没有时 profile.py 降级为 flat parser）
- 所有 CLI 统一入口 `bin/isali`，子命令派发
- 所有 CLI 支持 `--plan` / `--dry-run` / `--verbose`
- **非交互默认**：失败用非零 exit code，不弹交互 prompt
- 新 skill 必须从 `isali new-skill <name>` 脚手架生成
- 凭证永远不硬编码，读 profile 或环境变量

## 目录约定

```
isali/
├── bin/isali                 # 统一 CLI 入口
├── packages/isali_core/      # 共享 Python 库（profile/harness/logger/doctor）
├── skills/<name>/
│   ├── SKILL.md              # ≤10 行主流程 + 密集 trigger 关键词
│   ├── references/           # 详细文档（按需 load）
│   ├── scripts/              # 实际执行脚本
│   ├── verify.sh             # 必填：自检脚本
│   └── evals/                # 至少 1 个 case
├── profiles/default.yaml     # 默认 profile 模板
├── hooks/                    # hooks 配置示例
├── docs/
└── .claude-plugin/marketplace.json
```

## 关键命令

```bash
isali doctor              # 环境自检
isali push <md>           # 推公众号（vendored 公众号 SDK）
isali cover <prompt>      # 生成封面
isali fetch <url>         # 抓内容
isali new-skill <name>    # 脚手架
```

## 约束参考

- 公众号 SDK 已 vendor 到 `skills/isali-wechat-post/scripts/`（来源 JimLiu/baoyu-skills，见 `scripts/LICENSE.md`）
- 微信公众号凭证读 `~/.isali/wechat.env`（旧路径 `~/.baoyu-skills/.env` 仍兼容）
- isali 自己的配置在 `~/.isali/profile.yaml`
- 日志写 `~/.isali/logs/YYYY-MM-DD.jsonl`
