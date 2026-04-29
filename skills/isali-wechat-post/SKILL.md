---
name: isali-wechat-post
description: Push a markdown article to WeChat Official Account draft box. Reads style/CTA/tags from ~/.isali/profile.yaml; runs the vendored wechat-api.ts (originally from JimLiu/baoyu-skills, see scripts/LICENSE.md) via bun. Triggers 关键词 "推公众号", "发公众号", "post to wechat", "microsoft 公众号", "微信草稿", "push wechat", "发到公众号", "推到草稿箱".
harness:
  requires: [Bash]
  graceful_degradation: true
---

# isali-wechat-post

## 主流程（4 步）

1. 读 profile 风格 → 决定字数/语气/CTA
2. 确认 MD 就绪，本地预览通过 (`isali push <md> --dry-run`)
3. 推送到草稿箱 (`isali push <md>`)
4. 提醒用户去微信公众平台 → 草稿箱预览 → 群发

## 详细参考

- profile 字段映射 → `references/profile.md`
- baoyu 底层命令 → `references/baoyu.md`
- 标题/摘要/封面选择 → `references/article-fields.md`
- 多账号切换 → `references/multi-account.md`
- 失败排查（IP 白名单 / token 过期 / 图上传）→ `references/troubleshoot.md`

## 自查

- [ ] 所有数据可追溯一手源
- [ ] CTA 从 profile 读，不硬编码
- [ ] 封面图比例 2.35:1 或接近
- [ ] 标题风格符合 `profile.content.tone`
