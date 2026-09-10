from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    prompt: str
    required_terms: tuple[str, ...]


CASES = (
    EvaluationCase("E-01", "把课程报告拆成可执行步骤", ("步骤", "报告")),
    EvaluationCase("E-02", "给出三天复习计划", ("第1天", "第2天", "第3天")),
    EvaluationCase("E-03", "任务已经逾期怎么办", ("优先", "截止")),
    EvaluationCase("E-04", "如何安排两门课程", ("课程", "时间")),
    EvaluationCase("E-05", "API Key 错误时怎么办", ("检查", "重试")),
    EvaluationCase("E-06", "总结学习资料的下一步", ("资料", "下一步")),
)


def score_output(case: EvaluationCase, output: str) -> dict[str, int | bool]:
    """Return reproducible offline checks; this is not a claim of model quality."""
    normalized = output.strip()
    matched = sum(term in normalized for term in case.required_terms)
    return {
        "not_empty": bool(normalized),
        "required_terms": matched,
        "required_terms_total": len(case.required_terms),
        "has_action_structure": any(marker in normalized for marker in ("1.", "第1", "第一", "先", "下一步")),
        "no_service_error": "AI 服务暂时不可用" not in normalized,
    }
