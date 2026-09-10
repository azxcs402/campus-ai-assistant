# 05 · 数据库设计（初步数据模型）

> 文档编号：05 ｜ 状态：草案 v0.1 ｜ 落地责任：`tasks/inbox/TASK-004-database-design.md`（定稿表结构、迁移、索引）
> 关联：[02-requirements.md](02-requirements.md) 数据需求、[04-api-spec.md](04-api-spec.md) 接口字段、[03-architecture.md](03-architecture.md) 存储边界。
>
> 说明：本文档定义**业务数据对象**。数据库选型（SQLite 起步或 PostgreSQL）、向量索引承载方式、迁移工具由 TASK-004 决策后回填「附录 A 选型决定」。

## 1. ER 总览（实体关系）

```text
users 1───N course_members N───1 courses 1───N tasks (self-ref 父任务 1─N 子任务)
  │                                1
  │                                │
  └──N conversations ──N messages  N── materials 1──N material_chunks
        （会话1─N消息）              （资料1─N切分单元）

users.role ∈ {student, teacher, admin}
courses.owner_id → users（创建者）
tasks.course_id → courses；tasks.created_by → users；tasks.parent_task_id → tasks
materials.course_id → courses；materials.uploaded_by → users
conversations.user_id → users；messages.conversation_id → conversations
material_chunks.material_id → materials
```

## 2. 数据对象明细

> 约定：`PK` 主键；`FK` 外键；`UQ` 唯一；`IDX` 索引建议；时间统一存 UTC 或带时区（TASK-004 定稿，展示层转本地）；软删除策略（is_deleted）由 TASK-004 决定，任务类数据倾向物理删除+审计可选。

### 2.1 users 用户

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | int/bigint | PK | |
| account | string | UQ, not null | 学号/账号，登录标识 |
| password_hash | string | not null | 密码哈希，禁止明文（NFR-03） |
| nickname | string | not null | 昵称 |
| role | enum | not null, default `student` | `student` / `teacher` / `admin`（FR-11）。**【实现状态 2026-09-10】** 已实现：注册时账号等于环境变量 `ADMIN_ACCOUNT` 即为 `admin`（启动时也会把该账号升级为 admin）；角色可经 `PATCH /users/{id}/role` 由管理员调整（`student/teacher/admin`），**管理员不能修改自己的角色**（400） |
| created_at / updated_at | datetime | not null | |

### 2.2 courses 课程

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | int | PK | |
| name | string | not null | 课程名 |
| semester | string | nullable | 如 2026-秋 |
| invite_code | string | UQ, nullable | 加入课程的邀请码（FR-03 join）— **【计划中，未实现】**（当前表无此列） |
| owner_id | int | FK→users | 创建者 |
| created_at / updated_at | datetime | not null | |

### 2.3 course_members 课程成员（学生与课程的 N–N）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | int | PK | |
| course_id | int | FK→courses, not null | |
| user_id | int | FK→users, not null | |
| role_in_course | enum | default `student` | `student` / `teacher`（教师可见所授课程） |
| joined_at | datetime | not null | |
|  |  | UQ(course_id, user_id) | 一人一课仅一条 |

### 2.4 tasks 学习任务（含子任务自关联）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | int | PK | |
| title | string | not null | 任务名（≤ 200 字符，FR-08 超长约束） |
| course_id | int | FK→courses, not null | 归属课程（FR-02） |
| created_by | int | FK→users, not null | 创建者（可见性边界） |
| parent_task_id | int | FK→tasks, nullable | 父任务（AI 拆解出的子任务用，FR-16）— **【计划中，未实现】** |
| status | enum | not null, default `todo` | `todo` / `doing` / `done` |
| priority | enum | default `medium` | `low` / `medium` / `high` |
| due_at | datetime | nullable | 截止时间（可空则视为无截止）。**【实现 2026-09-10】** 采用 ISO 8601 存 UTC；**纯日期输入按校园时区（UTC+8）当日 23:59:59.999999 归一化**；非法值 422 |
| note | text | nullable | 备注/任务要求（已实现，前端可录入） |
| estimate_hours | float | nullable | 预估时长（拆解子任务可带，FR-16）— **【计划中，未实现】** |
| completed_at | datetime | nullable | 完成时间。**【实现 2026-09-10】** 已加列（启动时幂等 `ALTER TABLE` 迁移）：`PATCH` 状态转 `done` 时写入、转回时清空；**当前未参与统计聚合**（统计过滤基于 `due_at`） |
| created_at / updated_at | datetime | not null | |
| IDX |  |  | (created_by, status)、(course_id, due_at) |

> 一致性规则：子任务 `course_id`、`created_by` 必须与父任务一致；父任务存在子任务时可展示"已拆分"状态（[01-design-thinking.md](01-design-thinking.md) 4.3）。

### 2.5 materials 课程资料（文件 + 解析状态）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | int | PK | |
| course_id | int | FK→courses, not null | 归属课程 |
| uploaded_by | int | FK→users, not null | 上传者 |
| filename | string | not null | 原始文件名 |
| title | string | nullable | 自定义标题，缺省=文件名 |
| file_path | string | not null | 存储路径（相对存储根，不存绝对路径） |
| file_type | string | not null | 扩展名/媒体类型（白名单，FR-05） |
| file_size | int | not null | 字节数 |
| parse_status | enum | not null, default `queued` | `queued` / `processing` / `ready` / `failed`（FR-05/12） |
| parse_error | string | nullable | 解析失败原因 |
| created_at / updated_at | datetime | not null | |
| IDX |  |  | (course_id, created_at) |

### 2.6 material_chunks 资料切分单元（RAG 基础，FR-12/13）— **【计划中，未实现】**

> **实现状态（2026-09-10）**：该表**尚未创建**；RAG（解析/切分/向量/检索）未实现，资料 `parse_status` 恒为 `queued`。下表为设计方案，保留供 RAG 立项时使用。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | int/bigint | PK | |
| material_id | int | FK→materials, not null | 所属资料 |
| seq | int | not null | 资料内顺序 |
| content | text | not null | 切分文本 |
| location | string | nullable | 定位元数据：章节/页码（来源展示，FR-15） |
| embedding | vector | nullable | 向量（若由独立向量库承载，则本字段可为空并记 `vector_ref`） |
| vector_ref | string | nullable | 独立向量库中的索引键 |
| created_at | datetime | not null | |
| UQ / IDX |  |  | UQ(material_id, seq)；IDX(material_id) |

> 删除/覆盖语义：删除 materials 时必须同步删除其全部 chunks 与向量索引条目（AC-13-2）；重传同名文件按新 material 处理，旧条目清理后生效（AC-13-3）。

### 2.7 conversations 会话

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | int | PK | |
| user_id | int | FK→users, not null | 所属用户 |
| title | string | nullable | 会话名（缺省用首条消息摘要） |
| created_at / updated_at | datetime | not null | 更新时间=最近活跃，用于列表排序（AC-07-2） |
| IDX |  |  | (user_id, updated_at desc) |

### 2.8 messages 消息

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | int/bigint | PK | |
| conversation_id | int | FK→conversations, not null | |
| role | enum | not null | `user` / `assistant` / `system`（可选）；**已实现**（仅 `user`/`assistant`） |
| type | enum | not null | `chat` 普通对话 / `rag` 课程资料问答（FR-14）— **【计划中，未实现】**（当前表无此列） |
| content | text | not null | 消息文本（**已实现**） |
| course_scope_id | int | FK→courses, nullable | RAG 检索范围（type=rag 时）— **【计划中，未实现】** |
| citations | json | nullable | 引用来源数组（material_id/filename/location/snippet，FR-15）— **【计划中，未实现】** |
| created_at | datetime | not null | |
| IDX |  |  | (conversation_id, created_at) |

> 消息一旦生成以追加为主；删除会话级联删除其消息（可交由 TASK-004 定级联策略）。

## 3. 派生/只读数据

- 统计（FR-10/17）不设冗余业务表，由统计聚合模块按需计算（`stats` 查询模型，见 [03-architecture.md](03-architecture.md) 3.2）；若后期数据量大再考虑物化，本期不做。
- 提醒（FR-09）：基础版不做独立提醒任务表，以 `tasks.due_at` 查询生成"即将截止"；如需主动推送（外部渠道）再引入提醒记录表（可选范围，不影响基础交付）。

## 4. 决策项与实现现状（2026-09-10 更新，基线 `codex/standard-feature-expansion` @ `222fa02`）

| # | 决策项 | 现状 |
| --- | --- | --- |
| 1 | 数据库选型与连接管理 | **已定**：SQLite + 原生 `sqlite3`，启动时 `init_db()` 建表 + 幂等 `ALTER TABLE`（如 `tasks.completed_at`） |
| 2 | 迁移与种子数据 | 启动自迁移（`CREATE TABLE IF NOT EXISTS` / 列存在性检查）；管理员由环境变量 `ADMIN_ACCOUNT` 指定；邀请码生成**未实现** |
| 3 | 时间存储与比较口径 | **已定**：统一存 UTC ISO 8601；纯日期输入与统计 `from/to` 按**校园时区 UTC+8** 取当日边界后转 UTC；日期筛选非法值 422 |
| 4 | 删除与级联策略 | **课程**：非空（有任务或资料）返回 409 **阻止删除**；**任务**：仅创建者/管理员可删；**资料**：上传者/课程所有者/管理员可删（其他 404）。软删除未采用 |
| 5 | 向量承载方式 | **未定（计划中）**：`material_chunks` 未建表，RAG 未实现 |
| 6 | 字段长度/枚举/建表 SQL | 已随代码实现（见各表"实现状态"标注）；`parent_task_id`/`estimate_hours`/`invite_code`/`material_chunks`/`messages.type` 等仍为**计划中** |
