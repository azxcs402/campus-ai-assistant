# 04 · API 规格说明（初步草案）

> 文档编号：04 ｜ 状态：草案 v0.1 ｜ 定稿责任：`tasks/inbox/TASK-005-api-design.md`
> 本文件给出**初步** API 列表、参数与返回值约定，供系统设计与前后端并行开发对齐；实现时以 TASK-005 定稿的 OpenAPI 规格为准，本文档随之更新。需求追溯：FR 编号见 [02-requirements.md](02-requirements.md)。
>
> **实现状态（2026-09-10 更新，基线 `codex/standard-feature-expansion` @ `222fa02`）**：已实现 **25 个端点**；本文件中标注 **【计划中】** 的端点尚未实现。详细差异见 §1.1，验收状态见 [standard-feature-acceptance.md](standard-feature-acceptance.md)。

## 1. 通用约定

- 基础路径：`/api/v1`；数据格式：JSON（上传接口为 `multipart/form-data`）；
- 认证：登录后返回访问令牌；受保护接口请求头携带 `Authorization: Bearer <token>`；
- 时间：统一 ISO 8601（含时区或统一 UTC+8 约定，由 TASK-005 定稿）；"即将截止/剩余时间"以后端服务器时间为准（AC-09-2）；
- 分页：列表接口支持 `page`/`page_size`（默认 `1`/`20`），返回 `{ items, total, page, page_size }`；
- 统一错误结构：

```json
{ "code": "VALIDATION_ERROR", "message": "请求参数不合法", "details": [ { "field": "title", "message": "任务名不能为空" } ] }
```

| HTTP 状态码 | 语义 |
| --- | --- |
| 200 / 201 | 成功 / 创建成功 |
| 400 | 参数错误（`code=VALIDATION_ERROR`） |
| 401 | 未认证或令牌失效（`code=UNAUTHORIZED`） |
| 403 | 越权访问（`code=FORBIDDEN`，不泄露资源存在性） |
| 404 | 资源不存在（`code=NOT_FOUND`） |
| 409 | 冲突（如重复提交/重名覆盖需确认，`code=CONFLICT`） |
| 429 | 频率超限（`code=RATE_LIMITED`） |
| 502 / 504 | AI 网关不可用 / 超时（`code=AI_UNAVAILABLE` / `AI_TIMEOUT`，与业务错误区分） |

### 1.1 实现差异说明（2026-09-10，【事实】）

| 草案约定 | 当前实现 | 说明 |
| --- | --- | --- |
| 错误结构 `{code, message, details}`，校验错误 400 | FastAPI 默认 `{"detail": ...}`，**校验错误 422** | 前端 `request()` 已把 `detail` 数组映射为 `item.msg` 并以"；"拼接，用户侧可读；`code`/`details` 结构属**计划中** |
| 列表分页 `{items,total,page,page_size}` | 返回裸数组，**无分页参数** | 属**计划中** |
| AI 故障返回 502/504 | 捕获异常后**返回 201 + 统一文案"AI 服务暂时不可用。请稍后重试…"** | 安全上不泄露上游细节；非 AI 功能不受影响 |
| 课程删除"处理级联策略" | **非空课程返回 409 阻止删除**（"课程仍有任务或资料，请先清理后再删除"）；空课程 204 | 采用"阻止删除"策略 |
| 资料解析状态机（queued→processing→ready/failed） | `parse_status` 恒为 `queued`，前端显示"已保存（解析待接入）" | 解析与 RAG 属**计划中** |
| 时间字段 | `due_at` 采用 ISO 8601；**纯日期按校园时区（UTC+8）当日 23:59:59.999999 归一化后转 UTC** 存储 | 统计 `from/to` 亦按校园时区取边界 |

## 2. 接口总览

> 版本列：基础版接口即可满足「≥ 3 个 HTTP API」的课程要求（实际基础版已超过 10 个）。`🔒` = 需要登录。

### 2.1 认证与用户（FR-01、FR-11）

| 方法 | 路径 | 说明 | 版本 | 权限 |
| --- | --- | --- | --- | --- |
| POST | `/auth/register` | 学生注册（学号/账号+密码+昵称） | 基础 | 公开 |
| POST | `/auth/login` | 登录，返回令牌与用户信息 | 基础 | 公开 |
| POST | `/auth/logout` | 登出，注销令牌 — **【计划中，未实现】**（前端仅清除本地 token） | 基础 | 🔒 |
| GET | `/auth/me` | 当前用户信息与角色 | 基础 | 🔒 |
| GET | `/users` | 用户列表（管理）— **已实现**（仅管理员；返回全部用户 `id/account/nickname/role`，无分页） | 标准 | 🔒 admin（非管理员 403） |
| PATCH | `/users/{id}/role` | 调整用户角色（管理）— **已实现**（`role ∈ student/teacher/admin`，非法值 422；**管理员不能修改自己的角色** 400；用户不存在 404） | 标准 | 🔒 admin（非管理员 403） |

### 2.2 课程（FR-03、FR-11）

| 方法 | 路径 | 说明 | 版本 | 权限 |
| --- | --- | --- | --- | --- |
| GET | `/courses` | 我的课程列表 | 基础 | 🔒 |
| POST | `/courses` | 创建课程 | 基础 | 🔒 student/teacher |
| GET | `/courses/{id}` | 课程详情 — **已实现**（含 `task_count`、`material_count`；非成员 403，管理员可访问） | 基础 | 🔒 成员 |
| PATCH | `/courses/{id}` | 修改课程信息（`name`/`semester`）— **已实现**（仅课程所有者或管理员，其他 403） | 基础 | 🔒 所有者/admin |
| DELETE | `/courses/{id}` | 删除课程 — **已实现**（空课程 204；**仍有任务或资料返回 409**；仅所有者或管理员） | 基础 | 🔒 所有者/admin |
| POST | `/courses/{id}/join` | 通过邀请码/课程号加入 — **【计划中，未实现】**（`courses.invite_code` 列未建） | 基础 | 🔒 student |

### 2.3 学习任务（FR-02、FR-09、FR-16）

| 方法 | 路径 | 说明 | 版本 | 权限 |
| --- | --- | --- | --- | --- |
| GET | `/tasks` | 任务列表（筛 course_id/status/upcoming/截止排序，分页） | 基础 | 🔒 |
| POST | `/tasks` | 创建任务 | 基础 | 🔒 |
| GET | `/tasks/{id}` | 任务详情 — **【计划中，未实现】**（前端编辑使用列表数据回填） | 基础 | 🔒 本人 |
| PATCH | `/tasks/{id}` | 更新任务（含标记完成）— **已实现**：可改 `title`/`course_id`/`due_at`/`priority`/`note`/`status`；转 `done` 写入 `completed_at`，转回清空；非本人且非管理员 404 | 基础 | 🔒 本人/admin |
| DELETE | `/tasks/{id}` | 删除任务 | 基础 | 🔒 本人 |
| GET | `/tasks/upcoming` | 即将截止任务（7 天内、未完成、升序、含 `remaining_hours`/`urgent`） | 基础 | 🔒 |
| POST | `/tasks/{id}/split` | AI 拆解：生成子任务建议（不落库）— **【计划中，未实现】** | 特色 | 🔒 本人 |
| POST | `/tasks/batch` | 批量创建（确认拆解结果后落库，含父子关联）— **【计划中，未实现】**（`parent_task_id` 未建） | 特色 | 🔒 |

### 2.4 资料（FR-04、FR-05、FR-12/13 状态）

| 方法 | 路径 | 说明 | 版本 | 权限 |
| --- | --- | --- | --- | --- |
| GET | `/courses/{course_id}/materials` | 课程资料列表（含解析状态） | 基础 | 🔒 成员 |
| POST | `/materials` | 上传资料（multipart，字段见 3.3）— **已实现**（扩展名白名单、≤20MB、`parse_status='queued'`） | 标准 | 🔒 成员 |
| DELETE | `/materials/{id}` | 删除资料 — **已实现**（**上传者、课程所有者或管理员**可删；其他 404，不泄露存在性；当前无向量索引需清理） | 标准 | 🔒 上传者/课程所有者/admin |
| GET | `/materials/{id}/parse-status` | 解析状态查询（排队/处理/可问答/失败+原因）— **【计划中，未实现】**（无解析管线） | 标准 | 🔒 成员 |

### 2.5 对话与问答（FR-06、FR-07、FR-14、FR-15）

| 方法 | 路径 | 说明 | 版本 | 权限 |
| --- | --- | --- | --- | --- |
| POST | `/conversations` | 新建会话（可指定会话名） | 基础 | 🔒 |
| GET | `/conversations` | 会话历史列表（时间倒序） | 基础 | 🔒 |
| GET | `/conversations/{id}/messages` | 会话消息序列 | 基础 | 🔒 本人 |
| POST | `/conversations/{id}/messages` | 发送消息 — **已实现（普通对话）**：请求体 `{content, provider?}`；`provider` 为用户自定义 API 配置（`name`/`base_url`（须 http(s)）/`model`/`api_key`），缺省时使用环境变量或演示模式；响应为落库后的助手消息。**`type=rag` 与 `citations` 属【计划中，未实现】** | 基础（rag 属特色） | 🔒 本人 |
| DELETE | `/conversations/{id}` | 删除会话 — **【计划中，未实现】** | 基础 | 🔒 本人 |

### 2.6 统计（FR-10、FR-17）

| 方法 | 路径 | 说明 | 版本 | 权限 |
| --- | --- | --- | --- | --- |
| GET | `/stats/overview` | 总任务数/已完成/**逾期**/完成率 — **已实现**：查询参数 `course_id?`（需课程成员）、`from?`/`to?`（`YYYY-MM-DD`，按校园时区取日边界；非法或 from>to → 422）；响应 `{total, completed, overdue, completion_rate, server_time}`；管理员统计全量，其他用户仅本人任务 | 标准 | 🔒 |
| GET | `/stats/courses` | 按课程分组的完成情况 — **已实现**：`from?`/`to?` 同上；返回 `[{course_id, course_name, total, completed, overdue, completion_rate}]`（非管理员仅所属课程） | 标准 | 🔒 |
| GET | `/stats/courses/{course_id}/progress` | 单课程完成率与趋势 — **【计划中，未实现】**（当前以 `GET /stats/courses` 提供分组数据；趋势图未实现） | 标准 | 🔒 成员 |

## 3. 关键接口的请求/返回示例（初步）

### 3.1 登录 `POST /api/v1/auth/login`

```json
// 请求
{ "account": "20240001", "password": "******" }
// 200 返回
{ "token": "eyJhbGciOi...", "user": { "id": 1, "nickname": "小林", "role": "student" } }
// 401 返回（统一提示，不暴露账号是否存在）
{ "code": "UNAUTHORIZED", "message": "账号或密码错误", "details": [] }
```

### 3.2 创建任务 `POST /api/v1/tasks`

```json
// 请求
{
  "title": "操作系统课程设计——进程调度模拟",
  "course_id": 3,
  "due_at": "2026-10-30T23:59:59+08:00",
  "priority": "high",
  "note": "可两人组队",
  "parent_task_id": null
}
// 201 返回
{ "id": 101, "title": "操作系统课程设计——进程调度模拟", "course_id": 3,
  "status": "todo", "due_at": "2026-10-30T23:59:59+08:00",
  "priority": "high", "note": "可两人组队", "created_at": "2026-09-09T19:20:00+08:00" }
// 400 返回
{ "code": "VALIDATION_ERROR", "message": "请求参数不合法",
  "details": [ { "field": "title", "message": "任务名不能为空" },
               { "field": "due_at", "message": "截止时间不能早于当前时间" } ] }
```

### 3.3 上传资料 `POST /api/v1/materials`（multipart/form-data）

| 字段 | 说明 | 约束（初步） |
| --- | --- | --- |
| `file` | 文件二进制 | PDF/PPT/PPTX/DOC/DOCX/TXT；≤ 20MB（上限由 TASK-005 定稿） |
| `course_id` | 归属课程 | 必须为成员 |
| `title`（可选） | 自定义标题 | 缺省用文件名 |

```json
// 201 返回
{ "id": 55, "course_id": 3, "filename": "ch05-scheduling.pdf", "size": 2097152,
  "parse_status": "queued", "created_at": "2026-09-09T19:30:00+08:00" }
// 400（格式不支持）
{ "code": "VALIDATION_ERROR", "message": "不支持的文件类型",
  "details": [ { "field": "file", "message": "仅支持 PDF/PPT/PPTX/DOC/DOCX/TXT" } ] }
```

### 3.4 发送消息（普通对话）`POST /api/v1/conversations/{id}/messages`

```json
// 请求
{ "type": "chat", "content": "帮我解释一下什么是进程调度" }
// 200 返回
{ "id": 501, "role": "assistant", "content": "进程调度是操作系统按某种策略决定……",
  "created_at": "2026-09-09T19:31:00+08:00", "citations": null }
```

### 3.5 课程资料问答（RAG，特色版）`POST /api/v1/conversations/{id}/messages`

```json
// 请求
{ "type": "rag", "content": "老师讲的滑动窗口算法在课件哪里？怎么理解？", "course_id": 3 }
// 200 返回
{ "id": 502, "role": "assistant",
  "content": "在《计算机网络》第 4 章课件第 12 页附近有滑动窗口的讲解……",
  "citations": [
    { "material_id": 55, "filename": "ch05-scheduling.pdf", "source": "ch05-scheduling.pdf",
      "location": "第 4 章 / 第 12 页", "snippet": "滑动窗口：发送方维护一个窗口……" }
  ],
  "created_at": "2026-09-09T19:32:00+08:00" }
// 资料中无相关内容时（不可编造）
{ "id": 503, "role": "assistant",
  "content": "当前课程资料中未找到与“滑动窗口”相关的内容，请尝试换一种问法或上传相关课件。",
  "citations": [], "created_at": "..." }
```

### 3.6 AI 拆解任务 `POST /api/v1/tasks/{id}/split`

```json
// 请求（可带约束）
{ "hint": "课设在第 10 周答辩，第 9 周末需完成初稿", "deadline": "2026-11-20T23:59:59+08:00" }
// 200 返回：建议列表（不落库，确认后再 /tasks/batch）
{ "suggestions": [
    { "title": "阅读任务书并列出功能点", "suggested_due": "2026-09-15", "estimate_hours": 2 },
    { "title": "设计进程调度数据结构",   "suggested_due": "2026-09-20", "estimate_hours": 4 }
  ],
  "editable": true }
// 502（AI 网关不可用）
{ "code": "AI_UNAVAILABLE", "message": "AI 服务暂不可用，请稍后重试或手动创建任务", "details": [] }
```

### 3.7 统计总览 `GET /api/v1/stats/overview?course_id=3&from=2026-09-01&to=2026-09-30`

```json
// 200 返回（当前实现：无 by_course / trend 字段，按课程数据请用 GET /stats/courses）
{ "total": 12, "completed": 7, "overdue": 2, "completion_rate": 0.58,
  "server_time": "2026-09-10T02:15:00+00:00" }
// 422 返回（日期非法或 from > to）
{ "detail": "开始日期不能晚于结束日期" }
```

### 3.8 按课程统计 `GET /api/v1/stats/courses?from=2026-09-01&to=2026-09-30`（已实现）

```json
// 200 返回
[ { "course_id": 3, "course_name": "操作系统", "total": 5, "completed": 4,
    "overdue": 1, "completion_rate": 0.8 },
  { "course_id": 4, "course_name": "计算机网络", "total": 0, "completed": 0,
    "overdue": 0, "completion_rate": 0 } ]
```

> **未实现（计划中）**：`by_course`/`trend` 内嵌于 overview、`GET /stats/courses/{course_id}/progress`、按完成时间（`completed_at`）的聚合。

## 4. 与版本/需求/任务的对应关系

| API 分组 | 覆盖需求 | 实现状态（2026-09-10） |
| --- | --- | --- |
| 认证、课程、任务、对话/会话 | FR-01/02/03/06/07/09 | **基础版已实现**（`/auth/logout`、`GET /tasks/{id}`、`DELETE /conversations/{id}` 除外） |
| 资料上传与状态、统计、用户管理 | FR-05/10/11/17 | **已实现**：`/materials`（上传/删除）、`/users`、`/users/{id}/role`、`/stats/overview`、`/stats/courses`；解析状态机与 `/materials/{id}/parse-status` **计划中** |
| RAG 问答（`type=rag`、`citations`）、任务拆解 | FR-12/13/14/15/16 | **未实现（计划中）** |

- 自动化测试现状：**21 条**（`backend/tests/test_api.py` 15 条 + `backend/tests/test_standard_features.py` 6 条），Codex 报告 21 passed；契约测试（OpenAPI/分页/错误结构）仍属计划中（见 [06-test-plan.md](06-test-plan.md)）。
- 本草案由 TASK-005 定稿为 OpenAPI 规格（含完整参数表、枚举、鉴权细节、限流策略与契约测试用例）；
- 实现冲突时以定稿规格为准，并回写本文档，保证 [AGENTS.md](../AGENTS.md) 一致性清单通过。
