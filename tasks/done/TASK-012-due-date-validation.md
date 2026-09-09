# TASK-012 截止日期校验

- 状态：done
- 负责 Agent：Codex
- 来源：DeepSeek 最终评审 C-5

## 完成标准

- 创建和更新任务时拒绝非法 `due_at`。
- 接受前端日期控件产生的 `YYYY-MM-DD` 以及 ISO datetime。
- 无时区输入按 UTC 解释并标准化，避免提醒接口比较异常。
- 有回归测试覆盖创建和更新。

## 实际结果

- `TaskIn` 和 `TaskPatch` 统一校验并标准化 `due_at`。
- 支持 `YYYY-MM-DD`、ISO datetime 和 `Z` 时区格式。
- 无时区输入按 UTC 处理。
- 新增非法日期、日期标准化和更新场景测试。
