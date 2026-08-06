# Image API 配置

## 默认端点

`gpt-image-2` 通过 liaobots 的 OpenAI 兼容接口：

- URL: `https://ai.liaobots1.work/v1/images/generations`（也可用 `ISALI_IMAGE_API_URL` 覆盖）
- Model name: `gpt-image-2`
- Auth: Bearer token

> **2026-08-06 变更**：`gpt-image-2` 已从上游的 Chat Completions 端点下线，走 `/v1/chat/completions` 会返回
> `400 This model is not supported on the Chat Completions endpoint`。请求体也随之从 `messages` 改为 `prompt`。
> `generate.py` 现在会把配置里以 `/chat/completions` 结尾的 URL 自动重写成 `/images/generations`，
> 所以旧的 `~/.isali/image.env` / `profile.yaml` 不改也能用。

默认 API key 已内置（开箱即用），优先级：

1. 环境变量 `ISALI_IMAGE_API_KEY`
2. `~/.isali/profile.yaml` → `image.api_key`
3. 内置默认

## 自定义端点

如果要改用其他提供方（OpenAI 官方 / Azure / 其它中转）：

```yaml
# ~/.isali/profile.yaml
image:
  api_url: https://api.openai.com/v1/images/generations
  model: dall-e-3
  # api_key 建议走环境变量而非写文件
```

**注意**：不同端点的请求/响应格式可能不同。当前 `generate.py` 发标准 images 请求体（`prompt` / `n` / `size`），并按以下顺序解析响应：

1. `data[0].b64_json`（标准 images 端点，当前生产路径）
2. `data[0].url`（下载到本地）
3. `choices[0].message.content` 里的 `data:image/...;base64,...` 或 Markdown 图片链接 —— 兼容旧的 chat 风格网关，避免上游回滚时再次失效

## 性能

单次生成耗时约 **22-60 秒**（受内容复杂度影响）：
- 简单图形 ~22s
- 含大量文字/布局 ~45-55s

## 尺寸

请求体显式传 `size`（默认 `1536x1024`）。prompt 里再描述 aspect ratio（如 "2.35:1"）可影响构图，但实际画布尺寸由 `size` 决定。需要 2.35:1 封面时，用 `1536x1024` 出图后裁切：

```bash
python3 -c "
from PIL import Image
im=Image.open('cover.png');w,h=im.size;th=int(w/2.35);t=(h-th)//2
im.crop((0,t,w,t+th)).save('cover-crop.png')"
```

## 失败排查

- **400 `not supported on the Chat Completions endpoint`**：端点/请求体不匹配，见文首 2026-08-06 变更说明
- 超时：默认 180s，复杂图可能触发；调大 timeout
- 返回无图：报错会带响应 head，检查是否是文本回复（prompt 偏移）
- HTTP 错误现在会直接抛出网关原文（状态码 + body 前 300 字），不再是裸 traceback
