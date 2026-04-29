---
name: isali-cover-gen
description: Generate a WeChat-quality article cover image via gpt-image-2. Reads cover style preset + brand color from ~/.isali/profile.yaml. Triggers 关键词 "生成封面", "做封面", "cover image", "文章配图", "公众号封面", "gpt-image", "封面设计", "make cover".
harness:
  requires: [Bash]
  graceful_degradation: true
---

# isali-cover-gen

## 主流程（3 步）

1. 从 profile 读 `cover.style_preset` + `cover.brand_color` + `cover.aspect_ratio`
2. 选 prompt 模板（`presets/<style>.txt`），填入标题/副标题/数据点
3. 调 gpt-image-2 API，保存 PNG，返回路径

## 调用方式

```bash
isali cover --title "GPT-Image-2" --subtitle "一次跳过两代" \
            --bullets "Arena 榜单 #1" "+241 分" \
            --style minimal-tech  --out ./cover.png
```

或直接传完整 prompt：

```bash
isali cover --prompt "your full prompt"  --out ./cover.png
```

## 详细参考

- 内置 prompt 预设 → `references/presets.md`
- API 凭证/端点配置 → `references/api.md`
- 输出比例 / 模型能力边界 → `references/limits.md`

## 自查

- [ ] 所有文字 prompt 中只用 profile/参数提供的内容
- [ ] 输出比例与 profile 一致
- [ ] 耗时记录到审计日志
- [ ] 失败时返回非零退出
