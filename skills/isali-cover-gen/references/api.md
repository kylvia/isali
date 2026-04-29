# Image API 配置

## 默认端点

`gpt-image-2` 通过 liaobots 的 OpenAI 兼容接口：

- URL: `https://ai.liaobots.work/v1/chat/completions`
- Model name: `gpt-image-2`
- Auth: Bearer token

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

**注意**：不同端点的请求/响应格式可能不同。当前 `generate.py` 假设 OpenAI chat/completions 兼容接口（返回 data URI 嵌在 `choices[0].message.content` 里）。

如果要支持标准 `/v1/images/generations`，需扩展 `generate.py` 的响应解析分支。

## 性能

单次生成耗时约 **22-60 秒**（受内容复杂度影响）：
- 简单图形 ~22s
- 含大量文字/布局 ~45-55s

## 尺寸

通过 prompt 描述 aspect ratio（如 "2.35:1"），模型会尽量匹配。实际输出常见：
- 1254×533（约 2.35:1）
- 1536×1024（3:2）
- 1024×1024（1:1，默认）

## 失败排查

- 超时：默认 180s，复杂图可能触发；调大 timeout
- 返回无图：打印 content head 检查是否是文本回复（prompt 偏移）
- 格式不认：确认 `data:image/...;base64,` 前缀存在
