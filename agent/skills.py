"""
Skills 层 — 领域知识的封装与检索

对应图片知识点：
- 图1：Skills（技能层）
- 图2：RAG（检索增强生成）
- 图3：文档隔离（按主题拆分知识库）
"""

import os


KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")


def load_skill(topic: str) -> str:
    """按主题加载知识文件（RAG 检索）。对应图3的文档隔离策略。"""
    topic_map = {
        "security": "security.md",
        "style": "style.md",
        "performance": "performance.md",
        "all": None,
    }
    if topic == "all":
        return load_all_skills()
    filename = topic_map.get(topic)
    if not filename:
        available = ", ".join(topic_map.keys())
        return f"未知主题 '{topic}'。可用主题: {available}"
    filepath = os.path.join(KNOWLEDGE_DIR, filename)
    if not os.path.exists(filepath):
        return f"知识文件不存在: {filepath}"
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def load_all_skills() -> str:
    """加载所有知识文件。"""
    parts = []
    for filename in sorted(os.listdir(KNOWLEDGE_DIR)):
        if filename.endswith(".md"):
            filepath = os.path.join(KNOWLEDGE_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            topic = filename.replace(".md", "")
            parts.append(f"=== {topic.upper()} 审查规则 ===\n{content}")
    return "\n\n".join(parts)


def get_review_prompt(skills_content: str, file_content: str, filename: str) -> str:
    """构建审查 Prompt（注入 RAG 知识）。对应图2的检索→注入→回答流程。"""
    return f"""你是一个专业的代码审查员。请根据以下审查规则，审查给定的代码文件。

## 审查规则（来自知识库）

{skills_content}

## 待审查的代码文件: {filename}

{file_content}

## 审查要求

请按以下格式输出审查结果：

1. 对每个发现的问题，标注严重级别：
   - CRITICAL：安全漏洞、数据丢失风险（必须立即修复）
   - HIGH：功能 Bug、性能问题（应该修复）
   - MEDIUM：代码可读性、命名问题（建议修复）
   - LOW：代码风格、注释完善（可选改进）

2. 每个问题包含：
   - 严重级别
   - 文件名和行号
   - 问题描述
   - 修复建议

3. 最后给出总结：
   - 问题总数统计
   - 是否建议通过审查
"""
