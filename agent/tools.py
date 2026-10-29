"""
Tools 层 — Agent 与外部世界交互的能力

对应图片知识点：
- 图1：Tool Use（工具调用）
- 图4：Function Calling（LLM 生成结构化函数调用指令）
"""

import os
import re
import glob as glob_module
from typing import Any


TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "读取指定路径的文件内容。用于审查代码时读取源文件。",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要读取的文件路径"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_files",
        "description": "列出指定目录下的文件。用于发现需要审查的代码文件。",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "要扫描的目录路径"
                },
                "pattern": {
                    "type": "string",
                    "description": "文件匹配模式，如 '*.py'，默认为所有文件"
                }
            },
            "required": ["directory"]
        }
    },
    {
        "name": "grep_pattern",
        "description": "在文件中搜索匹配指定正则表达式模式的行。用于查找潜在问题模式。",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要搜索的文件路径"
                },
                "pattern": {
                    "type": "string",
                    "description": "要搜索的正则表达式模式"
                }
            },
            "required": ["path", "pattern"]
        }
    }
]

MAX_FILE_SIZE = 100 * 1024


def execute_tool(name: str, params: dict[str, Any]) -> str:
    if name == "read_file":
        return _read_file(params["path"])
    elif name == "list_files":
        return _list_files(params["directory"], params.get("pattern", "*"))
    elif name == "grep_pattern":
        return _grep_pattern(params["path"], params["pattern"])
    else:
        return f"错误：未知工具 '{name}'"


def _read_file(path: str) -> str:
    if not os.path.exists(path):
        return f"错误：文件不存在 '{path}'"
    file_size = os.path.getsize(path)
    if file_size > MAX_FILE_SIZE:
        return f"错误：文件过大 ({file_size} 字节)，超过 {MAX_FILE_SIZE} 字节限制"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        line_count = content.count("\n") + 1
        return f"文件: {path} ({line_count} 行)\n{'=' * 40}\n{content}"
    except Exception as e:
        return f"错误：读取文件失败 '{path}': {e}"


def _list_files(directory: str, pattern: str = "*") -> str:
    if not os.path.isdir(directory):
        return f"错误：目录不存在 '{directory}'"
    matches = glob_module.glob(os.path.join(directory, "**", pattern), recursive=True)
    filtered = [
        f for f in matches
        if "__pycache__" not in f and not os.path.basename(f).startswith(".")
    ]
    if not filtered:
        return f"目录 '{directory}' 中没有匹配 '{pattern}' 的文件"
    result_lines = [f"目录 '{directory}' 中的文件 ({len(filtered)} 个)："]
    for f in sorted(filtered):
        size = os.path.getsize(f)
        result_lines.append(f"  {f} ({size} 字节)")
    return "\n".join(result_lines)


def _grep_pattern(path: str, pattern: str) -> str:
    if not os.path.exists(path):
        return f"错误：文件不存在 '{path}'"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return f"错误：读取文件失败 '{path}': {e}"
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return f"错误：无效的正则表达式 '{pattern}': {e}"
    matches = []
    for i, line in enumerate(lines, 1):
        if regex.search(line):
            matches.append(f"  行 {i}: {line.rstrip()}")
    if not matches:
        return f"文件 '{path}' 中没有匹配 '{pattern}' 的内容"
    return f"文件 '{path}' 中匹配 '{pattern}' 的行 ({len(matches)} 处)：\n" + "\n".join(matches)
