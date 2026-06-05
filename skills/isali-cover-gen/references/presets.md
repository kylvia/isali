# Prompt 预设

三套内置风格，通过 `--style` 或 `profile.cover.style_preset` 选择。

## minimal-tech（默认）

**视觉**：深蓝紫渐变背景 + 网格点阵质感 + 大字标题 + 紫罗兰粒子光轨

**适合**：AI 产品/技术发布、评测文章、信息类长文

**参考**：Apple Keynote / Figma 发布页

## editorial

**视觉**：奶油白纸张背景 + 粗黑手绘线条 + 左侧大标题 + 右侧白板信息图

**适合**：知识类文章、教程拆解、工具方法论、概念解释

**参考**：手绘白板信息图 / sketchnote / 知识博主封面

## poster

**视觉**：戏剧化渐变 + 电影感光影 + 粗体 display 字体 + tagline 式副标

**适合**：故事性强的文章、情绪类内容、话题事件

**参考**：Netflix 海报 / 电影宣传物料

## 添加自定义 preset

1. 在 `presets/` 目录下新建 `<name>.txt`
2. 可用占位符：`{title}` `{subtitle}` `{bullets_str}` `{aspect_ratio}` `{brand_color}` `{style}`
3. profile 或 `--style` 里引用这个 name

例：

```txt
# ~/.isali/presets/cyberpunk.txt   （或直接放到 skill 的 presets/ 目录）
设计一张 {aspect_ratio} 的赛博朋克风封面。主色 {brand_color}，
"{title}" 霓虹文字效果，副标题 "{subtitle}"，底部 {bullets_str}...
```
