"""
Agent 核心 — ReAct 循环

对应图片知识点：
- 图2：ReAct（Reasoning + Acting）循环
- 图2：Extended Thinking（深度思考）
- 图2：Human-in-the-Loop（人机协作）
- 图5：maxTurns 限制（防止死循环）
"""

import anthropic
from .tools import TOOL_DEFINITIONS, execute_tool
from .skills import load_skill, get_review_prompt
from .hooks import pre_review_hook, post_review_hook


class CodeReviewAgent:
    """代码审查 Agent，实现 ReAct 循环。"""

    def __init__(self, config: dict, allowed_tools: list[str] | None = None):
        self.config = config
        self.allowed_tools = allowed_tools or ["read_file", "list_files", "grep_pattern"]
        self.max_turns = 10

        client_kwargs = {"api_key": config["api_key"]}
        if config.get("base_url"):
            client_kwargs["base_url"] = config["base_url"]
        self.client = anthropic.Anthropic(**client_kwargs)
        self.model = config["model"]
        self.max_tokens = config["max_tokens"]

    def review(self, target_path: str, max_turns: int = 10) -> dict:
        """主入口：审查指定路径下的代码文件。"""
        self.max_turns = max_turns
        print(f"\n{'=' * 60}")
        print(f"  Code Review Agent 启动")
        print(f"  目标: {target_path}")
        print(f"  模型: {self.model}")
        print(f"  最大轮次: {max_turns}")
        print(f"{'=' * 60}\n")

        # ReAct Step 1: Observe — 发现文件
        print("[Observe] 扫描目标目录...")
        files_result = execute_tool("list_files", {"directory": target_path, "pattern": "*.py"})
        print(files_result)

        file_paths = self._extract_file_paths(files_result, target_path)
        if not file_paths:
            return {"status": "no_files", "report": "未找到可审查的 Python 文件"}

        # ReAct Step 2: Think — 加载审查知识（RAG）
        print(f"\n[Think] 加载审查知识库...")
        skills_content = load_skill("all")
        print(f"  已加载 {skills_content.count('===')} 个主题的审查规则")

        # ReAct Step 3: Act — 逐文件审查（循环）
        all_reports = []
        turn = 0

        for filepath in file_paths:
            turn += 1
            if turn > self.max_turns:
                print(f"\n[Stop] 达到最大轮次限制 ({self.max_turns})")
                break

            print(f"\n{'─' * 40}")
            print(f"[Turn {turn}/{self.max_turns}] 审查: {filepath}")

            # Hook:Pre — 过滤不需要审查的文件
            hook_result = pre_review_hook(filepath, {})
            if hook_result.get("skip"):
                print(f"  [Hook:Pre] {hook_result['reason']}")
                continue

            # Observe — 读取文件
            file_content = execute_tool("read_file", {"path": filepath})
            if file_content.startswith("错误"):
                print(f"  [Observe] {file_content}")
                continue
            print(f"  [Observe] 已读取文件内容")

            # Think + Act — 调用 Claude 审查
            print(f"  [Think] Claude 正在分析代码...")
            review_result = self._call_claude(skills_content, file_content, filepath)

            # Hook:Post — 格式化报告
            formatted = post_review_hook(review_result)
            all_reports.append(formatted["formatted_report"])

            if formatted["has_critical"]:
                print(f"  [Human-in-the-Loop] 发现 CRITICAL 问题！")

            print(f"  [Act] 发现 {formatted['issue_count']} 个问题")

        final_report = "\n\n".join(all_reports)
        return {"status": "completed", "report": final_report}

    def _call_claude(self, skills_content: str, file_content: str, filename: str) -> str:
        """调用 Claude API 审查代码。"""
        prompt = get_review_prompt(skills_content, file_content, filename)
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except anthropic.APIError as e:
            return f"API 调用失败: {e}"

    def _extract_file_paths(self, list_result: str, base_dir: str) -> list[str]:
        """从 list_files 输出中提取文件路径。"""
        paths = []
        for line in list_result.split("\n"):
            line = line.strip()
            if ".py" in line and "字节" in line:
                path = line.split(" (")[0].strip()
                if path.endswith(".py"):
                    paths.append(path)
        return paths
