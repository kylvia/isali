---
name: isali-writing-recipe
description: 动笔前定配方。跑 7 问预检 + 素材预检，匹配 recipes/ 库里的结构模板，输出"配方卡"（markdown）给下游写作 skill / subagent 起草用。Triggers 关键词 "定配方", "配方卡", "写作配方", "7 问预检", "writing recipe", "动笔前", "文章配方", "怎么写这篇", "结构怎么搭", "选题已定下一步".
harness:
  requires: [Read]
  graceful_degradation: true
---

# isali-writing-recipe

诺鸭船长 (@noahduck283) 工作流里 "Phase 3：动笔前先把配方定死" 的 isali 化实现。
跟 profile 的 9 维文风**正交**——profile 管"作者声音"（每个 profile 一种），recipe 管"文章结构"（每篇文章一种）。

## 主流程（5 步）

1. **接素材** — 用户给：选题 / 已抓的素材 / 引用文章 / 标题候选。
2. **跑 7 问预检** — 读 `references/intake-7q.md`，逐题问用户。每题都要拿到一个明确答案，含糊的退回补素材。
3. **跑素材预检** — 读 `references/material-precheck.md`，对照 3 个硬门槛（画面级事例 / 数据有出处 / 原创差异点）。任一不达标 → **不能动笔**，退回补素材。
4. **匹配配方** — 读 `references/recipes/README.md` 决策树，从 7 问答案路由到一个 recipe；读对应 `references/recipes/<name>.md` 提取结构 / 推进器 / 情绪曲线。
5. **输出配方卡** — 按下方 schema 输出 markdown，存到用户指定路径或返回字符串。

## 配方卡输出 schema（固定）

```markdown
# 配方卡 — <文章标题草稿>

> 生成时间：<ISO date>
> Recipe：<recipe-name>
> 推荐 profile：<profile-name>

## 7 问回执
1. 文章类型：...
2. 核心判断（一句话）：...
3. 目标读者：...
4. 开头钩子类型：...
5. 结尾落点：...
6. 情绪模板：...
7. 争议级别：L0 / L1 / L2

## 素材预检
- 画面级事例：[√/✗] <列出>
- 有出处数据：[√/✗] <列出>
- 原创差异点：[√/✗] <列出>

## 主结构（按段落）
1. <段落 1 任务> — 推进器：<手法>
2. ...

## 情绪曲线
<一句话描述>

## 风格搭配建议
- profile: <name>（理由：...）
- 不要踩的雷：...
```

## 调用方式

直接在 Claude 里说"定配方 / 配方卡 / 跑 7 问"等触发词，或：

```
请用 isali-writing-recipe 给以下选题定配方：
<选题描述>
<已有素材（可选）>
```

不需要 CLI——本 skill 是 prompt-driven，Claude 主 session 直接跑。

## 跟其他 skill 的关系

- **上游**：`isali-fetch`（抓参考素材）/ `liao-wechat-article-pipeline`（选题已定后调用本 skill 而非直接起草）
- **下游**：subagent 起草 / `isali-wechat-post`（推草稿）/ `isali-cover-gen`（配图）
- **正交**：`~/.isali/profiles/*.yaml` 的 9 维文风——本 skill 不动 profile，只在配方卡里**推荐**用哪个 profile。

## 添加新配方（沉淀）

写完一篇文章觉得"这个结构跟现有 recipe 都不一样"？

1. cp `references/recipes/pain-point-tutorial.md` 到 `references/recipes/<新名字>.md`
2. 改 schema 各字段，附 1 篇代表作链接做引证
3. 编辑 `references/recipes/README.md`：在索引加一行 + 决策树补一条分支

目标：写 10 篇 → 沉淀 5-7 个常用 recipe，覆盖 80% 选题。

## 自查

- [ ] 7 问每题都有明确答案，没有"差不多就行"
- [ ] 素材预检 3 项都过门槛，否则未输出配方卡
- [ ] 配方卡里"推荐 profile" 字段填了，理由可观测
- [ ] 没有把"作者文风"（9 维）抄进配方卡——那是 profile 的事
- [ ] 失败 / 退回时明确告诉用户缺什么、回哪一步
