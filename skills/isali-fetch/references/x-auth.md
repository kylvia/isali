# X/Twitter 认证配置

## 为什么需要

X 对未登录用户限制严格：
- 视频无法播放
- 部分推文内容隐藏
- 某些用户的主页直接 403

要完整抓取，需 `auth_token` + `ct0` 两个 cookie。

## 获取方式

1. 浏览器登录 `x.com`
2. 打开 DevTools → Application → Cookies → `https://x.com`
3. 复制 `auth_token` 和 `ct0` 两个值

## 传入方式

### 方式 A：命令行（一次性）

```bash
isali fetch https://x.com/OpenAI/status/xxx \
  --cookie auth_token=your_token \
  --cookie ct0=your_ct0
```

### 方式 B：环境变量（推荐）

```bash
export ISALI_X_AUTH_TOKEN=your_token
export ISALI_X_CT0=your_ct0
```

（当前 `scripts/fetchers.py` 未读 env，TODO）

### 方式 C：Profile（长期）

```yaml
# ~/.isali/profile.yaml
x:
  auth_token: your_token
  ct0: your_ct0
```

（同上，TODO）

## ⚠️ 凭证安全提醒

- `auth_token` 是完整 session 凭证，等同于账号密码
- **不要**写进任何会被 git 追踪的文件
- 用完建议去 X 设置 → Security → Sessions 登出所有会话 rotate 掉
- 推荐开一个**自动化专用小号**跑这类脚本，不要用主号

## 限制

- 即使带 cookie，X 对高频请求仍会限流
- 特定推文可能被作者设为仅关注可见，cookie 账号需已关注
- 不支持批量 timeline 抓取（本 skill 是单 URL 抓取）
