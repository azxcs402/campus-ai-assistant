# 标准版功能验收表（standard-feature-acceptance）

> 基线：`main` @ `5907417`（含 `15 passed` 测试、资料上传/列表、AI 供应商切换）
> 编制：DeepSeek 文档审查 Agent ｜ 日期：2026-09-09 ｜ 性质：**只读代码核验 + 验收标准设计**，未修改 `backend/`、`frontend/`、`README.md` 与测试代码
> 标签：**【事实】**＝可在代码中核验；**【建议】**＝验收/实现建议；**【差距】**＝文档与代码不一致
>
> **状态词（全文统一）**：`已完成` / `部分完成` / `未完成（计划中）`。**未实现的功能一律标记为"未完成（计划中）"，不得表述为已实现。**

## 1. 状态总览

| # | 功能项 | 关联需求 | 状态 | 一句话依据【事实】 |
| --- | --- | --- | --- | --- |
| A1 | 任务编辑 | FR-02 | **未完成（计划中）** | 后端 `PATCH /api/v1/tasks/{id}` 支持改 title/due_at/priority/note/status；前端任务卡片只有"完成/恢复"（`data-status`）与"删除"（`data-delete`），**无编辑入口** |
| A2 | 课程管理 | FR-03 | **部分完成** | 后端仅 `GET /courses`、`POST /courses`；前端有"新建课程"（`#createCourseBtn`）与两处课程下拉；无改名/删除/详情/加入 |
| A3 | 角色权限 | FR-11 | **未完成（计划中）** | `users.role` 仅建表默认 `student` 并在 `/auth/me` 回显；**无任何按角色的鉴权分支**，无 `/users`、`/users/{id}/role`，注册恒为 student |
| A4 | 按课程统计 | FR-10 | **未完成（计划中）** | `GET /stats/overview` 只返回 `total / completed / completion_rate`（当前用户全量）；无 `course_id` 维度，无 `/stats/courses/{id}/progress` |
| A5 | 时间统计 | FR-10 | **未完成（计划中）** | 统计接口无 `from/to` 等时间参数（函数签名仅 `user`），无按周/月趋势；前端统计区为 3 个数字卡 |
| A6 | 逾期统计 | FR-10 / FR-09 | **未完成（计划中）** | 统计响应无 `overdue`；`tasks` 表**无 `completed_at`**，无法计算"逾期完成"；`GET /tasks/upcoming` 仅返回 7 天内未完成任务（含 `remaining_hours`、`urgent`），是最小近似而非逾期统计 |
| A7 | 图表展示 | FR-17 | **未完成（计划中）** | 前端 `app.js` / `index.html` **无 chart/canvas/SVG 图表代码**，无图表库依赖；统计仅文本数字 |

> 一致性提示：`docs/00-project-overview.md` 将上述能力列入"标准版/特色版"范围，属**计划**表述；`docs/02-requirements.md` 已按版本分层；`docs/04-api-spec.md` 草案中包含的对应端点**多数尚未实现**（见第 4 节）。

## 2. 逐项验收表

> 验收方式：**自动化**＝可写成 `pytest` 接口用例；**人工**＝需浏览器/人工判断。所有"当前结果"列在未实现时写"未完成"，**不伪造通过结果**。

### A1 任务编辑界面

| 项目 | 内容 |
| --- | --- |
| 验收标准（建议细化 FR-02 / AC-02-2） | ①任务卡片提供"编辑"入口；②可修改标题、截止时间、优先级、备注；③保存后列表与统计即时反映；④非法输入（空标题/非法日期）给出可读提示且不落库；⑤并发/重复提交不产生重复数据 |
| 当前结果【事实】 | **未完成（计划中）**：前端无编辑入口；仅 API 支持 `PATCH`（`backend/app.py` 任务 PATCH 分支）；备注字段 API 接受但 UI 无录入 |
| 代码证据 | `frontend/app.js`：任务操作按钮仅 `data-status`、`data-delete`；`frontend/index.html` 任务列表容器 `#taskList` 无编辑表单 |
| 验收方式 | 自动化：`PATCH /tasks/{id}` 改各字段 → 校验响应与列表；人工：点击编辑→保存→列表/统计更新 |
| 阻塞项 | 无（后端已具备，属前端工作量） |
| 建议最小实现【建议】 | 复用创建表单做行内编辑或弹窗；前端调用现有 `PATCH`；补 1 条自动化用例（编辑后 `GET /tasks` 一致） |
| 通过判据 | 上述 5 条全部满足且自动化用例通过 |

### A2 课程管理

| 项目 | 内容 |
| --- | --- |
| 验收标准（建议细化 FR-03） | ①创建课程（名称必填、长度受限）；②列出我的课程；③重命名课程；④删除课程并明确其任务/资料的级联或阻止策略；⑤（如保留 join 设计）通过邀请码加入 |
| 当前结果【事实】 | **部分完成**：①✅ `POST /courses`（name 1–100 字符，空名/超长 422，已有自动化用例）；②✅ `GET /courses`（含 `task_count`）；③④⑤**未完成（计划中）** |
| 代码证据 | `backend/app.py`：仅 `@app.get("/api/v1/courses")`、`@app.post("/api/v1/courses")`；无 `GET/PATCH/DELETE /courses/{id}`、无 `POST /courses/{id}/join`；`courses` 表**无 `invite_code` 列**（对照 `docs/05-database.md` §2.2 草案） |
| 验收方式 | 自动化：创建/列表已覆盖；重命名、删除级联需新增用例；人工：前端入口与反馈 |
| 阻塞项 | 删除策略需先定稿（阻止删除 vs 级联删除），避免产生孤儿任务/资料（当前 `tasks.course_id`、`materials.course_id` 均为 `ON DELETE CASCADE`，**若直接加 DELETE 会连带删除任务与资料，须先确认是否符合预期**） |
| 建议最小实现【建议】 | 先做 `PATCH /courses/{id}`（重命名）+ 前端入口；删除功能需人工确认策略后再实现 |
| 通过判据 | ①–④ 达成；删除策略在 `docs/05-database.md` 中写明并与代码一致 |

### A3 角色权限

| 项目 | 内容 |
| --- | --- |
| 验收标准（建议细化 FR-11 / AC-11-1~4） | ①存在 student/teacher/admin 三种角色；②服务端按角色与资源归属强制鉴权（非前端隐藏）；③管理员可管理用户与角色；④越权访问返回 403/404 且不泄露资源存在性 |
| 当前结果【事实】 | **未完成（计划中）**：`users.role` 列存在（默认 `student`）并在 `/auth/me` 返回；注册接口不接受角色参数；所有受保护接口的依赖只有 `current_user`（仅校验登录态），**无角色判断**；无用户管理端点；前端无角色相关 UI |
| 代码证据 | `backend/app.py`：`role TEXT NOT NULL DEFAULT 'student'`；`public_user()` 返回 role；`POST /auth/register` 未设置 role；各接口 `Depends(current_user)` |
| 验收方式 | 自动化：三角色矩阵用例（现有 `test_protected_endpoint_requires_login` 只覆盖"未登录"）；人工：前端按角色隐藏/显示 |
| 阻塞项 | **需求依据不足**：真实用户调研与原型验证暂不执行，教师/管理员场景缺少验证（属待验证假设）。建议先做最小权限骨架并标注假设，避免投入大量实现后被证伪 |
| 建议最小实现【建议】 | 后端加 `require_role(*roles)` 依赖并在管理类端点使用；注册仅 student；提供管理端最小用户列表/改角色端点；补权限矩阵自动化用例 |
| 通过判据 | 权限矩阵用例全部通过；越权返回 403/404；文档（02/04/05）与实现一致 |

### A4 按课程统计

| 项目 | 内容 |
| --- | --- |
| 验收标准（建议细化 FR-10 / AC-10-1~3） | ①按课程返回任务总数/已完成/完成率；②无任务课程显示 0% 或"—"；③口径（是否含逾期）在文档中写明并与实现一致 |
| 当前结果【事实】 | **未完成（计划中）**：`GET /stats/overview` 只看 `created_by = 当前用户`，无课程维度 |
| 代码证据 | `backend/app.py` `stats()`：`SELECT COUNT(*) AS total, SUM(status='done') AS completed FROM tasks WHERE created_by = ?` → `{total, completed, completion_rate}` |
| 验收方式 | 自动化：造 2 门课多状态任务 → 断言各课程完成率；人工：前端按课程展示 |
| 阻塞项 | 需先定义完成率口径（是否计入逾期未完成） |
| 建议最小实现【建议】 | 新增 `GET /stats/courses/{course_id}/progress`（成员校验）或让 `/stats/overview` 返回 `by_course[]` |
| 通过判据 | 各课程统计与数据库一致；空课程有明确显示；口径写入 `docs/02-requirements.md` |

### A5 时间统计

| 项目 | 内容 |
| --- | --- |
| 验收标准（建议细化 FR-10） | ①支持按时间范围（如本周/本月/自定义 from-to）统计；②返回趋势序列（按天/周）；③时间口径以服务器时间为准（AC-09-2 已确立） |
| 当前结果【事实】 | **未完成（计划中）**：统计接口无时间参数；`tasks` 表只有 `created_at`、`updated_at`（字符串 UTC ISO），无 `completed_at`，因此**无法按完成时间做趋势** |
| 代码证据 | `stats()` 签名 `def stats(user: sqlite3.Row = Depends(current_user))`；`tasks` 建表语句无 `completed_at` |
| 验收方式 | 自动化：给定 from/to 断言过滤与趋势；人工：切换时间范围查看数字/图表变化 |
| 阻塞项 | 需先补 `completed_at`（或按 `updated_at` 近似，但需在文档说明局限） |
| 建议最小实现【建议】 | 1) 迁移加 `completed_at`（PATCH 置 `done` 时写入）；2) `GET /stats/overview?from=&to=` 返回 `trend[]` |
| 通过判据 | 时间过滤正确；趋势与数据一致；局限在文档标注 |

### A6 逾期统计

| 项目 | 内容 |
| --- | --- |
| 验收标准（建议细化 FR-10 / FR-09） | ①统计返回逾期未完成数量；②（可选）逾期完成数量与逾期率；③逾期判定基于服务器时间；④即将截止面板与逾期口径不冲突 |
| 当前结果【事实】 | **未完成（计划中）**：无 `overdue` 字段；现有近似为 `GET /tasks/upcoming`（7 天内、未完成、按 `due_at` 升序，带 `remaining_hours`、`urgent = remaining_hours <= 24`；前端 `#upcomingList` 渲染，逾期显示"已逾期"） |
| 代码证据 | `backend/app.py` `upcoming_tasks()`；`frontend/app.js` `renderUpcoming()` |
| 验收方式 | 自动化：造已逾期任务 → 断言统计计数与 upcoming 文案；人工：观察首页"即将截止"区 |
| 阻塞项 | 需统一"逾期"定义（`due_at` 已过且状态非 done）与日期语义（纯日期按 00:00 UTC 归一化，**UTC+8 下"今天"会被判为已逾期**，见 `docs/final-review.md` P1-3） |
| 通过判据 | 逾期计数与手工核对一致；日期语义在文档中写明并演示不产生歧义 |

### A7 图表展示

| 项目 | 内容 |
| --- | --- |
| 验收标准（建议细化 FR-17 / AC-17-1~3） | ①以图表呈现统计（如课程完成率对比、完成趋势）；②数据与统计接口一致；③空数据有占位说明；④适配桌面与手机屏幕 |
| 当前结果【事实】 | **未完成（计划中）**：前端无任何图表代码（无 `canvas`/`chart`/SVG 绘图），无图表依赖 |
| 代码证据 | `frontend/app.js`、`frontend/index.html` 中 `chart`/`canvas` 命中数为 0；`frontend/styles.css` 只有统计卡样式 |
| 验收方式 | 人工（视觉与响应式）；数据一致性可自动化断言接口 |
| 阻塞项 | **依赖约束**：`AGENTS.md` 要求不引入不必要依赖；若用图表库需人工批准（可先用手写 SVG/纯 CSS 柱状图） |
| 建议最小实现【建议】 | 用纯 CSS/SVG 画课程完成率条形图 + 每周完成数柱状图，零新增依赖 |
| 通过判据 | 图表数值与接口一致；空状态有提示；手机宽度不溢出 |

## 3. 验收执行顺序建议【建议】

1. **前置修复（P0）**：`frontend/app.js` 中 `$('refreshBtn').onclick = loadData;` 与 `loadData(selectedCourseId = null)` 组合会导致点击「刷新」被当作传入课程 id → 下拉清空 → 后续建任务 403/上传 422（详见 `docs/error-boundary-test-report.md` 第 8 节）。修一行后再做验收，避免误判其它功能。
2. **数据模型补齐**：`completed_at`（逾期/时间统计必需）、`courses.invite_code`（若保留 join 设计）。
3. **按依赖顺序实现**：A6（逾期）→ A4/A5（统计）→ A7（图表）依赖前两者的数据；A2（课程重命名）独立；A3（角色）依赖需求确认。
4. **每项完成即补自动化用例**，并回填本文档"当前结果"列（由实现 Agent 更新，文档 Agent 复核）。

## 4. 文档与代码不一致项【差距】

| # | 文档位置 | 文档描述 | 代码现实 | 建议处理 |
| --- | --- | --- | --- | --- |
| G1 | `docs/04-api-spec.md` 接口表 | 列出 `POST /auth/logout`、`GET/PATCH/DELETE /courses/{id}`、`POST /courses/{id}/join`、`GET /tasks/{id}`、`POST /tasks/{id}/split`、`POST /tasks/batch`、`GET /materials/{id}/parse-status`、`DELETE /conversations/{id}`、`GET /stats/courses/{id}/progress`、`GET /users`、`PATCH /users/{id}/role` | **均未实现**（实际 19 个端点，见第 1 节依据） | 在 04 中为未实现端点加"计划中"标记，或拆分为"已实现清单 / 计划清单" |
| G2 | `docs/04-api-spec.md` §1 | 统一错误结构 `{code, message, details}`；400 + 逐字段提示 | 实现为 FastAPI 默认 `detail`（字符串或数组），校验错误为 **422**；无 `code`/`details` 字段 | 二者取一：改实现或改文档（并同步 `docs/06-test-plan.md` ET-01） |
| G3 | `docs/04-api-spec.md` §2.5 | `POST /conversations/{id}/messages` 带 `type=chat|rag` 与 `citations` | 实现无 `type`/`citations`；取而代之的是请求体可选 `provider`（TASK-016），**该字段在 04 中未记录** | 04 增补 `provider` 字段（含 `name/base_url/model/api_key`）与校验规则，并标注 rag 属计划中 |
| G4 | `docs/05-database.md` §2.2 | `courses.invite_code`（加入课程邀请码） | 表无此列 | 若保留 join 设计则迁移加列；否则从 05 移除并同步 04、02 |
| G5 | `docs/05-database.md` §2.6 | `material_chunks`（RAG 切分单元） | **未建表** | 标注"计划中（RAG 未实现）" |
| G6 | `docs/05-database.md` §2.4 | `tasks.parent_task_id / estimate_hours / completed_at` | 三列**均不存在** | `completed_at` 建议尽快补（A5/A6 依赖）；其余标注计划中 |
| G7 | `docs/05-database.md` §2.8 | `messages.type / course_scope_id / citations` | 三列**均不存在** | 标注计划中（RAG/AI 拆解相关） |
| G8 | `docs/06-test-plan.md` FT-01 | 期望"登出" | 无 logout 端点（前端仅删本地 token） | 标记计划中或调整用例 |
| G9 | `docs/06-test-plan.md` FT-05 | 期望资料解析状态流转到 `ready` | `parse_status` **恒为 `queued`**，无解析实现 | 改为"仅存储"口径（前端已显示"已保存（解析待接入）"） |
| G10 | `docs/06-test-plan.md` FT-07 | 期望"造 1 小时后截止任务 → 查看首页提醒" | `#upcomingList` 存在且带 `urgent`（≤24h）样式，"提醒区"已具备最小形态，但**无推送/通知** | 细化用例：面板断言自动化、推送标注计划中 |
| G11 | `docs/06-test-plan.md` FT-08 / FT-09 / FT-10 | 统计图表、三角色矩阵、AI 拆解 | 均未实现 | 标注计划中（与第 1 节状态一致） |
| G12 | `docs/06-test-plan.md` §4 AT-01~AT-06 | RAG 输出验证（引用命中、拒答等） | RAG 未实现，**无对应可测对象** | 明确标注"未执行（计划中）"，或迁至 RAG 立项后启用 |
| G13 | `docs/02-requirements.md` FR-05 AC-05-3 | "上传进度可感知" | 实现只有按钮禁用态 + "处理中…"文案，无进度百分比 | 降级为"提交态可见"，或实现进度事件 |
| G14 | `docs/03-architecture.md` §2/§3.5 | 架构图含向量库、`material_chunks`、异步解析管线 | 均未实现（`parse_status` 无异步任务） | 在 03 中标注"计划中（特色版）" |
| G15 | `docs/00-project-overview.md` §3.2 | 标准版/特色版能力清单 | 多为计划 | 保持"计划"措辞，答辩口径以 `docs/final-review.md` 为准 |

> 已实现但文档未记录（反向差异）：`GET /tasks/upcoming` 的 `remaining_hours`/`urgent` 字段、`POST /conversations/{id}/messages` 的 `provider` 字段、资料的"已保存（解析待接入）"文案。建议一并补入 04/05。

## 5. 风险与验收建议

| 风险 | 说明 | 缓解 |
| --- | --- | --- |
| R1 P0 刷新缺陷未修 | 点「刷新」后核心流程失败，验收时易误判为其它功能不可用 | 验收前先修（一行）并回归 |
| R2 数据模型缺口 | 无 `completed_at` → 逾期/时间统计无法准确实现 | 先做迁移再实现统计 |
| R3 需求依据不足 | 角色权限（教师/管理员）缺少用户验证（真实调研暂不执行） | 最小实现 + 文档标注"待验证假设"；避免过度投入 |
| R4 依赖约束 | 图表若引入库违反"不引入不必要依赖" | 优先零依赖 SVG/CSS 方案；如需库须人工批准 |
| R5 文档-代码漂移 | 第 4 节 15 项差异，答辩引用易出错 | 按 G1~G15 逐项修正，由文档 Agent 复核后关闭 |
| R6 口径风险 | 把"计划中"功能讲成已实现 | 答辩统一引用 `docs/final-review.md` §2 与本文档状态列 |

**验收建议**：
1. 先执行"自动化验收"：现有 15 条测试 + 每项功能新增用例（A1 编辑、A2 重命名、A3 权限矩阵、A4 按课程、A5 时间、A6 逾期）；全部通过后记录命令与输出。
2. 再执行"人工验收"：按 A1~A7 的验收标准逐条走查浏览器（含移动端宽度），并把结果回填本文档（未执行前保持"未完成"）。
3. 文档同步：G1~G15 处理完后，由文档 Agent 复核 `02/04/05/06/03/00` 与代码一致性。

## 6. 事实与假设边界（自查）

- 本文档所有"当前结果"均基于 `main` @ `5907417` 的代码核验（后端 19 个端点、15 条测试、前端标记命中数），**未运行服务、未做浏览器验收、未执行新增测试**。
- 未实现功能一律标注"未完成（计划中）"；未虚构任何测试/评估/用户调研结果。
- 验收标准中标注【建议】的条目为文档 Agent 提议，需人工确认后写入 `docs/02-requirements.md`。
