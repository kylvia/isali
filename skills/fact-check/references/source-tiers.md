# 源分级规则

| 级别 | 示例 | 采信度 |
|---|---|---|
| **一手** | 官方发布、论文原文、API 直返结果、榜单官方截图、直播回看 | ⭐⭐⭐ |
| **二手** | 原厂博客、官方 X 账号推文、官方开发者社区 | ⭐⭐ |
| **三手** | 媒体报道（TechCrunch 等）、Reddit 帖子、公众号转述、YouTube 评论 | ⭐ |

## 规则

1. **所有一手可查证的声明**必须查到一手
2. **数字**一律追溯一手（比如跑分去 arena.ai 官网核对精确值）
3. **直接引述**必须有原始来源 URL
4. **只有一个三手源**支持的声明 → `⚠️ 标注"待补证"` 或删除

## 常见一手来源

| 领域 | 一手 |
|---|---|
| AI 模型榜单 | arena.ai, huggingface.co, papers with code |
| OpenAI 官方 | openai.com/blog, platform.openai.com, help.openai.com |
| Anthropic | anthropic.com/news, docs.anthropic.com |
| Google | blog.google, developers.google.com |
| GitHub/开源项目 | repo README、release notes、issues |
| 学术 | arxiv.org, openreview.net, neurips/iclr proceedings |

## 找不到一手怎么办

三个出路：
1. 尝试英文关键词搜（中文转述往往丢信息）
2. 顺着三手文章里的链接链逐级上溯
3. 找不到就**明确标 ⚠️ 待补证**，不要"冒充一手"
