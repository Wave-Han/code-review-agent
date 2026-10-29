"""
Hooks 层 — 工具执行前后的拦截器

对应图片知识点：
- 图1：Hooks（钩子层，PreToolUse / PostToolUse）
"""

import re
from typing import Any


def pre_review_hook(filepath: str, params: dict[str, Any]) -> dict[str, Any]:
    """审查前的预处理（PreToolUse Hook）。过滤不需要审查的文件。"""
    binary_exts = {".png", ".jpg", ".jpeg", ".gif", ".exe", ".dll", ".so", ".pyc"}
    for ext in binary_exts:
        if filepath.endswith(ext):
            return {"skip": True, "reason": f"跳过二进制文件: {filepath}"}
    skip_dirs = ["node_modules", "__pycache__", ".git", "venv"]
    for d in skip_dirs:
        if d in filepath:
            return {"skip": True, "reason": f"跳过 {d} 目录中的文件"}
    return {"skip": False, "params": params}


def post_review_hook(review_result: str) -> dict[str, Any]:
    """审查后的后处理（PostToolUse Hook）。格式化报告，按严重程度排序。"""
    issues = _extract_issues(review_result)
    sorted_issues = _sort_by_severity(issues)
    summary = _generate_summary(sorted_issues)
    formatted = _format_report(sorted_issues, summary)
    return {
        "formatted_report": formatted,
        "issue_count": len(sorted_issues),
        "has_critical": any(i["severity"] == "CRITICAL" for i in sorted_issues),
    }


def _extract_issues(text: str) -> list[dict[str, str]]:
    """从审查结果中提取问题列表。"""
    issues = []
    pattern = r"(CRITICAL|HIGH|MEDIUM|LOW)[：:]\s*(.+?)(?=\n(?=CRITICAL|HIGH|MEDIUM|LOW|$)|$)"
    matches = re.findall(pattern, text, re.DOTALL)
    for severity, description in matches:
        issues.append({"severity": severity, "description": description.strip()})
    if not issues:
        issues.append({"severity": "LOW", "description": text[:500]})
    return issues


def _sort_by_severity(issues: list[dict[str, str]]) -> list[dict[str, str]]:
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    return sorted(issues, key=lambda x: order.get(x["severity"], 99))


def _generate_summary(issues: list[dict[str, str]]) -> str:
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for issue in issues:
        sev = issue["severity"]
        if sev in counts:
            counts[sev] += 1
    total = sum(counts.values())
    recommend = "不通过" if counts["CRITICAL"] > 0 else "通过（有建议）" if total > 0 else "通过"
    return (
        f"问题总数: {total} | "
        f"CRITICAL: {counts['CRITICAL']} | HIGH: {counts['HIGH']} | "
        f"MEDIUM: {counts['MEDIUM']} | LOW: {counts['LOW']} | "
        f"审查建议: {recommend}"
    )


def _format_report(issues: list[dict[str, str]], summary: str) -> str:
    lines = ["=" * 60, "  代码审查报告", "=" * 60, ""]
    for i, issue in enumerate(issues, 1):
        lines.append(f"[{issue['severity']}] 问题 #{i}")
        lines.append(f"  {issue['description'][:200]}")
        lines.append("")
    lines.append("-" * 60)
    lines.append(f"  {summary}")
    lines.append("-" * 60)
    return "\n".join(lines)
