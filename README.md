# 校园智能学习助手

Campus AI Assistant 是一个面向大学生的课程任务与资料管理系统。项目把课程、学习任务、截止时间、课程资料和 AI 学习助手集中到一个入口，帮助用户记录任务、跟踪完成情况，并把 AI 建议整理成可执行的学习安排。

本项目用于《系统设计与实践》课程答辩。当前版本定位为可运行、可演示的课程项目，优先保证核心功能真实可用、数据能够持久化、接口行为可测试。

**公开项目链接：** https://github.com/azxcs402/campus-ai-assistant

> `127.0.0.1` 地址仅用于启动后的本机演示，不作为教师访问项目的提交链接。

## 功能概览

当前版本已实现：

- 用户注册、登录、会话保持和退出入口
- 课程创建、课程列表、课程详情、课程修改和安全删除
- 学习任务创建、编辑、完成、恢复、删除、筛选和截止时间排序
- 即将截止任务展示和逾期任务统计
- 课程资料上传、按课程查看、删除，以及文件类型和大小校验
- AI 文本对话、会话与消息保存
- OpenAI 兼容 API 配置，包括 Base URL、模型名称和 API Key
- 无 API Key 时的本地演示模式和 AI 服务故障降级
- 按课程和日期范围统计任务总数、完成数、逾期数和完成率
- 课程完成率的前端条形图展示
- student、teacher、admin 角色模型及管理员用户角色管理
- 后端资源归属校验和越权访问保护

当前明确不属于已实现功能：

- 课程资料的文本解析、切分、向量化、检索和来源引用
- 基于课程资料的 RAG 问答
- AI 任务智能拆解和子任务批量写入
- 真实用户调研、原型验证和完整用户体验测试

上述内容在需求、架构或测试文档中作为后续计划记录，答辩时不应表述为当前版本已经完成。

## 技术栈

### 前端

- HTML、CSS、原生 JavaScript
- 浏览器 `fetch` 调用后端 HTTP API
- 浏览器 `localStorage` 保存登录态和用户配置的 AI API 信息

### 后端

- Python 3
- FastAPI、Uvicorn、Pydantic
- SQLite
- `python-multipart`，用于资料上传
- OpenAI 兼容 HTTP API，用于可选的真实 AI 对话

### 工程特点

- 前后端分离，前端只通过 HTTP API 获取和提交数据
- SQLite 保存用户、课程、任务、资料、会话和消息
- 后端统一执行身份认证、资源归属和管理员权限校验
- AI 服务不可用时不影响任务、课程、资料和统计功能
- 测试使用临时数据库，不污染开发环境中的 `data/app.db`

## 项目结构

```text
campus-ai-assistant/
├─ backend/
│  ├─ app.py                         # FastAPI 应用、数据模型和 API
│  ├─ offline_eval.py                # AI 离线评估辅助逻辑
│  ├─ requirements.txt               # Python 依赖
│  └─ tests/                         # 后端自动化测试
├─ frontend/
│  ├─ index.html                     # 页面结构
│  ├─ app.js                         # 前端状态、交互和 API 调用
│  └─ styles.css                     # 页面样式
├─ data/
│  ├─ app.db                         # 本地 SQLite 数据库，运行后生成
│  └─ uploads/                       # 上传资料保存目录，运行后生成
├─ docs/
│  ├─ 00-project-overview.md         # 项目概览
│  ├─ 01-design-thinking.md          # 设计思维与需求分析
│  ├─ 02-requirements.md             # 需求和版本分层
│  ├─ 03-architecture.md             # 系统架构
│  ├─ 04-api-spec.md                 # API 说明
│  ├─ 05-database.md                 # 数据库设计
│  ├─ 06-test-plan.md                # 测试计划与执行记录
│  ├─ final-demo-checklist.md        # 现场演示清单
│  ├─ presentation-outline.md        # 答辩汇报大纲
│  ├─ project-contribution.md        # 项目分工与贡献说明
│  └─ vibe-log/                      # Vibe Coding 过程日志
├─ ppt/
│  └─ build_defense_ppt.mjs          # 答辩 PPT 生成脚本
├─ run-backend.cmd                   # 启动后端
├─ run-frontend.cmd                  # 启动前端静态服务器
└─ README.md
```

## 环境要求

- Windows、macOS 或 Linux
- Python 3.10 或更高版本
- Node.js，仅在使用 `ppt/build_defense_ppt.mjs` 生成答辩 PPT 时需要
- 一个可用的现代浏览器，如 Chrome 或 Edge

项目不要求前端安装 npm 依赖。后端依赖安装在 `backend/.venv` 中即可。

## 安装与启动

### 1. 创建后端虚拟环境并安装依赖

在项目根目录执行：

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..
```

如果系统没有 `py` 命令，可以将其替换为 `python`。

### 2. 启动后端

双击项目根目录的 `run-backend.cmd`，或执行：

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000 --app-dir backend
```

后端地址：

- API 根地址：`http://127.0.0.1:8000`
- 健康检查：`http://127.0.0.1:8000/api/v1/health`
- Swagger 文档：`http://127.0.0.1:8000/docs`

### 3. 启动前端

在另一个终端双击 `run-frontend.cmd`，或执行：

```powershell
cd frontend
py -m http.server 5500
```

然后打开 `http://127.0.0.1:5500`。前端和后端都启动后，注册账号或使用已有账号登录即可。

## AI API 配置

项目支持两种 AI 对话模式。

### 演示模式

不配置 API Key 时，系统返回本地演示回复。任务管理、课程管理、资料管理和统计功能不依赖外部 AI 服务，仍可正常运行。

### 真实模型模式

可以在页面的“管理 API”中填写配置名称、OpenAI 兼容接口的 Base URL、模型名称和 API Key。也可以在启动后端前设置环境变量：

```powershell
$env:LLM_API_KEY = "你的 API Key"
$env:LLM_BASE_URL = "https://api.deepseek.com/v1"
$env:LLM_MODEL = "deepseek-chat"
```

项目也会读取根目录 `.env` 中的本地环境变量。`.env` 不应提交到 Git，API Key 不应写入 README、日志、截图或源码。

## 演示账号与数据

首次使用可以直接在登录页注册账号。答辩演示建议提前准备：

- 1 门课程
- 2–3 条学习任务
- 1 条今日或近期截止的任务
- 1 份小型 `.txt` 或 `.md` 课程资料
- 1 条 AI 对话问题

详细的 5 分钟演示步骤见 [docs/final-demo-checklist.md](docs/final-demo-checklist.md)。资料上传当前主要验证文件保存、元数据展示、格式白名单和 20 MB 大小限制。资料解析与 RAG 问答尚未实现。

## 测试

在项目根目录执行：

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests -q
```

当前文档记录的自动化测试共 21 条，覆盖：

- 健康检查、注册登录和受保护接口
- 课程、任务、资料和会话主流程
- 任务编辑、完成状态和统计
- 课程详情、删除策略和角色权限
- 逾期统计、日期范围校验和课程统计
- 资料格式、文件大小和越权删除
- AI API 地址校验、供应商参数转发、401、超时和网络故障降级
- AI 离线评估流程

测试不等同于真实用户调研或完整用户体验测试。相关人工测试目前仍属于后续工作。

## API 主要分组

API 前缀为 `/api/v1`，主要分组如下：

- `/health`：健康检查
- `/auth/*`：注册、登录和当前用户
- `/users/*`：管理员用户和角色管理
- `/courses/*`：课程创建、列表、详情、修改和删除
- `/tasks/*`：任务增删改查、完成状态和即将截止任务
- `/materials`：课程资料上传、列表和删除
- `/conversations/*`：会话和 AI 消息
- `/stats/*`：总览统计和按课程统计

完整接口、请求字段、响应示例和实现差异见 [docs/04-api-spec.md](docs/04-api-spec.md)。运行后也可以通过 Swagger 查看实际 API。

## 数据库与文件存储

默认数据库路径为 `data/app.db`，默认资料目录为 `data/uploads/<course_id>/`。

主要数据对象包括：`users`、`courses`、`course_members`、`tasks`、`materials`、`conversations` 和 `messages`。

默认情况下，数据库和上传文件属于本地开发数据，不应直接作为源码提交物的一部分。数据库设计见 [docs/05-database.md](docs/05-database.md)。

## 项目文档与课程交付材料

项目设计和交付材料位于 `docs/`，主要包括：

- 项目概览和设计思维文档
- 需求、架构、API 和数据库文档
- 测试计划、测试验收和 AI 离线评估
- 项目分工说明
- Vibe Coding 日志
- 答辩大纲和现场演示清单
- RAG 方案与当前不实现 RAG 的决策说明

课程答辩 PPT 正在制作中，生成脚本位于 `ppt/build_defense_ppt.mjs`。个人职业发展规划属于课程要求的个人材料，单独提交，不作为本项目 README 或源码的一部分。

## 已知限制与后续方向

- 资料上传后目前保存文件和元数据，解析状态仍需进一步实现
- RAG、资料引用和基于资料的问答属于后续特色能力
- AI 对话当前以单轮请求为主，完整历史上下文和会话切换仍需增强
- 邀请码加入课程、部分教师专属权限和部分管理接口仍可继续完善
- 统计当前以截止日期为主要筛选口径，按完成时间的趋势统计属于后续方向
- 真实用户调研、原型验证、人工 AI 评分和真机测试尚未完成

项目当前版本优先保证功能边界清楚、演示过程可复现，并在答辩中如实区分“已实现”“部分实现”和“计划中”。

## 相关文档

- [答辩汇报大纲](docs/presentation-outline.md)
- [现场演示清单](docs/final-demo-checklist.md)
- [最终评审记录](docs/final-review.md)
- [标准版功能验收表](docs/standard-feature-acceptance.md)
- [项目分工说明](docs/project-contribution.md)
- [Vibe Coding 日志](docs/vibe-log/README.md)

## AI 协作说明

项目开发过程中使用 Codex 和 DeepSeek Harness 作为辅助工具。工具主要用于需求拆分、代码实现建议、测试分析和文档复核。项目的功能取舍、代码审核、运行验证、测试执行和最终交付由项目负责人确认。
