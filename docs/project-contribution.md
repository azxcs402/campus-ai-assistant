# 成员贡献记录模板（project-contribution）

> 🔄 **final-review 更新注记（2026-09-09）**：正文 FR 现状表将 FR-04/FR-05 标为"未实现"，基于更早代码。提交 `a39a6e2` 后 **FR-04（课程资料列表）已实现、FR-05（上传/白名单/大小/删除）已部分实现**（解析状态机、同名策略、`parse-status` 端点未实现；RAG FR-12~15 仍未实现）。填写贡献表与答辩材料前，请以 [final-review.md](final-review.md) §2.2 的 FR 现状表为准更新。

> 文档编号：TASK-009 交付物 ③ ｜ 状态：**模板**（待小组填写） ｜ 最后更新：2026-09-09
>
> **重要定位声明**：本文是**模板文件**，供小组成员填写最终分工与工作量。文中「成员A/B/C/D」为**占位示例**，不代表任何真实成员姓名或真实工作量；**成员姓名、角色、分工、工作量均待小组讨论确认后填写**。禁止虚构真实姓名、工作量或未完成功能。
>
> 填写完成后请删除本文所有「占位/示例/待确认」提示，并同步更新本仓库文档地图中与本文件相关的引用（如需）。

---

## 1. 成员贡献表（模板）

> 填写说明：①「关键产出」请链接仓库内真实文件（相对本仓库根目录的路径）；②「自估工作量」建议用百分比或人天（小组内口径统一，合计尽量接近 100%）；③「备注」可写佐证方式（如 git log、文件归属）、配合情况或待办。

| 成员 | 角色 | 负责模块与文档 | 关键产出（链接仓库文件） | 自估工作量 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 成员A | 需求分析与设计思维 | 用户调研设计、画像/POV、构思筛选、需求文档 | [docs/00-project-overview.md](00-project-overview.md)、[docs/01-design-thinking.md](01-design-thinking.md)、[docs/02-requirements.md](02-requirements.md)、[tasks/](../tasks/) 任务拆分 | _待填_ | 按 git log 与文件归属可佐证（docs/ 与 tasks/ 主体） |
| 成员B | 架构与系统设计 | 架构、技术选型、接口、数据库设计 | [docs/03-architecture.md](03-architecture.md)、[docs/04-api-spec.md](04-api-spec.md)、[docs/05-database.md](05-database.md)、[docs/06-test-plan.md](06-test-plan.md) | _待填_ | 按 git log 与文件归属可佐证 |
| 成员C | 实现（MVP 代码） | 后端 API、前端页面、启动脚本 | [backend/app.py](../backend/app.py)、[backend/tests/test_api.py](../backend/tests/test_api.py)、[frontend/index.html](../frontend/index.html)、[frontend/app.js](../frontend/app.js)、[frontend/styles.css](../frontend/styles.css)、[run-backend.cmd](../run-backend.cmd)、[run-frontend.cmd](../run-frontend.cmd) | _待填_ | 按 git log 与文件归属可佐证（backend/ frontend/） |
| 成员D | 测试/审查/答辩材料 | 接口测试、文档交叉检查、答辩与演示材料 | [docs/presentation-outline.md](presentation-outline.md)、[docs/demo-script.md](demo-script.md)、本文（本批 docs/） | _待填_ | 按 git log 与文件归属可佐证 |

> **空白行**：小组人数多于 4 人可在此复制表头增加行；少于 4 人可合并角色并注明。

### 1.1 按 git log 与文件归属可佐证的分工建议（供小组讨论使用）

以下为**基于仓库文件归属与提交历史的建议口径**（Agent 未代替小组定人，仅给出佐证维度）：

- **知识库与设计思维文档、任务拆分** → 文件集中于 `docs/00~02`、`docs/vibe-log/`、`tasks/`；建议由负责需求分析与规划的同学认领；
- **架构 / 接口 / 数据库 / 测试计划文档** → 文件集中于 `docs/03~06`；建议由负责系统设计的同学认领；
- **MVP 代码与接口测试** → 文件集中于 `backend/`、`frontend/`、仓库根 `run-*.cmd`；建议由负责实现的同学认领；
- **审查与答辩材料** → 本批 `docs/presentation-outline.md`、`docs/demo-script.md`、`docs/project-contribution.md` 及其记录；建议由负责演示/答辩的同学认领并补齐。

> 注意：仓库内文档与任务由 DeepSeek Harness / Codex 两个 Agent 按课程工作流先行起草（见 [AGENTS.md](../AGENTS.md) 与 `docs/vibe-log/`），**Agent 产出不等于小组某成员的个人工作量**——小组成员应以「人工审阅、复核、修订、现场执行（访谈/测试/答辩）」等真实参与为依据填写，必要时用 git log 佐证谁做了哪些修订提交。

## 2. 项目成果清单

### 2.1 功能成果对照 FR（按实现现状填写，勿虚报）

| 编号 | 功能 | 现状 | 仓库证据 |
| --- | --- | --- | --- |
| FR-01 | 用户注册与登录（会话保持、退出） | ✅ 已实现（MVP） | [backend/app.py](../backend/app.py) `/auth/register\|login\|me`；[frontend/app.js](../frontend/app.js) 登录/注册表单与 localStorage token |
| FR-02 | 学习任务管理（增删改查、筛选排序） | ✅ 已实现（MVP） | [backend/app.py](../backend/app.py) `/tasks` 系列；[frontend/app.js](../frontend/app.js) `#taskForm`/`renderTasks` |
| FR-03 | 课程管理（创建/列表/成员） | 🟡 部分（创建+列表+自动加成员；无课程详情页与加入码） | [backend/app.py](../backend/app.py) `/courses` |
| FR-04 | 课程资料列表 | ⛔ 未实现（计划中） | —（无接口与页面） |
| FR-05 | 课程资料上传 | ⛔ 未实现（计划中，标准版） | — |
| FR-06 | AI 文本对话 | 🟡 已实现单轮对话；真实多轮上下文未接入 | [backend/app.py](../backend/app.py) `assistant_reply`；[vibe-log/2026-09-09-codex-mvp.md](vibe-log/2026-09-09-codex-mvp.md)「当前限制」 |
| FR-07 | 对话记录保存（会话+消息落库） | ✅ 已实现（后端落库与会话列表；前端仅自动使用最新会话，切换 UI 计划中） | [backend/app.py](../backend/app.py) `/conversations` 系列 |
| FR-08 | 异常输入与边界处理 | ⛔ 未实现（计划中，标准版） | — |
| FR-09 | 截止提醒与即将截止视图 | 🟡 部分（任务列表按截止排序；独立提醒视图未做） | [backend/app.py](../backend/app.py) `list_tasks` 排序逻辑 |
| FR-10 | 任务完成率统计 | ✅ 已实现接口（MVP 提前实现总览口径，无分课程/趋势） | [backend/app.py](../backend/app.py) `/stats/overview` |
| FR-11 | 角色与权限控制 | ⛔ 未实现（计划中，标准版） | — |
| FR-12~15 | RAG（解析切分/向量索引/检索回答/来源展示） | ⛔ 未实现（计划中，特色版） | — |
| FR-16 | AI 学习任务智能拆解 | ⛔ 未实现（计划中，特色版） | — |
| FR-17 | 学习数据可视化 | ⛔ 未实现（计划中，标准版） | — |

### 2.2 文档清单

| 文档 | 内容 | 路径 |
| --- | --- | --- |
| 项目总览 | 目标/范围/角色/版本分层 | [docs/00-project-overview.md](00-project-overview.md) |
| 设计思维 | 共情→定义→构思→原型→测试（⚠️ 假设已标注） | [docs/01-design-thinking.md](01-design-thinking.md) |
| 需求文档 | FR-01~17 / NFR / 版本分层 / 红线 | [docs/02-requirements.md](02-requirements.md) |
| 系统架构 | 组件、数据流、技术选型附录 | [docs/03-architecture.md](03-architecture.md) |
| API 规格 | 接口草案 v0.1 | [docs/04-api-spec.md](04-api-spec.md) |
| 数据库设计 | 数据对象草案 | [docs/05-database.md](05-database.md) |
| 测试计划 | 功能/异常/AI/UX/接口测试计划 | [docs/06-test-plan.md](06-test-plan.md) |
| 汇报大纲 | 8–12 分钟课程汇报讲稿大纲 | [docs/presentation-outline.md](presentation-outline.md) |
| 演示脚本 | 5 分钟现场演示脚本与检查单 | [docs/demo-script.md](demo-script.md) |
| 贡献记录 | 本模板 | [docs/project-contribution.md](project-contribution.md) |
| 工作日志 | Agent 各轮事实日志 | [docs/vibe-log/](../docs/vibe-log/) |

### 2.3 测试证据（如实引用，不得扩大）

| 项目 | 状态与声明 | 证据位置 |
| --- | --- | --- |
| 接口自动化测试 | 4 个用例，Codex 日志声明运行结果「4 passed」（health、注册→课程→任务→统计链路、会话消息持久化、未登录拦截 401） | [backend/tests/test_api.py](../backend/tests/test_api.py)、[docs/vibe-log/2026-09-09-codex-mvp.md](vibe-log/2026-09-09-codex-mvp.md) |
| 运行时冒烟 | Codex 日志声明：健康检查通过、前端静态页 HTTP 200、Python 语法检查通过 | 同上日志 |
| 完整功能/异常测试矩阵 | 仅存在于测试计划，未执行 | [docs/06-test-plan.md](06-test-plan.md) |
| 用户体验/原型测试 | 未执行（TASK-006 待办） | [tasks/inbox/TASK-006-prototype-validation.md](../tasks/inbox/TASK-006-prototype-validation.md) |

## 3. 第三方 / 参考说明（答辩需如实陈述）

- **EchoBot（技术参考）**：项目任务书指定 [EchoBot](https://github.com/KdaiP/EchoBot) 仅作**技术思路参考**，本项目**未复制其代码**，拥有独立的校园学习场景、需求分析、架构与实现（[AGENTS.md](../AGENTS.md) 第 1 节、[docs/00-project-overview.md](00-project-overview.md) §1）。当前仓库代码为 FastAPI + SQLite + 原生 JS 的独立实现（[backend/app.py](../backend/app.py)、[frontend/](../frontend/)）。
- **课程要求说明**：本项目属《系统设计与实践》课程项目，须从真实用户需求出发并走设计思维流程；**凡未经真实访谈/原型测试支撑的用户结论均为待验证假设**（[docs/01-design-thinking.md](01-design-thinking.md) 文档头声明），答辩表述不得与之冲突。
- **AI 协作说明（如课程要求披露）**：项目文档起草与代码初稿由两个 Agent（DeepSeek Harness / Codex）按任务文件完成，人工小组成员负责复核、修订与最终交付——如课程要求披露 AI 使用情况，请在答辩材料中如实说明协作方式与各自的审校工作量。

## 4. 填写注意事项

1. **不得虚报未完成功能**：FR-04/05、FR-08、FR-11、FR-12~17 均未实现，只能在「计划中/标准版/特色版」口径下表述，不得写「已完成」；
2. **不得虚构访谈/测试**：未执行的用户访谈（TASK-001）与原型测试（TASK-006）不能写成已做；测试结论只能引用第 2.3 节所列证据；
3. **不得虚构成员贡献**：所有成员姓名、角色、工作量为占位，须由小组当面确认后填写；工作量应反映真实参与（含对 Agent 产出的审校修订），可附 git log 佐证；
4. **引用一致性**：填写后请自查第 2 节的 FR 状态与最新代码一致（若后续 Codex 实现标准版功能，需同步更新本表并在 `docs/vibe-log/` 记录）；
5. **保密与安全**：不得把 API Key、`.env`、真实个人信息写进本文件或任何仓库文件（[AGENTS.md](../AGENTS.md) 第 2 节）；
6. 完成后删除本文档头部的「模板/占位」声明，并把本文档状态从「模板」改为「已填写」。
