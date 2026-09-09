# tasks/done · 已完成

存放**通过复核、完成标准全部满足**的任务文件。

## 使用规则

1. 任务移入本目录时，「当前状态」改为 `done`，并保留完成日期与提交号；
2. 归档任务文件**只读**：如需再次修改，复制为新的 `TASK-XXX` 任务并说明与旧任务的关系；
3. 交付物链接保持有效（文档/代码/测试结果）；若相关文档后续变更，在任务文件注明"已由 XX 任务更新"；
4. 本目录是项目进展的可审计记录，供汇报与复盘使用。

## 已完成任务

| 编号 | 任务 | 完成日期 | 交付物 |
| --- | --- | --- | --- |
| [TASK-007-mvp-review.md](TASK-007-mvp-review.md) | MVP 用户体验与设计思维审查 | 2026-09-09 | `docs/mvp-review.md`、`docs/demo-user-test.md` |
| [TASK-008-rag-plan.md](TASK-008-rag-plan.md) | 两天 RAG 方案与演示数据 | 2026-09-09 | `docs/rag-plan.md`、`docs/rag-demo-dataset.md` |
| [TASK-009-demo-materials.md](TASK-009-demo-materials.md) | 课程答辩与演示材料 | 2026-09-09 | `docs/presentation-outline.md`、`docs/demo-script.md`、`docs/project-contribution.md` |

> 注：上述任务完成于 `deepseek/mvp-review` 分支；提交号见 `docs/vibe-log/` 整合日志（推送完成后可在任务文件补记）。
