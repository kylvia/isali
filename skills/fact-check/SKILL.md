---
name: fact-check
description: Rigorous fact-checking of an article or claim. Flags numeric claims, weak sources, unsourced quotes, superlatives. Has both a regulatory mode (Claude follows the flow) and a static linter (`isali fact-check <md>`, no LLM). Triggers 关键词 "事实核查", "fact check", "verify claim", "核实数据", "找原始来源", "check sources", "交叉验证".
harness:
  requires: [WebSearch, WebFetch]
  graceful_degradation: true
---

# fact-check

## 主流程（Claude 执行时）

1. 识别可验证声明（数字 / 专有名词 / 直接引用 / 技术断言）
2. 源分级 → 见 `references/source-tiers.md`
3. 交叉验证（一手 ≥2 源 → ✅；单一三手源 → ⚠️）
4. 按 `references/report-format.md` 输出报告

## 静态 linter（不调 LLM）

```bash
isali fact-check <md> [--json] [--strict] [--warn-only]
```

扫四类风险（规则详见 `references/linter-rules.md`）：
- **numeric** — 百分比 / 排名 / elo / 耗时
- **weak_sources** — "据说"、"Reddit 上"
- **superlatives** — "首个"、"最快"、"碾压"
- **unsourced_quotes** — 引文附近无 `[link]`

## 常见陷阱

详见 `references/pitfalls.md`——引用的引用 / 媒体转述数字 / 翻译歧义等。

## 自查

- [ ] 每条声明都给了来源链接
- [ ] 一手来源优先
- [ ] 冲突明确标出
- [ ] 无法验证的标 ⚠️ 而不是默认采信
