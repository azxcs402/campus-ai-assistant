# 2026-09-10 · 标准功能最终验收（standard feature final review）

- **执行者**：DeepSeek 文档验收 Agent
- **分支**：`deepseek/standard-feature-final-review`（基于 `origin/codex/standard-feature-expansion`）
- **基线**：**`222fa02 fix: validate analytics date ranges`**（分支尖端）；相关提交：`56b9e55 docs: add standard feature acceptance table and AI offline eval set`（文档基线）、`8c0c1bb feat: add task editing roles and learning analytics`（业务实现）
- **性质**：只读代码核查 + 文档更新。**未修改** `README.md`、`backend/`、`frontend/`、`tests/`、`tasks/`。

## 核查到的事实（代码/测试级）

1. **测试**：`backend/tests/test_api.py` 15 条 + `backend/tests/test_standard_features.py` 6 条 = **21 条**（与 Codex 报告一致）。
2. **新增端点（相对上一基线）**：`GET/PATCH/DELETE /courses/{id}`、`GET /users`、`PATCH /users/{id}/role`、`GET /stats/courses`；`/stats/overview` 增加 `course_id`/`from`/`to` 与 `overdue`/`server_time`。
3. **数据模型**：`tasks.completed_at` 已实现（启动时幂等 `ALTER TABLE`），`PATCH` 状态转 `done` 写入、转回清空；`parent_task_id`/`estimate_hours`/`invite_code`/`material_chunks`/`messages.type` 等仍**未实现**。
4. **角色**：管理员由环境变量 `ADMIN_ACCOUNT` 指定；`require_admin`/`require_course_manager`（课程所有者或管理员）；管理员不能修改自己的角色；`teacher` 角色可分配但无专属权限。
5. **统计口径**：日期筛选字段为 `due_at`（不是 `completed_at`）；`YYYY-MM-DD` 必填，`from` 取当日 00:00、`to` 取当日 23:59:59.999999，按**校园时区 UTC+8** 解释后转 UTC；非法日期或 `from > to` → 422。`overdue` = 未完成且 `due_at < 服务器当前时间`。
6. **日期语义修正**：纯日期 `due_at` 归一化为**校园时区当日 23:59:59.999999**，此前"输入今天即判逾期"的问题已消除。
7. **前端**：任务编辑（编辑/取消）、课程详情面板（改名/删除/元信息）、管理员用户角色面板、学习统计面板（课程筛选 + 日期筛选 + 零依赖 CSS 条形图）；`request()` 已把 422 的 `detail` 数组转为可读文本；`$('refreshBtn').onclick = () => loadData();` 已修复此前的"刷新清空下拉"缺陷。
8. **离线 AI 评估**：`backend/offline_eval.py` 6 条样例 + `score_output()`，由 `test_offline_ai_evaluation_set_uses_mock_provider_and_persists` 以 **mock provider** 驱动（无外网、无真实 Key，测试桩文本），并断言消息落库。

> 以上均为静态核验；**本 Agent 未复跑 pytest、未做浏览器验收**。Codex 报告：21 passed、`node --check frontend/app.js` 通过、`git diff --check` 通过、浏览器已验证任务编辑/完成率/课程详情、375px 无水平溢出。

## 本轮文档改动

| 文件 | 改动 |
| --- | --- |
| `docs/standard-feature-acceptance.md` | 基线更新为 `222fa02`；A1–A7 重新核验：A1 任务编辑、A2 课程管理、A3 角色权限（最小）、A4 按课程统计、A5 时间统计、A6 逾期统计、A7 图表展示**均改为已完成**（附代码/测试/Codex 浏览器证据）；"完整用户测试"标注**待本人执行**；未完成项清单与不一致项（G1–G9）更新 |
| `docs/ai-offline-eval.md` | 记录 `backend/offline_eval.py` 6 条样例（E-01~E-06）与 `score_output()` 字段；记录测试 `test_offline_ai_evaluation_set_uses_mock_provider_and_persists`；明确 **mock provider / 无外网 / 无真实 API Key / 测试桩文本**；区分"自动化离线检查已通过"与"人工双人评分未执行" |
| `docs/02-requirements.md` | 版本表状态更新；FR-02/03/10/11/17 补实现状态与口径（含 `ADMIN_ACCOUNT`、`completed_at`、统计按 `due_at`、422 日期校验）；标准版补测试数量 21 条 |
| `docs/04-api-spec.md` | 新增 §1.1 实现差异说明；§2.1/2.2/2.3/2.4/2.5/2.6 逐个端点标注**已实现/计划中**并补参数与权限口径；新增 §3.8 `/stats/courses` 示例并修正 §3.7 响应字段；§4 更新实现状态与测试数量 |
| `docs/05-database.md` | `users.role` 实现说明；`courses.invite_code`、`tasks.parent_task_id/estimate_hours`、`material_chunks`、`messages.type/course_scope_id/citations` 标注**计划中**；`tasks.completed_at`/`due_at` 标注已实现与日期语义；§4 决策项改为"决策项与实现现状"表 |
| `docs/06-test-plan.md` | 头部补 21 条（15+6）与执行来源；FT-01~FT-10、ET-01~ET-09 标注实现/自动化状态与口径修正；新增 §2.1 标准版 6 条自动化用例清单；§4 增 §4.3 当前可执行离线检查并声明 AT-01~06 未执行；§5 用户体验测试标注**未执行（待本人执行）** |
| `docs/vibe-log/README.md` | 追加本日志索引 |

## 仍未完成（计划中，未写入任何"已完成"表述）

RAG（FR-12~15）与资料解析；课程邀请码加入；AI 任务拆解（FR-16）；`/auth/logout`；`GET /tasks/{id}`；`DELETE /conversations/{id}` 与会话历史切换；真实多轮上下文；按完成时间（`completed_at`）的趋势统计；教师专属权限；分页与统一错误结构；429 限流；**真实用户调研、原型验证、个人职业发展规划均未实现/未执行**；AI 人工双人评分与完整用户测试**待本人执行**。

## 遗留

- 建议在可用环境复跑 `python -m pytest backend/tests -q` 并留档 21 passed 输出（本 Agent 未执行）。
- `ADMIN_ACCOUNT` 需在演示前设置，否则无管理员可用。
- 真机移动端（375px 仅浏览器视口验证）与真实 API 配置切换（不得记录 Key）仍待人工执行。
