# 2026-09-09 · 创建项目知识库与首批任务拆分

- **执行者**：DeepSeek 需求分析与规划 Agent
- **分支**：`deepseek/project-knowledge`
- **依据**：`DEEPSEEK_INITIAL_TASK.md`（初始化任务）
- **性质**：本轮**只产出文档与任务文件，未编写任何前端/后端/业务代码**

## 本轮目标

按任务书完成：项目知识库（AGENTS 规则 + docs/ 00–06）、设计思维全过程文档、任务看板说明、首批 6 个任务文件，并提交推送分支。

## 产出文件清单

| 文件 | 内容 |
| --- | --- |
| `AGENTS.md` | 两个 Agent 共同遵守的开发规则（工作流/分支提交/文档/任务流转/代码/一致性清单） |
| `docs/00-project-overview.md` | 项目目标、范围、角色、核心价值、文档地图 |
| `docs/01-design-thinking.md` | 共情→定义→构思→原型→测试→系统设计转化（含访谈提纲、POV、7 选 3 构思、低保真流程、测试方案） |
| `docs/02-requirements.md` | FR-01~17 + NFR-01~09 + 验收标准 + 假设影响清单 + 范围红线 |
| `docs/03-architecture.md` | 前端/后端/AI 网关/RAG/存储的关系、数据流、安全边界（技术选型待 TASK-003） |
| `docs/04-api-spec.md` | 草案 v0.1：认证/课程/任务/资料/对话/统计接口、错误结构、示例 |
| `docs/05-database.md` | users/courses/course_members/tasks/materials/material_chunks/conversations/messages |
| `docs/06-test-plan.md` | 功能/异常/AI 输出/UX/接口测试与门槛 |
| `docs/vibe-log/README.md` 与本文 | 日志规则与本轮记录 |
| `tasks/{inbox,doing,review,done}/README.md` | 任务看板四目录使用规则 |
| `tasks/inbox/TASK-001..006-*.md` | 首批任务：用户调研/需求定稿/架构/数据库/API/原型验证，状态均 `ready` |

## 关键决策

1. **方向收敛（7 选 3）**：保留 ①任务集中管理+截止提醒（I1）②课程资料库+RAG 问答（I2+I3）③AI 任务拆解弱化版（I4）；I5 统计可视化延后到标准版，I6 资料共享、I7 教师发布暂缓。
2. **版本分层**：基础版（登录/任务/资料列表/AI 对话/记录/≥3 API/持久化/前端展示）→ 标准版（三角色权限/上传/统计/可视化/异常处理/API 文档测试）→ 特色版（RAG：解析切分/向量索引/检索回答/来源展示 + AI 拆解）。
3. **编号体系定稿**：FR-01~17（01 文档第 6 节映射表与 02 文档编号完全一致）；任务 TASK-001~006；用例 FT/ET/AT。
4. **范围红线**：Live2D/语音/QQ/Telegram/复杂本地文件操作仅作可选；不做通用聊天机器人；README.md 一律不修改。
5. **技术栈不预设**：03/05 文档留「附录/决策项」，由 TASK-003/004 选型后回填，避免本轮引入无必要依赖。

## 待验证项（延续到后续任务）

- 01 文档全部用户行为/动机结论均为 ⚠️ **待验证假设**（无真实访谈数据）；
- 用户访谈落地 → `TASK-001-user-research`；
- 原型可用性验证（H1~H6、测试任务与指标）→ `TASK-006-prototype-validation`；
- RAG 评估门槛（引用命中率等）初步设定，待原型/实现后校准。

## 一致性自查结果

- [x] Markdown 语法检查（标题/表格/代码块闭合）
- [x] FR/API/TASK/状态词编号跨文档一致（01↔02↔03↔04↔05↔06↔tasks）
- [x] 相对链接指向的文件均存在
- [x] 待验证内容均带 ⚠️ 标注，未虚构已完成功能
- [x] 无密钥/`.env`/真实个人信息
- [x] 未修改 `README.md`
- [ ] 提交与推送（提交已完成于本分支；推送因本会话 TLS 环境限制待人工执行，推送成功后回填提交号）

## 提交信息（推送后回填）

- 提交号：_待推送后回填_（本地提交信息见上；推送动作需在具备完整 TLS 凭据的终端执行，例如 `git push -u origin deepseek/project-knowledge`）
- 说明：`docs: initialize project knowledge base and task breakdown (design thinking, requirements, architecture, api, database, test plan)`
