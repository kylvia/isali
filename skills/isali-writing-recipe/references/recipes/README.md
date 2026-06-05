# Recipes 索引

每个 recipe = 一种**结构模板**。跟 profile（作者声音）正交——同一个 recipe 可以用不同 profile 演奏出不同味道。

## 当前配方库

| recipe | 适用类型 | 一句话 |
|---|---|---|
| [pain-point-tutorial](pain-point-tutorial.md) | 痛点解决 | 描述常见痛点 → 拆穿核心问题 → 分步教程 → 收益数据 → 行动召唤 |
| [news-takeaway-with-twist](news-takeaway-with-twist.md) | 资讯解读 | 反直觉角度切入 → 单句拆穿 → 3 个画面级支撑 → actionable → 金句收尾 |

> 后续每写一篇沉淀 1 个新配方。

## 决策树（从 7 问 → recipe）

```
Q1 文章类型 = ?

├─ 痛点解决
│  └─ Q4 钩子 = 场景认领 + Q6 情绪 = 共鸣→认知
│     → pain-point-tutorial
│
├─ 资讯解读
│  ├─ 有反直觉角度（Q4 钩子 = 悬念抛出 + Q7 争议 = L1）
│  │  → news-takeaway-with-twist
│  └─ 流水复述无 twist
│     → (待补：news-takeaway 普通版)
│
├─ 信息差          → (待补：info-asymmetry)
├─ 反思感悟        → (待补：reflection-narrative)
├─ 评测对比        → (待补：evaluation-compare)
├─ meta 方法论     → (待补：meta-methodology)
└─ 故事叙事        → (待补：story-narrative)
```

**找不到匹配的 recipe？**
- 暂时用最接近的 + 在配方卡里标注"无完全匹配，已用 X recipe 调整以下字段：..."
- 写完后 → 决定要不要沉淀成新 recipe（参考下方 schema）

## Recipe 文件 schema（添加新配方时遵循）

```markdown
# <recipe-name>

> 一句话适用场景

## 适用判断

- 文章类型：<Q1 选项>
- 推荐钩子类型：<Q4 选项>
- 推荐情绪模板：<Q6 选项>
- 不推荐场景：<什么情况下不要用>

## 主结构（按段落）

| # | 段落任务 | 推进器 | 字数占比 |
|---|---|---|---|
| 1 | <做什么> | <怎么过渡到下一段> | <%> |
| 2 | ... | ... | ... |

## 情绪曲线

<一句话 + 用箭头图：平→共鸣→平→俏皮>

## 争议级别建议

<L0/L1/L2 + 理由>

## 素材预检要求（在通用门槛之上的 recipe-specific 要求）

- <比如：必须有"我自己跑过的数据"，不能只引二手>

## 风格搭配建议

- profile：<推荐 profile 名> — 理由：<为什么>
- 不要踩的雷：<比如：避免书面语过重、避免长句>

## 引证样本

- <文章链接 + 一句话点出哪里体现了这个结构>
```

## 沉淀新配方的时机

写完一篇文章，**自检 3 题**：
1. 这篇用的结构跟现有 recipe 完全一样吗？
2. 如果不一样，这个新结构能在未来 5 篇内复用吗？
3. 能用 1 个名字概括它的核心特征吗？

3 个都 √ → 抽成新 recipe 沉淀进 `recipes/`。
