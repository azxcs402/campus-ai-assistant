# Final Review · 最终评审（交付基线核验）

> 评审日期：2026-09-09 ｜ 评审方：DeepSeek（文档/评审 Agent）｜ 性质：静态评审 + 文档核验，未修改任何代码
> **评审基线**：`origin/codex/integration` @ `a39a6e2 feat: add course material management`（本地已同步的最远提交）。
> **方法说明（事实）**：逐行阅读 `backend/app.py`、`backend/tests/*`、`frontend/*`、根目录脚本与 `docs/` 后对照 [02-requirements.md](02-requirements.md)、[01-design-thinking.md](01-design-thinking.md) 完成。评审期间**无法连接 GitHub 与包源**（多次 fetch/pip 超时），因此：①未重跑自动化测试——"测试通过"仅引用 Codex 日志声明（`docs/vibe-log/2026-09-09-codex-mvp.md`：5 passed）与测试文件存在；②若远端在此时间点后有更新，需重新核验。
>
> 标签约定：**【事实】**=可直接由代码/文件核验；**【推断】**=合理推测未经实验；**【建议】**=评审给出的处理意见。

## 1. 当前系统功能总览（事实）

### 1.1 后端（`backend/app.py`，FastAPI + SQLite，共 18 个 HTTP 端点）

| 功能域 | 端点（`/api/v1` 前缀） | 实现要点 |
| --- | --- | --- |
| 健康检查 | `GET /health` | 返回 `{"status":"ok"}` |
| 认证 | `POST /auth/register`、`POST /auth/login`、`GET /auth/me` | PBKDF2 密码哈希；HMAC 自签 token；注册恒为 `role=student`；**无 `/auth/logout`** |
| 课程 | `GET /courses`、`POST /courses` | 创建时自动加入成员；列表含 `task_count`；**无更新/删除/加入（join）接口** |
| 学习任务 | `GET /tasks`、`POST /tasks`、`PATCH /tasks/{id}`、`DELETE /tasks/{id}` | 状态 `todo/doing/done`；排序=未完成优先→`due_at` 升序（空 `due_at` 靠后）；`due_at` **不做格式/时区校验** |
| 课程资料 | `GET /courses/{id}/materials`、`POST /materials`、`DELETE /materials/{id}` | 扩展名白名单 `.pdf/.ppt/.pptx/.doc/.docx/.txt/.md`、≤20MB；文件存 `data/uploads/<course_id>/<uuid>.<ext>`；**`parse_status` 恒为 `queued`，无任何解析处理**；删除仅上传者本人 |
| 对话 | `GET/POST /conversations`、`POST/GET /conversations/{id}/messages` | 消息与回复落库；会话按 `updated_at` 倒序；AI 调用见 1.2 |
| 统计 | `GET /stats/overview` | 仅 `total/completed/completion_rate`；**无逾期、无按课程、无时间范围** |

数据库表（`init_db`，事实）：`users, courses, course_members, tasks, materials, conversations, messages` 共 7 张；**无 `material_chunks`**；`tasks` 无 `parent_task_id/estimate_hours/completed_at`；`messages` 无 `type/course_scope_id/citations`（对照 [05-database.md](05-database.md) 草案）。

### 1.2 AI 对话（事实）

- 未配置 `LLM_API_KEY` → 返回固定"演示模式"文案（无网络依赖，演示稳定）。
- 配置后 → `urllib` 调 OpenAI 兼容 `/chat/completions`（默认 `https://api.deepseek.com/v1`，模型 `deepseek-chat`，25s 超时，异常时返回"AI 服务暂时不可用"）。
- **请求只包含当前问题**，不携带该会话历史消息 → **真实多轮上下文未接入**（与 Codex 日志"当前限制"一致）。
- 无 embedding/向量/RAG 相关代码。

### 1.3 前端（`frontend/`，原生 HTML/CSS/JS 单页）

面板：登录/注册卡 → 顶部统计三卡（全部任务/已完成/完成率）＋「学习任务」面板（新建表单 + 任务列表[完成/恢复/删除]）＋「课程资料」面板（上传表单 + 列表[标题/文件名/大小/状态/删除]，提示语"RAG 检索将在下一阶段接入"）＋「AI 学习助手」面板（对话，标题徽标静态为"演示模式可用"）。
已知前端约束（事实）：会话**固定复用最新一条**，无历史切换 UI；资料列表**只展示第一个课程**的资料（上传目标可选任意课程，但列表不随选择刷新）；任务无编辑入口（仅完成/删除）；登出=删除本地 token 并刷新（无服务端登出）。

### 1.4 测试（引用 Codex 日志 + 文件核验）

`backend/tests/test_api.py` 共 5 条：健康检查；注册→建课→建任务→标完成→统计（完成率=1.0）；会话消息落库（user/assistant 顺序）；未登录 401 拦截；资料上传/列表/删除（含 `parse_status=="queued"` 断言）。Codex 日志声明 5 passed；**本评审未能重跑**（网络不可用无法安装依赖），建议答辩前在联网环境执行 `pip install -r backend/requirements.txt && python -m pytest backend/tests -q` 并留存输出。

## 2. 实际代码与文档的一致性检查

### 2.1 任务书基础版门槛（结论：**a39a6e2 之后已全部满足**）—— 事实

| 任务书门槛 | 状态 | 证据 |
| --- | --- | --- |
| ①用户登录 | ✅ | `/auth/register`、`/auth/login`、前端登录卡 |
| ②学习任务增删改查 | ✅（界面无"编辑"，API 支持 PATCH） | `/tasks` 系列 4 端点 |
| ③课程资料列表 | ✅（a39a6e2 新增） | `GET /courses/{id}/materials` + 前端资料区（修复了 [mvp-review.md](mvp-review.md) R-1"未实现"的旧结论，见 5 节） |
| ④AI 文本对话 | ✅（单轮；演示模式或真实 LLM） | `assistant_reply` |
| ⑤对话记录保存 | ✅（落库；UI 无历史切换） | `messages` 表、`GET /conversations` |
| ⑥≥3 个 HTTP API | ✅（实际 18 个） | 1.1 |
| ⑦数据库持久化 | ✅ | SQLite `data/app.db` |
| ⑧前端展示后端数据 | ✅ | `frontend/app.js` 全量走 API |

### 2.2 FR 逐条核验（对照 [02-requirements.md](02-requirements.md)）

| FR | 状态（事实） | 与需求口径的出入 |
| --- | --- | --- |
| FR-01 注册登录 | 部分 | 无退出接口/会话失效机制；错误提示见 P0-2 |
| FR-02 任务管理 | 部分 | CRUD API 全；UI 无编辑、无备注录入；`due_at` 无校验（P1-5） |
| FR-03 课程管理 | 部分 | 仅创建+列表；无改名/删除/加入邀请码 |
| FR-04 课程资料列表 | ✅ 已实现 | 与 AC-04-1/04-2 相符；列表含解析状态 |
| FR-05 课程资料上传 | 部分 | 白名单/大小/删除已实现（AC-05-1/2/4 前半）；**无同名策略提示、无解析状态机与 `parse-status` 端点（AC-05-3/05-4 后半 ✗）** |
| FR-06 AI 文本对话 | 部分 | 单轮可答（AC-06-1/3）；**AC-06-2"多轮上下文连续"未实现** |
| FR-07 对话记录保存 | 部分 | 后端落库与会话列表 ✓（AC-07-1/2/3 后端）；**UI 无历史会话切换** |
| FR-08 异常输入处理 | 部分 | Pydantic 后端校验存在但错误结构是 FastAPI `detail`，**非 [04-api-spec.md](04-api-spec.md) 草案的 `code/message/details` 结构**；前端 422 显示不可读（P0-2） |
| FR-09 截止提醒/即将截止 | 未实现 | 仅列表排序近似；无即将截止区/高亮/剩余时间（P1-1） |
| FR-10 完成率统计 | 部分 | 总完成率 ✓；无按课程/时间段/逾期（实现的是 MVP 子集，04 草案将本接口列标准版，Codex 提前实现了子集） |
| FR-11 角色权限 | 未实现 | 标准版范围；注册恒 student，无 teacher/admin |
| FR-12~15 RAG | 未实现 | 特色版范围；无 embedding/向量/检索/引用（见 [final-rag-decision.md](final-rag-decision.md)） |
| FR-16 AI 拆解 | 未实现 | 特色版范围 |
| FR-17 数据可视化 | 未实现 | 标准版范围 |

### 2.3 API / 数据库 / 前端与既有文档的差异（事实）

- [04-api-spec.md](04-api-spec.md) 草案中以下端点**未实现**：`POST /auth/logout`、`GET/PATCH/DELETE /courses/{id}`、`POST /courses/{id}/join`、`GET /tasks/upcoming`、`POST /tasks/{id}/split`、`POST /tasks/batch`、`GET /materials/{id}/parse-status`、`DELETE /conversations/{id}`、`GET /stats/courses/{id}/progress`、`/users` 系列。错误结构、分页封装（`{items,total,…}`）也未落地（返回裸数组）。
- [05-database.md](05-database.md) 草案中 `material_chunks`、`messages` 扩展列、`tasks` 扩展列未建。
- [06-test-plan.md](06-test-plan.md) 的 FT-05 期望状态机流转到 `ready`——当前不可能发生（P0-1 相关）。
- **文档口径过时清单**：本文件与 [final-demo-checklist.md](final-demo-checklist.md)、[final-rag-decision.md](final-rag-decision.md) 以当前代码为准；此前基于更早代码（无资料功能）的 [mvp-review.md](mvp-review.md)、[rag-plan.md](rag-plan.md)、[demo-script.md](demo-script.md)、[presentation-outline.md](presentation-outline.md)、[project-contribution.md](project-contribution.md) 已在各自顶部加入"final-review 更新注记"，答辩引用时以标注为准。

## 3. 问题清单（P0 / P1 / P2）

### P0 —— 演示/诚信红线，答辩前必须处理

**P0-1 资料"待解析"是空状态机，存在误导（事实→建议）**
- 现象：所有上传资料 `parse_status` 恒为 `queued`，后端没有任何解析/状态流转代码；前端资料区固定显示"待解析"，提示语写"当前版本保存资料和解析状态"。
- 复现：上传任意 `.txt` → 列表中状态一直为"待解析"，永远不变。
- 影响：若答辩把"资料上传"描述成"已解析/可基于资料问答"即失真；评审追问"解析结果在哪、状态如何到 ready"会无法回答。
- 建议（二选一，需 Codex/人工拍板）：A. 维持"仅存储"口径——把 UI 文案改为"已保存（解析待接入）"、隐藏或改写"待解析"状态；B. 实现最小 TXT/MD 解析并让状态流转。**不得在未实现解析时宣称可解析/可问答**（诚信红线，见 [final-rag-decision.md](final-rag-decision.md)）。

**P0-2 前端 422/校验错误不可读（事实→建议）**
- 现象：`request()` 将 FastAPI 的 `detail`（数组）直接 `new Error(...)`；注册/登录路径显示为 `[object Object]`；任务/资料/聊天表单路径**无 try/catch**，校验失败为静默未处理 Promise。
- 复现：注册时输入 5 位密码点"注册"→ 页面显示 `[object Object]`（注册路径）或毫无反应（任务表单路径：输入空标题提交）。
- 影响：异常输入处理（FR-08）在界面上不可用，演示时一旦出错无法自解释。
- 建议（Codex，低风险高价值）：`request()` 内把 `detail`（字符串或数组）规范化为可读文本；给任务/资料/聊天提交补 try/catch 与禁用态防重复。

**P0-3 口径红线（建议）**：当前不存在任何"基于课程资料的问答/向量检索/RAG"实现；上传文件仅被保存。凡演示与答辩涉及"资料问答/RAG/召回/来源引用"只能表述为"计划中"，并可使用 [final-rag-decision.md](final-rag-decision.md) 第 6 节的解释话术。代码内已有证据（前端提示语）支持"下一阶段接入"的口径，切勿与之矛盾。

### P1 —— 建议答辩前修复或至少明确知晓

**P1-1 即将截止/提醒视图缺失（事实）**：仅任务列表按截止升序。复现：造一条 1 小时后截止任务，无任何高亮/剩余时间/提醒区。影响：FR-09 无载体，演示"防漏截止"价值弱。建议：若时间允许，加最小"即将截止区"（如 ≤3 天高亮 + 剩余天数文案，纯前端或加 `/tasks/upcoming` 皆可）；否则在答辩中如实说明并展示"排序近似"。

**P1-2 会话历史不可切换（事实）**：前端固定复用 `conversations[0]`。复现：聊两轮后新建会话（无入口）不可行；刷新后回到旧会话。影响：FR-07 的"历史回看/继续"只有后端能力。建议：低成本加会话列表/切换或至少"新建会话"按钮；否则口径改为"记录已保存、界面切换属后续"。

**P1-3 资料列表固定在第一个课程（事实）**：`loadData()` 只渲染 `freshCourses[0]` 的资料。复现：预置 2 门课程，向第二门上传资料 → 上传成功，但列表仍显示第一门课程资料，用户会以为上传丢失。影响：多课程演示必踩坑。建议（Codex）：资料区绑定课程下拉，切换即重新拉取 `GET /courses/{id}/materials`（演示只用单课程可临时规避）。

**P1-4 前端提交无防重复、失败静默（事实）**：任务/资料/聊天提交均无 loading/禁用与 try/catch。复现：双击"添加任务"/网络慢时重复提交产生多条。建议（Codex）：提交中禁用按钮 + try/catch + 错误条展示（与 P0-2 一并处理）。

**P1-5 截止时间无校验、无时区语义（事实）**：`due_at` 任意字符串可入库；前端 date 控件给 `YYYY-MM-DD`，列表原样输出；排序为字符串比较。复现：API 直传 `due_at="abc"` 成功。建议：至少前端约束 + 后端 ISO 校验；演示数据避免混用格式（此点同时关联 UX-02）。

**P1-6 资料无预览/下载（事实）**：上传后仅见元数据，UI 无法打开文件。演示"查看资料"只能展示列表。建议：若演示需要"能看内容"，可（不改代码前提下）讲解存储位置 `data/uploads/<course_id>/`；产品上补下载/预览接口属后续。

**P1-7 `.env` 不会被程序读取（事实）**：代码用 `os.getenv`，无 dotenv 加载逻辑；`run-backend.cmd` 也不读取 `.env`。影响：演示前把 key 写进 `.env` 不会生效。建议：在演示准备说明中明确"在启动后端前于当前会话导出 `LLM_API_KEY` 等环境变量"（见 [final-demo-checklist.md](final-demo-checklist.md)），长期由 Codex 增加 dotenv 或文档说明（推断：无 dotenv 依赖 → 见 `requirements.txt`）。

### P2 —— 可延后/改进

- **README.md 仅一行标题（事实）**：AGENTS.md 规定 Agent 不得改 README，需人工补写（项目简介/启动/架构/演示/致谢 EchoBot 仅参考）。
- **测试覆盖缺口（事实→建议）**：现有 5 条未覆盖非法扩展名/超 20MB/403 非成员/删除他人资料 404/重复注册 409/字段非法 422/越权等（[06-test-plan.md](06-test-plan.md) ET 系列）。建议 Codex 若有余力补异常用例；答辩前务必联网重跑全量并留档（本评审未能执行，见文首）。
- **OpenAPI 文档未与 04 草案同步（事实）**：FastAPI `/docs` 自动生成可用；`docs/04-api-spec.md` 仍为草案 v0.1，且草案中若干端点未实现（见 2.3）。
- **无演示种子数据脚本（推断→建议）**：建议 Codex 提供一次性 seed（创建课程/示例任务/示例资料），答辩准备更稳。
- **移动端未实测（推断）**：仅 CSS 两档媒体查询；手机浏览器可用性未验证（沿用 mvp-review UX-10）。
- **角色/权限、统计可视化等标准版项**：见 2.2，本期不要求（02 文档版本口径）。

## 4. Codex 下一步应执行的代码任务（按优先级，均不改文档）

| # | 优先级 | 任务 | 证据位置 | 建议验收 |
| --- | --- | --- | --- | --- |
| C-1 | P0 | 修正资料状态口径：要么"仅存储"文案（去掉误导的"待解析"承诺），要么实现最小 TXT/MD 解析 + 状态机 + `GET /materials/{id}/parse-status` | `backend/app.py` materials 部分、`frontend/index.html` 提示语、`frontend/app.js` `renderMaterials` | 上传后状态不再撒谎：或明确"已保存"，或能流转到 `ready/failed` |
| C-2 | P0 | 前端错误可读 + 防重复：`request()` 规范化 `detail`；任务/资料/聊天表单补 try/catch、loading 禁用 | `frontend/app.js` | 注册 5 位密码、空标题提交均给出可读中文提示且不产生重复数据 |
| C-3 | P1 | 资料列表随课程切换（下拉联动刷新） | `frontend/app.js` `loadData/renderMaterials`、`index.html` | 多课程下上传到 B 课后，切换到 B 课可见 |
| C-4 | P1 | （可选小步）会话列表/切换 UI，或加"新建会话" | `frontend/app.js` | 能切换历史会话或新建会话 |
| C-5 | P1 | `due_at` 后端 ISO 校验 + 前端展示友好化（含"即将截止"高亮可并入 C-1 批次） | `backend/app.py` `TaskIn/TaskPatch` | 非法日期 400；列表展示可读日期 |
| C-6 | P2 | 补异常/权限/边界测试用例；提供 seed 数据脚本 | `backend/tests/` | 全量测试通过并留档输出 |
| C-7 | P2 | 说明/支持 .env 加载（dotenv 或文档化环境变量导出） | `run-backend.cmd`、`requirements.txt` | 无 key 时演示模式；有 key 时真实回复（需联网验证） |

> 红线提醒（Codex）：以上任务**不得**把"资料问答/RAG"标记为实现；embedding 决策见 [final-rag-decision.md](final-rag-decision.md) D 项，需人工确认后再动工。

## 5. 与先前评审文档的关系（更新说明）

- [mvp-review.md](mvp-review.md) 基于更早基线（无资料功能），其 R-1（FR-04 未实现、门槛③不达标）**已被 a39a6e2 解决**：资料列表/上传/删除已实现。其余 UX 问题（UX-01~10）中，UX-01 校验错误、UX-02 时间语义、UX-03 状态徽标、UX-04 会话切换、UX-05 防重复、UX-09 无编辑入口等在本次复核中**仍成立**（已并入本文档 P0/P1）；UX-06（静默自动建课）仍成立但影响低。
- [demo-script.md](demo-script.md) / [presentation-outline.md](presentation-outline.md) / [project-contribution.md](project-contribution.md) 中"资料上传与列表未实现"的表述基于旧代码；权威的演示流程见 [final-demo-checklist.md](final-demo-checklist.md)。
- [rag-plan.md](rag-plan.md) / [rag-demo-dataset.md](rag-demo-dataset.md) 为**设计方案**（计划），不是已实现；当前实现决策见 [final-rag-decision.md](final-rag-decision.md)。

## 6. 一致性自查

- [x] 所有"已实现/未实现/部分"表述均可由代码/文件核验（文首基线 a39a6e2）
- [x] 测试结论未夸大：5 passed 仅引用 Codex 日志，明确标注"本评审未重跑"
- [x] 问题清单每项标注 事实/推断/建议 并提供复现
- [x] 未修改 backend/、frontend/、README.md 及任何配置文件
- [x] 交付文档位于 docs/，与前文档的过时表述已在本文件与各文档顶部注记中澄清
