# 标准版功能验收表（standard-feature-acceptance）

> **基线**：`origin/codex/standard-feature-expansion` @ **`222fa02`**（`fix: validate analytics date ranges`）
> 相关提交：`8c0c1bb feat: add task editing roles and learning analytics`（业务实现）、`56b9e55 docs: add standard feature acceptance table and AI offline eval set`（本文档上一版）
> 更新：2026-09-10（DeepSeek 文档验收 Agent）｜ 性质：**只读代码核验 + 引用 Codex 已验证事实**
> 标签：**【事实】**＝可在代码/测试中核验；**【Codex 已验证】**＝Codex 声明的浏览器验证；**【待本人执行】**＝尚需人工执行
>
> **状态词**：`已完成` / `部分完成` / `未完成（计划中）`。**RAG、真实用户调研、原型验证、个人职业发展规划一律保持未完成口径。**

## 1. A1–A7 最终状态

| # | 功能项 | 关联需求 | 最终状态 | 依据【事实】 |
| --- | --- | --- | --- | --- |
| A1 | 任务编辑 | FR-02 | **已完成** | 前端 `data-action="edit"` → `beginTaskEdit()` 回填表单（标题/课程/截止/优先级/备注）→ 提交走 `PATCH /tasks/{id}`；`cancelTaskEdit()` 可取消。后端 PATCH 支持 title/course_id/due_at/priority/note/status，并在状态转 `done` 时写 `completed_at`、转回时清空。测试：`test_task_can_edit_all_fields_and_tracks_completion`。**【Codex 已验证】浏览器已验证任务编辑** |
| A2 | 课程管理 | FR-03 | **已完成**（邀请码加入除外） | `GET /courses/{id}`（含 `task_count`/`material_count`）、`PATCH /courses/{id}`（改名/学期，所有者或管理员）、`DELETE /courses/{id}`（204；**课程仍有任务或资料时返回 409 阻止删除**）。前端"课程详情"面板 `#courseForm`（保存/删除/关闭 + 元信息）。测试：`test_course_details_update_and_safe_delete`。**【Codex 已验证】浏览器已验证课程详情**。`POST /courses/{id}/join`（邀请码）**未完成（计划中）** |
| A3 | 角色权限 | FR-11 | **已完成**（最小实现） | 三角色：注册时账号等于环境变量 `ADMIN_ACCOUNT` 即为 `admin`，否则 `student`；启动时同样把该账号升级为 admin。`GET /users`（仅管理员）、`PATCH /users/{id}/role`（仅管理员，**禁止修改自己的角色** 400，用户不存在 404）；`require_admin`、`require_course_manager`（所有者或管理员）；管理员越权范围受控（如非成员访问课程详情 403、改他人任务 404 而管理员可改）。前端 `#adminPanel` 仅 admin 可见，用户列表可改角色（自身下拉禁用）。测试：`test_admin_role_management_and_cross_user_permissions` |
| A4 | 按课程统计 | FR-10 | **已完成** | `GET /stats/courses`（按课程分组：`course_id/course_name/total/completed/overdue/completion_rate`，非管理员仅本人任务与所属课程），`GET /stats/overview?course_id=` 支持课程过滤（需课程成员）。前端"学习统计"面板课程下拉 + 条形图。测试：`test_course_date_and_overdue_statistics` |
| A5 | 时间统计 | FR-10 | **已完成**（口径：按截止日期） | `GET /stats/overview?from=&to=` 与 `GET /stats/courses?from=&to=`；日期必须是 `YYYY-MM-DD`（否则 422"日期筛选必须使用 YYYY-MM-DD 格式"），`from` 取当日 00:00、`to` 取当日 23:59:59.999999，均按**校园时区 UTC+8** 解释后转 UTC 比较；**开始日期晚于结束日期返回 422，detail 为"开始日期不能晚于结束日期"**（`222fa02` 修复）。前端日期筛选 + 重置。测试同上。**局限【事实】**：过滤字段是 `t.due_at`（截止日期），`completed_at` 已记录但**未参与统计**；"按完成时间的趋势"未实现 |
| A6 | 逾期统计 | FR-10 / FR-09 | **已完成** | `overview` 与 `stats/courses` 均返回 `overdue`（判定：`status != 'done' AND due_at IS NOT NULL AND due_at < 服务器当前时间`）；前端统计卡新增"已逾期"，条形图行显示"逾期 N"。测试断言 `overdue == 1`。**日期语义已修正**：纯日期 `due_at` 归一化为"校园时区（UTC+8）当日 23:59:59.999999"再转 UTC，因此输入"今天"不会再被立即判为逾期。`GET /tasks/upcoming`（7 天内、含 `remaining_hours`/`urgent`）保留为首页"即将截止"区 |
| A7 | 图表展示 | FR-17 | **已完成**（零依赖） | 前端 `renderCourseChart()` 用纯 CSS 条形图（`.chart-row/.chart-track/.chart-bar`，宽度=完成率百分比，文案"完成/总数 · 逾期 N"），**未引入任何图表库**；空数据有占位文案"所选时间段暂无课程任务数据。"。**【Codex 已验证】375px 移动端视口无水平溢出** |

> 状态说明：A1–A7 的"已完成"均指**后端接口 + 测试 + 前端界面**三者齐备；其中浏览器交互结论来自 Codex 的验证声明，本报告未复跑浏览器。

## 2. 自动化与浏览器证据

### 2.1 自动化测试（21 passed，Codex 报告；本报告静态核验用例数一致）

| 文件 | 用例数 | 覆盖 |
| --- | --- | --- |
| `backend/tests/test_api.py` | 15 | 健康检查、认证/课程/任务/统计主闭环、即将截止、重复注册、非法课程名、非法日期归一化、任务不存在、消息落库、provider 地址校验、AI 三类故障安全降级、provider 转发、未登录 401、资料上传/列表/删除、资料格式与大小、资料越权 |
| `backend/tests/test_standard_features.py` | 6 | **任务编辑与 completed_at**、**课程详情/改名/安全删除（409）**、**角色管理与跨用户权限**、**按课程与日期/逾期统计（含 422 日期校验）**、**会话私有性与管理员可审核**、**离线 AI 评估集（mock provider）** |

> 本报告**未执行** `pytest`（需切换环境/装依赖，超出只读范围）；"21 passed" 为 Codex 声明，用例数量与断言内容已逐条静态核验。`node --check frontend/app.js` 与 `git diff --check` 通过亦为 Codex 声明。

### 2.2 浏览器证据（【Codex 已验证】，本报告未复现）

| 验证项 | 结论 | 说明 |
| --- | --- | --- |
| 任务编辑 | 已验证 | 回填→保存→列表更新；完成率随之变化 |
| 完成率更新 | 已验证 | 与 `/stats/overview` 一致 |
| 课程详情 | 已验证 | 详情面板可打开、可保存 |
| 375px 移动端 | 已验证 | 无水平溢出 |

### 2.3 顺带修复的既有缺陷【事实】

- **P0「刷新」缺陷已修**：`$('refreshBtn').onclick = () => loadData();`（旧代码把 MouseEvent 当课程 id，导致下拉清空、建任务 403/上传 422）。
- **422 错误可读化已修**：`request()` 将 `detail` 数组映射为 `item.msg` 并用"；"拼接，不再是 `[object Object]`。
- **资料列表随课程联动**：`loadMaterials(courseId)` 使用当前选中课程；`courseSelect.onchange` 同步资料课程下拉。
- **日期展示友好化**：`formatDate()` 使用 `toLocaleString('zh-CN')`；编辑时 `dateInputValue()` 截取日期部分。

## 3. 待本人执行（不得标记为已完成）

| # | 事项 | 说明 |
| --- | --- | --- |
| P-1 | **完整用户测试** | **待本人执行**：按 A1–A7 逐条走查浏览器（桌面 + 375px），核对编辑/详情/统计/角色联动；本轮未执行 |
| P-2 | **AI 输出人工双人评分** | 见 [ai-offline-eval.md](ai-offline-eval.md)：自动化离线检查已通过，**人工 0–4 分双人评分未执行** |
| P-3 | 真实 API 配置切换 | 用临时凭据在浏览器完成一次真实供应商调用（不得记录 Key）；本轮未执行 |
| P-4 | 真机移动端 | Codex 已验证 375px 视口，真机（iOS/Android）未验证 |

## 4. 仍未完成事项（计划中，不得写成已完成）

| 事项 | 状态 | 说明 |
| --- | --- | --- |
| RAG（FR-12/13/14/15） | **未完成（计划中）** | 无文本解析、切分、embedding、向量检索、引用来源；资料 `parse_status` 恒为 `queued`，前端显示"已保存（解析待接入）" |
| 课程邀请码加入（`POST /courses/{id}/join`） | **未完成（计划中）** | `courses.invite_code` 列未建 |
| AI 任务智能拆解（FR-16） | **未完成（计划中）** | 无 `/tasks/{id}/split`、`/tasks/batch`；`tasks.parent_task_id` 未建 |
| 会话增强 | **未完成（计划中）** | 无 `DELETE /conversations/{id}`、无会话历史切换 UI、LLM 请求不带历史（单轮） |
| 登出接口 | **未完成（计划中）** | 无 `POST /auth/logout`；前端仅清除本地 token |
| 任务详情 `GET /tasks/{id}` | **未完成（计划中）** | 前端编辑使用列表数据回填 |
| 按完成时间的趋势统计 | **未完成（计划中）** | 时间过滤当前基于 `due_at`；`completed_at` 未参与聚合 |
| 教师专属权限 | **未完成（计划中）** | `teacher` 角色已可分配，但除课程所有者外无额外权限分支 |
| 真实用户调研 / 原型验证 | **未执行（计划中）** | 无访谈、无用户测试数据；相关结论仍为待验证假设 |
| 个人职业发展规划 | **未完成（计划中）** | 未实现 |

## 5. 文档与代码不一致项（本轮基线 `222fa02`）

| # | 文档位置 | 文档描述 | 代码现实 | 处理建议 |
| --- | --- | --- | --- | --- |
| G1 | `docs/04-api-spec.md` §2 | 曾列 `POST /auth/logout`、`/courses/{id}/join`、`GET /tasks/{id}`、`split`/`batch`、`/materials/{id}/parse-status`、`DELETE /conversations/{id}`、`/stats/courses/{id}/progress` 等 | 仍未实现（`/stats/courses/{id}/progress` 实际以 `GET /stats/courses` 实现） | 已在 04 中标注"计划中"，并补入已实现端点 |
| G2 | `docs/04-api-spec.md` §1 | 错误结构 `{code,message,details}` | 实现为 FastAPI `detail`（字符串或数组），校验错误 422 | 已在 04 增加"实现差异"说明；前端已可读化 |
| G3 | `docs/04-api-spec.md` §2.5 | 未记录请求体 `provider` 字段 | 已实现（TASK-016） | 已补入 04 |
| G4 | `docs/05-database.md` §2.2 | `courses.invite_code` | 未建列 | 保持"计划中" |
| G5 | `docs/05-database.md` §2.6 | `material_chunks` | 未建表 | 保持"计划中" |
| G6 | `docs/05-database.md` §2.4 | `tasks.parent_task_id / estimate_hours / completed_at` | **`completed_at` 已实现**（含 `ALTER TABLE` 幂等迁移）；另两列未建 | 已在 05 更新 |
| G7 | `docs/05-database.md` §2.8 | `messages.type / course_scope_id / citations` | 未建列 | 保持"计划中" |
| G8 | `docs/06-test-plan.md` | 测试数量、FT-02/03/08/09 期望、ET-01 期望 | 已更新为 21 条与当前实现一致 | 已在 06 更新 |
| G9 | `docs/02-requirements.md` FR-10/11/17 | 原为"规划中"口径 | 已实现（最小实现） | 已在 02 补实现状态与口径说明 |

## 6. 风险与验收建议

| 风险 | 说明 | 缓解 |
| --- | --- | --- |
| R1 管理员发放方式 | 管理员只能由环境变量 `ADMIN_ACCOUNT` 指定（未设置时无人可管理角色） | 演示前设置该变量并注册对应账号；文档写明部署前提 |
| R2 统计口径 | 时间过滤基于 `due_at`，易被理解为"完成时间"；`completed_at` 未参与统计 | 在 02/04 写明口径；如需完成趋势，扩展聚合字段 |
| R3 教师角色空转 | `teacher` 可分配但无专属权限 | 明确其为"预留角色"，或在需求中标注待验证 |
| R4 日期语义 | 已于本分支修正：纯日期 `due_at` = 校园时区当日 23:59:59.999999（转 UTC 存储）；统计 `from/to` 亦按校园时区取边界 | 无需规避；答辩可将其作为"时区口径"亮点说明 |
| R5 未执行的人工项 | P-1~P-4 均未执行，不能声称"用户测试通过" | 答辩口径只引用自动化与 Codex 浏览器验证范围 |

**验收建议**：①在可用环境复跑 `python -m pytest backend/tests -q` 并记录 21 passed 输出；②按 P-1 完成一次完整浏览器走查（含角色切换、日期筛选、移动端）；③按 `ai-offline-eval.md` 完成人工双人评分；④G1~G9 处理后由文档 Agent 复核。

## 7. 事实边界自查

- 所有"已完成"均有代码/测试证据或明确标注为 Codex 已验证；**未执行**的项目（完整用户测试、人工 AI 评分、真实 API 调用、真机）均标注"待本人执行"。
- RAG、资料解析、邀请码加入、AI 拆解、真实用户调研、原型验证、职业规划**均为未完成/计划中**，未写入任何"已实现"表述。
- 本报告未修改 `backend/`、`frontend/`、`README.md`、`tests/`、`tasks/`。
