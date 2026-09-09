# TASK-008 RAG 方案与演示数据

## Status

ready

## Owner

DeepSeek Harness

## Objective

为课程资料问答设计两天内可实现的 RAG 方案，并准备演示数据。

## Scope

- 描述资料上传、文本解析、切分、索引、检索和回答流程。
- 说明课程范围过滤和答案来源展示。
- 设计资料中找不到答案时的诚实回答。
- 准备 5 个课程资料问答演示问题及预期来源。
- 评估 RAG 在当前项目中的实现优先级和降级方案。

## Allowed Changes

- `docs/rag-plan.md`
- `docs/rag-demo-dataset.md`
- `docs/vibe-log/`

## Forbidden Changes

- 不修改 `backend/`、`frontend/`、数据库结构或 API 实现。
- 不引入新的依赖。

## Acceptance Criteria

- 方案能对应 `FR-12` 至 `FR-15`。
- 明确最小可行实现和不可省略的安全边界。
- 演示问题能用于答辩验证来源引用。
