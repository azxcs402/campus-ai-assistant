# 2026-09-09 · Final Review（最终评审与交付文档）

- **执行者**：DeepSeek Harness（文档/评审 Agent）
- **分支**：`deepseek/final-review`（基于 `origin/codex/integration` @ `a39a6e2`，并合并了 `deepseek/mvp-review` 的评审文档）
- **性质**：纯文档轮。只新增/修改 `docs/`；未修改 `backend/`、`frontend/`、`README.md`、`.env*`、git 配置及任何课程原始文件。

## 本轮工作

1. 同步远端引用（本地 `origin/codex/integration` 已含 Codex 新提交 `a39a6e2 feat: add course material management`；评审期间 GitHub 网络不可达，多次 fetch/pip 超时——测试未重跑，仅引用 Codex 日志声明）。
2. 通读最新代码（`backend/app.py` 18 个端点、`backend/tests/*` 5 条用例、`frontend/*`、根脚本、`.env.example`、README）与既有文档，建立"已实现/部分实现/未实现"事实基线。
3. 产出三份最终交付文档：
   - `docs/final-review.md`：功能总览、代码↔文档一致性核验、P0/P1/P2 问题清单（含复现/影响/建议，标注事实·推断·建议）、Codex 下一步任务 C-1~C-7。
   - `docs/final-demo-checklist.md`：5 分钟演示流程（含注册登录/课程/任务/即将到期/资料上传查看/AI/统计），逐步预期结果与失败备用方案。
   - `docs/final-rag-decision.md`：不建议周五前实现真向量 RAG 的决策、必要条件与缺失项、不可伪造 RAG 的理由、R0 降级方案、答辩话术。
4. 为 5 份基于更早代码的文档（mvp-review / rag-plan / project-contribution / demo-script / presentation-outline）加入顶部"final-review 更新注记"，澄清 FR-04/05 状态变化并指向最终文档。

## 关键结论

1. **基础版门槛已全部满足**：`a39a6e2` 补上课程资料列表/上传后，mvp-review 的 R-1（FR-04 未实现）已失效。
2. **最高优先级问题（P0）**：①资料 `parse_status` 恒 `queued` 且无解析管线，UI 存在误导（P0-1）；②前端 422/校验错误不可读（`[object Object]`、多处静默失败，P0-2）；③RAG 未实现的口径红线（P0-3）。
3. **RAG 决策**：无 embedding 服务实测/配置（DeepSeek Chat API 不提供 embedding 的假设不可成立）→ 不建议周五前实现向量 RAG；可选"关键词检索降级版（R0）"，且必须如实命名；禁止假装已实现。
4. 测试声明边界：5 passed 来自 Codex 日志；本评审因网络不可用未重跑，已在 final-review 文首标注，并建议答辩前联网执行 `pytest` 留档。

## 一致性自查

- [x] 变更仅限 `docs/`（新增 3 份最终文档 + 1 份日志 + 5 份更新注记 + README 索引）
- [x] 事实表述全部以 `a39a6e2` 代码/文件可核验；推断与建议显式标注
- [x] 未虚构测试结果、访谈或已完成功能；未修改任何代码与受保护文件

## 遗留

- 推送 `deepseek/final-review` 需在具备 TLS/网络的终端执行（本会话网络不可达）；若由其他终端执行，命令：`git push -u origin HEAD:deepseek/final-review`。
- P0/P1 修复（C-1~C-5）待 Codex 按 final-review 第 4 节执行；README 需人工补写。
