"""
配置 — 模型路由（Model-Agnostic）

对应图片知识点：
- 图1需求3：传入 LLM 调用配置（apikey / baseurl / modelname）
- 图4：getModel('glm-5') 的模型路由设计
"""

import os


def get_model_config() -> dict:
    """获取模型配置，支持环境变量覆盖。"""
    return {
        "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
        "model": os.environ.get("REVIEW_MODEL", "claude-sonnet-4-20250514"),
        "max_tokens": int(os.environ.get("REVIEW_MAX_TOKENS", "4096")),
        "base_url": os.environ.get("ANTHROPIC_BASE_URL", None),
    }


def validate_config(config: dict) -> bool:
    """验证配置是否完整。"""
    if not config.get("api_key"):
        print("错误：未设置 ANTHROPIC_API_KEY 环境变量")
        print("请运行：set ANTHROPIC_API_KEY=your-api-key")
        return False
    return True
