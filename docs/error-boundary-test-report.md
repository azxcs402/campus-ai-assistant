# 异常与边界测试验收报告（error-boundary-test-report）

> 编制日期：2026-09-09 ｜ 编制方：DeepSeek（测试验收文档 Agent）
> **评审基线（代码事实来源）**：`origin/codex/api-provider-switching` @ **`40ea247 test: verify configurable provider forwarding`**
> 关联提交链：`5099b60 feat: add configurable AI providers` → `166677e test: cover error and network boundaries` → `40ea247 test: verify configurable provider forwarding`
> **评审方式（只读）**：以 `git show <ref>:<path>` 读取文件内容；**未运行 pytest、未切换分支、未修改 `backend/`、`frontend/`、`README.md` 或 `backend/tests/test_api.py`**。本报告是本轮唯一新增文件。
>
> **诚实边界（务必先读）**：
> 1. 本报告**未执行测试**。"15 passed" 为 Codex 的声明（`tasks/done/TASK-017`、`tasks/done/TASK-018`、`docs/vibe-log/2026-09-10-codex-*.md`）；本报告已静态核验 `backend/tests/test_api.py` 中**确有 15 个 `def test_` 用例**，且断言与第 1、2 节的覆盖声明逐条对应。
> 2. 本报告**未做浏览器端真实 API 测试**：未在浏览器中打开页面完成真实 API 配置切换与真实上游调用；凡前端相关结论均为**静态代码核验**，已逐项标注"静态推断"。
> 3. 本报告**不含任何真实 API Key**；测试代码内部使用的是占位字符串（`fake-key`、`not-a-real-key`）。

## 0. 验收环境（事实）

| 项目 | 状态 |
| --- | --- |
| 被验收分支 / 提交 | `codex/api-provider-switching` @ `40ea247`（已推送到远端，本地引用已同步） |
| 本次提交改动范围 | 仅 `backend/tests/test_api.py`（+28 行）、`tasks/done/TASK-018-provider-forwarding-test.md`、`docs/vibe-log/2026-09-10-codex-provider-forwarding-test.md`；**`backend/app.py`、`frontend/*`、`docs/06-test-plan.md` 自 `166677e` 起未改动** |
| 后端实现 | `backend/app.py`（517 行）：`ProviderConfig`（`app.py:218-230`）、`assistant_reply`（`app.py:459-485`）、`POST /conversations/{id}/messages`（`app.py:488-500`） |
| 测试文件 | `backend/tests/test_api.py`：**15 条用例**（`fastapi.testclient` 接口层 + 2 条对 `assistant_reply` 的单元级 mock 用例） |
| 前端实现 | `frontend/index.html`（供应商选择器 `#providerSelect`、"管理 API" `#providerManageBtn`、配置表单 `#providerForm` / `#providerApiKey`）、`frontend/app.js`（`campus_api_providers` localStorage 持久化、`provider: activeProvider()` 随消息发送） |
| 本地运行服务 | `127.0.0.1:5500`（前端静态）与 `127.0.0.1:8000`（后端）均在监听 |
| 运行服务来源 | `D:\桌面\campus-ai-assistant` 检出（分支 `codex/api-provider-switching`，工作树干净 @ `40ea247`）；此前实测 HTTP 返回字节数与检出文件完全一致（index.html 4294 B、app.js 13354 B），且本次提交未改前端，故服务内容即该分支前端版本 |
| 测试执行 | **未由本报告执行**；重跑需切换分支并安装依赖，超出只读范围 |

## 1. 11 类异常场景测试矩阵

| # | 异常场景 | 对应接口 / 页面 | 自动化用例（函数名） | 断言要点（事实） |
| --- | --- | --- | --- | --- |
| E1 | 重复注册 | `POST /api/v1/auth/register` ｜ 登录/注册卡（`#authForm`、`#registerBtn`） | `test_duplicate_registration_is_rejected` | 首次 201 → 同账号再次 409 |
| E2 | 非法课程名（空 / 超长） | `POST /api/v1/courses` ｜ "新建课程"（`#createCourseBtn`） | `test_invalid_course_name_is_rejected` | `name=""` → 422；`name="课"*101` → 422 |
| E3 | 非法截止日期 | `POST /api/v1/tasks`、`PATCH /api/v1/tasks/{id}` ｜ 任务表单 `#dueAt` | `test_task_due_at_rejects_invalid_datetime_and_normalizes_date` | `"abc"` → 422；`"2026-09-12"` → 201 且归一化 `2026-09-12T00:00:00+00:00`；PATCH 无时区值 → 归一化 `+00:00` |
| E4 | 不支持的文件格式 | `POST /api/v1/materials` ｜ 资料上传表单 `#materialForm` | `test_material_upload_rejects_unsupported_and_oversized_files` | `notes.exe` → 400 |
| E5 | 超过 20MB 的文件 | 同上 | 同上 | `b"x" * (20*1024*1024+1)` → 400 |
| E6 | 资料越权（删除他人资料） | `DELETE /api/v1/materials/{id}` ｜ 资料列表删除按钮 | `test_material_cannot_be_deleted_by_another_user` | 非上传者删除 → 404（不暴露资源存在性） |
| E7 | 任务不存在 | `PATCH` / `DELETE /api/v1/tasks/{id}` ｜ 任务列表"完成/删除" | `test_nonexistent_task_returns_not_found` | `id=999999` → 404（两种方法） |
| E8 | 无效 API 地址 | `POST /api/v1/conversations/{id}/messages`（`provider.base_url`）｜ AI 面板"管理 API" `#providerBaseUrl` | `test_message_provider_rejects_non_http_base_url` | `base_url="ftp://example.com"` → 422（后端 `ProviderConfig.validate_base_url`；前端另有 `/^https?:\/\//i` 前置校验） |
| E9 | API Key 错误 | 同上（上游返回 401） | `test_ai_api_key_error_timeout_and_network_failure_are_safe` | mock 抛 `HTTPError(401)` → 返回含"AI 服务暂时不可用"的固定文案，不抛异常 |
| E10 | AI 超时 | 同上（`urlopen(..., timeout=25)`） | 同上 | mock 抛 `TimeoutError` → 同一固定文案 |
| E11 | 网络中断 | 同上（DNS 失败/连接被拒等） | 同上 | mock 抛 `urllib.error.URLError` → 同一固定文案 |

> 说明：E9/E10/E11 由同一条用例内的三次 `monkeypatch` 循环覆盖；三条断言均只校验"安全文案关键字"，不校验上游差异（见第 4 节）。

## 2. 当前 15 条自动化测试的覆盖范围

| # | 用例 | 层级 | 覆盖内容 |
| --- | --- | --- | --- |
| 1 | `test_health` | 接口 | `GET /health` → `{"status":"ok"}` |
| 2 | `test_auth_course_task_and_stats` | 接口（主闭环） | 注册/登录态 → `/auth/me` → 建课 → 建任务 → 列表 → 标完成 → 统计完成率 1.0 → `/tasks/upcoming` 空数组 |
| 3 | `test_duplicate_registration_is_rejected` | 接口（异常） | 重复注册 409（E1） |
| 4 | `test_invalid_course_name_is_rejected` | 接口（异常） | 空名/超长名 422（E2） |
| 5 | `test_upcoming_tasks_returns_due_items` | 接口（功能） | 明日到期任务出现在即将截止列表首位（FR-09 子集） |
| 6 | `test_task_due_at_rejects_invalid_datetime_and_normalizes_date` | 接口（异常+边界） | 非法日期 422；纯日期与无时区时间归一化为 UTC（E3） |
| 7 | `test_nonexistent_task_returns_not_found` | 接口（异常） | 不存在任务 PATCH/DELETE 404（E7） |
| 8 | `test_conversation_persists_messages` | 接口（功能） | 消息落库与顺序 `["user","assistant"]`（FR-06/07） |
| 9 | `test_message_provider_rejects_non_http_base_url` | 接口（异常） | provider 非法 Base URL → 422（E8） |
| 10 | `test_ai_api_key_error_timeout_and_network_failure_are_safe` | 单元（mock 上游） | 401 错误 / 超时 / 网络中断三类故障均安全降级（E9/E10/E11） |
| 11 | **`test_custom_provider_is_forwarded_to_compatible_api`** | 单元（mock 上游） | **本次新增**：自定义 provider 被正确转发 —— mock `urlopen` 捕获请求，断言 `url == "http://127.0.0.1:9999/v1/chat/completions"`（尾部 `/` 被规范化）、`Authorization == "Bearer fake-key"`、请求体含 `"model": "test-model"`、`timeout == 25`，且返回内容进入回复 |
| 12 | `test_protected_endpoint_requires_login` | 接口（权限） | 未登录访问 `/tasks` → 401 |
| 13 | `test_material_upload_list_and_delete` | 接口（功能） | 上传 201（`parse_status="queued"`）→ 列表含文件名 → 删除 204（FR-04/05 子集） |
| 14 | `test_material_upload_rejects_unsupported_and_oversized_files` | 接口（异常） | 非法扩展名 400、超 20MB 400（E4/E5） |
| 15 | `test_material_cannot_be_deleted_by_another_user` | 接口（权限） | 越权删除资料 404（E6） |

**覆盖特征（事实）**：
- 全部测试**不依赖外网、不使用真实 Key**：AI 相关用例通过 `monkeypatch.setattr(app_module.urllib.request, "urlopen", ...)` 注入假实现；
- 测试数据库指向临时目录（`backend/tests/conftest.py` 设置 `DATABASE_PATH`、`TOKEN_SECRET`），不污染开发库；
- **未被自动化覆盖**：浏览器渲染与交互、真实供应商调用、令牌伪造/过期（仅有"未登录"）、重复提交幂等、级联删除、空状态、存储异常、同名文件策略、伪装扩展名、并发与 25s 真实超时体验。

## 3. 自动化测试与浏览器人工测试的区别

| 维度 | 自动化测试（现有 15 条） | 浏览器人工测试（尚需执行） |
| --- | --- | --- |
| 运行方式 | `TestClient` 进程内调用 + 单元级 mock，无真实网络 | 真实浏览器 + `run-frontend.cmd`(5500) + `run-backend.cmd`(8000) + 真实/模拟上游 |
| 证明范围 | 后端状态码、校验分支、异常降级文案、请求转发字段 | 页面渲染、表单交互、localStorage、供应商切换与真实回复 |
| 上游故障来源 | 注入的 `HTTPError(401)` / `TimeoutError` / `URLError` | 真实 401、真实超时、真实断网/代理/TLS 行为 |
| 可重复性 | 高（离线可重复，无凭据） | 低（依赖网络、额度、供应商状态） |
| 不能证明 | UI 可用性、真实上游差异、SSRF 实际可达性、超时体验 | 覆盖全部边界组合（需自动化兜底） |
| 本报告依据 | 已静态核验（未执行） | **未执行**（本报告不声称已完成浏览器 API 测试） |

## 4. API Key 错误、超时与网络中断的测试说明

### 4.1 自动化如何验证（事实）

- **Key 错误**：mock `urlopen` 抛 `urllib.error.HTTPError(..., 401, "Unauthorized", {}, None)`。注意 `HTTPError` 是 `URLError` 的子类，因此被 `app.py:484` 的 `except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError)` 捕获。
- **超时**：mock 抛 `TimeoutError`（真实路径为 `urlopen(..., timeout=25)`，`app.py:481`）。
- **网络中断**：mock 抛 `urllib.error.URLError`。
- **共同断言**：三种故障都返回包含 `"AI 服务暂时不可用"` 的固定文案；不抛异常、不返回堆栈、不回显 Key / Base URL / 上游响应细节。
- **配置转发**：新增用例验证自定义 `base_url`（含尾部 `/` 规范化）、`model`、`Authorization: Bearer <key>` 与 `timeout=25` 确实按预期构造出站请求；**该验证使用 mock，不产生真实网络请求**。

### 4.2 由此可主张的安全属性

| 属性 | 依据 |
| --- | --- |
| 不泄露凭据 | 固定文案不含 Key/URL；异常对象不进入响应；`app.py` 无日志输出调用（静态核验） |
| 不泄露上游细节 | 三类故障文案一致，无法通过响应差异探测上游（代价是可诊断性，见 4.4） |
| 不崩溃、不影响非 AI 功能 | 异常被捕获后返回文案；任务/资料/统计接口独立于 AI 调用链 |
| 密钥不落库 | `POST /messages` 仅写入 `payload.content` 与回复；provider（含 key）只用于本次出站请求 |
| 密钥不进仓库/页面文本 | `.gitignore` 含 `.env`；`.env.example` 的 `LLM_API_KEY` 为空；`#providerApiKey` 为 `type="password"`；测试使用 `fake-key` 占位 |

### 4.3 仍需注意的风险（自动化未覆盖）

1. **浏览器 localStorage 明文保存 Key**（`campus_api_providers`）：同源脚本（XSS）可读取；"管理 API"会把已存 Key 回填到密码框。界面已提示"不要在共享电脑上保存"，属演示级权衡。
2. **SSRF 面**：`base_url` 只校验 `http(s)://` 前缀（`app.py:224-230`），允许 `127.0.0.1`、内网网段等任意主机 → 后端可被诱导出站请求；无域名白名单、无私网拒绝、无速率限制（429 未实现）。
3. **同步阻塞超时**：单次请求最长占用 25s，无重试/退避/取消，并发可用性未验证。
4. **允许明文 http**：Key 会明文随请求发出，仅建议用于本地 mock/校内场景。

### 4.4 可诊断性取舍

三类故障返回同一句文案（安全上正确），但使用者无法区分"Key 错误""超时""断网"。若需兼顾可诊断性，建议在**服务端日志**（不含 Key）记录错误分类，前端仍展示统一文案。

## 5. 仍需人工执行的真实 API 配置切换步骤

> 目的：验证"网页配置的 API 真正生效"。**以下步骤尚未执行**（本报告未做浏览器测试）。执行时请使用**临时/低额度 Key**，**不要把 Key 写入任何文档、提交或聊天记录**；共享电脑上不要保存配置。

**前置**：`run-backend.cmd`（8000）、`run-frontend.cmd`（5500）已启动；浏览器打开 `http://127.0.0.1:5500`；登录或注册一个演示账号。

1. **确认当前为演示模式**：AI 面板状态显示"演示模式可用"；发送任意问题，应返回"演示模式：我已收到你的问题…"。
2. **打开配置入口**：点击 AI 面板「管理 API」→ 出现配置表单（名称 / Base URL / 模型 / API Key）。
3. **填写真实供应商配置**（示例字段名，值由演示者现场输入，勿记录 Key）：
   - 配置名称：如"答辩演示 API"；
   - Base URL：`https://api.deepseek.com/v1`（或其他 OpenAI 兼容地址，**必须以 `http://` 或 `https://` 开头**）；
   - 模型名称：如 `deepseek-chat`；
   - API Key：现场粘贴。
4. **保存并选中**：点击「保存 API」→ 表单隐藏；AI 面板状态下拉出现该配置并自动选中，状态文本变为"当前：<配置名称>"。
5. **验证真实调用**：发送一个稳定的简单问题 → 观察回复是否为**真实模型输出**（不再是"演示模式…"文案）；可在浏览器开发者工具 Network 面板确认请求发往 **8000 的 `/api/v1/conversations/{id}/messages`**，请求体含 `provider`（含 base_url/model，**不要把请求体截图公开展示**）。
6. **验证错误路径（重点）**：
   - **Key 错误**：把 Key 改成明显无效的字符串并保存 → 发送消息 → 应看到"AI 服务暂时不可用。请稍后重试…"（且不影响任务/资料/统计功能）；
   - **地址非法**：Base URL 填 `ftp://example.com` → 保存时前端即提示"Base URL 必须以 http:// 或 https:// 开头"；若绕过前端（直接调接口）应得到 422；
   - **网络中断/超时**：断开网络或填入不可达地址（如 `https://10.255.255.1/v1`）→ 发送消息 → 应在约 25s 内返回同一安全文案，页面不崩溃；
   - **切换回演示模式**：在 AI 面板下拉选择"环境变量 / 演示模式" → 再发消息 → 应回到"演示模式…"文案。
7. **验证配置管理**：再次点「管理 API」→ 确认可编辑已存配置；点「删除当前 API」（会二次确认）→ 下拉恢复为"环境变量 / 演示模式"。
8. **验证不泄露**：
   - 页面可见文本、聊天记录中不得出现 Key；
   - 浏览器开发者工具 → Application → Local Storage：确认 Key 仅存在于 `campus_api_providers`（属已知权衡，需在答辩中说明）；
   - 后端数据库（`messages` 表）与后端日志中不得出现 Key。
9. **清理**：删除演示配置；如使用真实 Key，请在演示后**吊销或轮换**该 Key；清空浏览器 localStorage（或在无痕窗口演示）。

**判定标准**：步骤 5 出现真实模型回复、步骤 6 三条错误路径均得到可读且一致的提示、步骤 8 无 Key 泄露 → 人工验收通过。

## 6. 当前未实现 RAG 的说明

- **事实**：`backend/app.py` 无文本解析、切分、embedding、向量存储/检索或引用返回实现；资料接口只有上传/列表/删除，`parse_status` 恒为 `queued`（前端展示"已保存（解析待接入）"，页面提示"当前版本仅保存资料元数据，文件解析和 RAG 检索将在下一阶段接入"）。
- **需求对照**：FR-12（解析切分）、FR-13（向量索引）、FR-14（检索增强回答）、FR-15（来源展示）**均未实现**（特色版计划）。
- **测试对照**：`docs/06-test-plan.md` 第 4 节的 AT-01~AT-06（引用命中、拒答、引用定位等）**全部未执行**；现有 15 条测试中的 AI 用例只覆盖**普通对话链路**（消息 → provider/环境变量 → 上游 chat completions），**不涉及"基于课程资料的问答"**。
- **答辩口径**：可说"RAG 的架构与方案已设计（`docs/03-architecture.md` §3.4、`docs/rag-plan.md`），当前未实现，属下一阶段"；**不可**说"已实现资料问答/已评估检索效果/有引用命中数据"。

## 7. 与 `docs/06-test-plan.md` 的一致性差异（待同步）

| 差异 | 说明 | 建议 |
| --- | --- | --- |
| 06 文档未记录新增自动化测试 | 该分支 `docs/06-test-plan.md` **自 `166677e` 起未修改**，15 条测试与 TASK-017/018 结果未回填 | 在 06 文档补"自动化测试清单/执行结果"小节 |
| ET-01 期望与实现不一致 | ET-01 期望"400 + `details` 逐字段提示"，实现为 FastAPI `422 + detail` 数组 | 统一 02/04/06 口径；前端先修可读性 |
| ET-03/05/06/08/09 无自动化 | 令牌失效、级联删除、重复提交、空状态、存储异常 | 列入后续测试任务或明确标注"人工验证" |
| ET-07 期望 502/504 区分 | 实现为统一文案（响应体方案，非状态码区分） | 与 4.4 的诊断取舍一并决策 |
| AT-01~AT-06（RAG） | 无实现可测 | 待 RAG 落地后再启用 |

## 8. 发现的问题（只读核验，未修复）

| 优先级 | 问题 | 证据（静态） | 影响 | 建议 |
| --- | --- | --- | --- | --- |
| **P0** | 点击「刷新」清空课程下拉 → 随后建任务 403 / 资料上传 422 | `frontend/app.js`：`loadData(selectedCourseId = null)` 与 `$('refreshBtn').onclick = loadData;`（`MouseEvent` 被当作课程 id） | 主要按钮触发后核心流程不可用 | 改为 `onclick = () => loadData();`，并按第 5 节思路回归验证 |
| P1 | 422 校验错误前端可能显示 `[object Object]` | `request()` 中 `new Error(body?.detail …)`，`detail` 为数组 | 异常输入的用户反馈不可读 | 规范化数组为逐条文本 |
| P1 | 自定义 Base URL 无主机/私网限制（SSRF 面） | `app.py:224-230` 仅校验协议前缀 | 可被诱导访问内网/本机 | 增加私网拒绝或域名白名单；答辩如实说明 |
| P1 | API Key 存浏览器 localStorage | `frontend/app.js` `campus_api_providers`；`index.html` 提示语 | 同源 XSS/共享电脑可读 | 生产化改服务端托管；答辩说明权衡 |
| P2 | 三类 AI 故障文案统一 | `app.py:484-485` | 排障体验差（安全上无害） | 服务端分类记录（不含 Key） |
| P2 | 资料列表固定渲染首个课程 | `frontend/app.js` `loadData()` 内 `renderMaterials(… freshCourses[0] …)` | 上传到非首课程后列表不可见 | 列表随课程下拉联动 |
| P2 | 06 测试计划未同步 15 条测试 | 第 7 节 | 文档与实现不一致 | 回填测试计划 |

## 9. 是否建议进入最终彩排

**建议：可以有条件进入最终彩排**，条件如下（未满足则不建议）：

1. **必修（约 10 分钟）**：修复 P0「刷新」缺陷（`onclick = () => loadData();`），并回归"刷新 → 添加任务/上传资料成功"。
2. **必做**：按第 5 节在浏览器完成一次**真实 API 配置切换**演练（含错误路径与清理），并记录"真实模型回复"这一事实；若现场网络不稳，默认使用演示模式并在台词中说明。
3. **必做**：彩排时确认后端为含 `/tasks/upcoming` 与 provider 支持的版本（前后端同源；注意本机 5500/8000 服务的是 `D:\桌面\campus-ai-assistant` 检出）。
4. **口径**：只引用可核验结论——"15 条接口层/单元级自动化测试，覆盖 11 类异常与边界场景，Codex 报告 15 passed；浏览器端真实 API 切换为人工复核项"；**不得**宣称浏览器端自动化验证或 RAG 已实现。
5. **可选**：请 Codex 将 15 条测试结果回填 `docs/06-test-plan.md`，消除第 7 节的文档差异后再彩排，效果更好。

若 P0 未修：彩排中**不要点击「刷新」按钮**，并在答辩中主动说明该已知缺陷与修复计划。
