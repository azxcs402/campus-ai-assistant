# tasks/inbox · 待办任务（Backlog）

存放**已拆分、待执行**的任务文件。

## 使用规则（详见 [AGENTS.md](../../AGENTS.md) 第 4 节）

1. 任务文件必须包含：任务目标、背景和上下文、需要修改的文件、不允许修改的范围、完成标准、测试方法、交付物、当前状态；
2. 初始状态统一为 `ready`；
3. 开始执行时：把任务文件移动到 `tasks/doing/`，并将状态改为 `doing`；
4. 编号体系：`TASK-XXX-短名.md`，编号全局唯一、一经使用不回收；
5. 不要在 inbox 中直接改写已完成任务；历史任务从 `tasks/done/` 查找。

## 当前任务

| 编号 | 任务 | 状态 |
| --- | --- | --- |
| [TASK-001-user-research.md](TASK-001-user-research.md) | 用户调研：验证设计思维假设 | ready |
| [TASK-002-requirements.md](TASK-002-requirements.md) | 需求定稿与验收标准 | ready |
| [TASK-003-system-architecture.md](TASK-003-system-architecture.md) | 系统架构与技术选型 | ready |
| [TASK-004-database-design.md](TASK-004-database-design.md) | 数据库设计落地 | ready |
| [TASK-005-api-design.md](TASK-005-api-design.md) | API 设计定稿 | ready |
| [TASK-006-prototype-validation.md](TASK-006-prototype-validation.md) | 原型验证 | ready |
