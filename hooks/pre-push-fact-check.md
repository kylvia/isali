# Hook: Fact-check before wechat push

**What it does**: 每当 Claude 要执行 `isali push <md>` 时，先自动跑 fact-check linter 扫 markdown。发现可疑点 → 提示 Claude 要不要继续。

## 适用场景

你希望避免"一冲动就发出去"的文章。这条 hook 在推送**前**强制过一遍静态核查。

## 如何安装

编辑 `~/.claude/settings.json`，在 `hooks.PreToolUse` 里加：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(isali push *)",
            "command": "md=$(jq -r '.tool_input.command' | grep -oE 'isali push [^ ]+' | awk '{print $3}'); if [ -n \"$md\" ] && [ -f \"$md\" ]; then ~/isali/bin/isali fact-check \"$md\" --warn-only; fi",
            "timeout": 10,
            "statusMessage": "Running fact-check before push..."
          }
        ]
      }
    ]
  }
}
```

## 能力

- **非阻塞版**（上面配置，默认）：只打印报告，不阻止推送
- **阻塞版**：把命令末尾的 `--warn-only` 改成 `--strict`，任何 finding 都会阻止推送

## 替代方案：用 skill 层面触发

如果你不想改全局 `~/.claude/settings.json`，另一个做法是让 `isali-wechat-post` 的 SKILL.md 约定"推送前 Claude 必须先 call fact-check"。但这是 advisory（Claude 可能忘），不如 hook 确定。

（这正是"hooks guarantee, skills advise"的体现）

## 测试

```bash
# 不会真推送，验证 hook 触发
isali push my-article.md --dry-run
```

会看到 `Running fact-check before push...` 状态消息，日志里有 fact-check 输出。
