# Linter 正则规则

`scripts/main.py` 里的静态扫描规则详表。

## numeric（数字声明，需验证）

| 模式 | 例 |
|---|---|
| `+?\d+(\.\d+)?\s*%` | 50%、+2.3% |
| `+?\d{3,}(\.\d+)?\s*(分|elo|points?)` | 1512 分、1271 elo |
| `第\s*\d+\s*名|#\s*\d+|排名第?\s*\d+` | 第 1 名、#3、排名第 2 |
| `\d+(\.\d+)?\s*(秒|分钟|小时|毫秒|ms|s|sec|min|hour)` | 35.3 秒、1.5 小时 |
| `\d+(,\d{3})*\s*(人|万|亿|次)` | 13 人、1.2 万次 |

## weak_sources（弱来源标记）

触发词：
- 中文：`Reddit 上`、`据说`、`有人说`、`听说`、`传言`、`好像`、`似乎`、`大概`、`网上有人`、`据传`
- 英文：`rumored`、`allegedly`、`reportedly`、`supposedly`

## superlatives（最高级）

触发词：
- 中文：`最快`、`最强`、`最好`、`唯一`、`首个`、`第一次`、`前所未有`、`碾压`、`吊打`、`史上`、`永远`、`绝对`
- 英文：`fastest`、`first ever`、`strongest`、`unbeatable`

最高级不是错——但如果后面**没数据支撑**就是夸张。linter 标出让 Claude / 人审。

## unsourced_quotes（无源引文）

匹配：`「……」`、`"……"`、`"……"`（≥ 4 字）

启发式：本行 + 前后 1 行窗口内**没有** `[文字](URL)` 或裸 `https?://` → 标注。

**例外（lint 抓不到）**：
- 术语、产品名本身（"GPT-4"、"Opus 4.6"）不需要来源
- 常识性短语（"一次跳过两代"）不需要
- Claude 审阅时要**人工排除这类**

## 退出策略

| 策略 | 触发条件 | 退出码 |
|---|---|---|
| 默认 | `numeric` 和 `weak_sources` **都非空** | 1 |
| `--strict` | 任一类别非空 | 1 |
| `--warn-only` | 任何情况 | 0 |

## 扩展

改 `scripts/main.py` 顶部的 `NUMERIC_PATTERNS` / `WEAK_SOURCE_MARKERS` / `SUPERLATIVES` 列表即可增减规则。
