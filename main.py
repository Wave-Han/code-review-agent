"""
入口 — Agent-as-a-Service

对应图片知识点：
- 图4：spawnClaudeWithModel 的程序化调用
- 图4：--allowedTools 最小权限

用法：
  set ANTHROPIC_API_KEY=your-key
  python main.py --target ./sample_code
"""

import argparse
import sys
from config import get_model_config, validate_config
from agent import CodeReviewAgent


def main():
    parser = argparse.ArgumentParser(description="Code Review Agent")
    parser.add_argument("--target", required=True, help="要审查的代码目录路径")
    parser.add_argument("--max-turns", type=int, default=10, help="最大审查轮次")
    parser.add_argument("--tools", nargs="+", default=["read_file", "list_files"],
                        help="允许使用的工具")
    args = parser.parse_args()

    config = get_model_config()
    if not validate_config(config):
        sys.exit(1)

    agent = CodeReviewAgent(config=config, allowed_tools=args.tools)
    result = agent.review(target_path=args.target, max_turns=args.max_turns)

    print(f"\n{'=' * 60}")
    print(result["report"])
    print(f"{'=' * 60}")
    print(f"\n状态: {result['status']}")

    if "CRITICAL" in result["report"]:
        print("\n⚠ 发现严重问题！请人工确认后决定是否通过审查。")


if __name__ == "__main__":
    main()
