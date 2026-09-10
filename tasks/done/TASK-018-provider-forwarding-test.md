# TASK-018 API 配置转发验证

- 状态：done
- 负责 Agent：Codex
- 范围：验证网页配置的 provider 被后端正确用于 OpenAI 兼容请求

## 完成标准

- 使用本地模拟 HTTP 接口，不访问外网。
- 验证自定义 Base URL 和模型名称被发送。
- 验证 API Key 被放入 Authorization 请求头。
- 验证返回的模型回答可以进入对话接口。

## 实际结果

- 使用 pytest monkeypatch 模拟 OpenAI 兼容接口，不访问外网。
- 验证 Base URL、模型名称、Authorization 请求头和 25 秒超时参数。
- 模拟接口返回内容可被 `assistant_reply` 正确解析。
- 完整测试结果：`15 passed`。
