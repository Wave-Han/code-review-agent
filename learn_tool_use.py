"""
Claude API Tool Use 完整教程

对应图片知识点：
- 图1：Tools 层（工具定义）
- 图2：ReAct 循环（观察→思考→行动）
- 图4：Function Calling（程序化调用）

运行方式：
    set ANTHROPIC_API_KEY=your-key
    python learn_tool_use.py
"""

import anthropic
import json
import os
from datetime import datetime


# ============================================================
# 第1步：定义工具（对应图1 Tools 层）
# ============================================================

tools = [
    {
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，如'北京'、'上海'"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_time",
        "description": "获取指定城市的当前时间",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                }
            },
            "required": ["city"]
        }
    }
]


# ============================================================
# 第2步：实现工具函数
# ============================================================

def get_weather(city: str) -> str:
    weather_data = {
        "北京": "晴天，25°C，空气质量良好",
        "上海": "多云，28°C，湿度 75%",
        "深圳": "阵雨，30°C，湿度 85%",
    }
    return weather_data.get(city, f"{city}：暂无天气数据")


def get_time(city: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"{city} 当前时间：{now}"


tool_map = {
    "get_weather": get_weather,
    "get_time": get_time,
}


# ============================================================
# 第3步：ReAct 循环（对应图2）
# ============================================================

def run_agent(user_message: str, max_turns: int = 5) -> str:
    """
    ReAct 循环：Observe → Think → Act → 循环
    对应图5的 maxTurns 限制，防止无限循环
    """
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": user_message}]

    print(f"\n{'='*60}")
    print(f"用户: {user_message}")
    print(f"{'='*60}")

    for turn in range(max_turns):
        print(f"\n--- ReAct 第 {turn + 1} 轮 ---")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [Think] Claude 决定调用: {block.name}")
                    print(f"  [Think] 参数: {json.dumps(block.input, ensure_ascii=False)}")

                    result = tool_map[block.name](**block.input)
                    print(f"  [Act]   执行结果: {result}")

                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }]
                    })

        elif response.stop_reason == "end_turn":
            final_text = response.content[0].text
            print(f"  [回答]  {final_text}")
            return final_text

    return "达到最大轮次限制，Agent 停止。"


# ============================================================
# 第4步：运行演示
# ============================================================

if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("请先设置 API Key：")
        print("  set ANTHROPIC_API_KEY=sk-ant-xxxxx")
        exit(1)

    # 演示1：简单工具调用
    print("\n" + "=" * 60)
    print("演示1：简单工具调用")
    print("=" * 60)
    run_agent("北京今天天气怎么样？")

    # 演示2：多工具组合调用
    print("\n" + "=" * 60)
    print("演示2：多工具组合调用")
    print("=" * 60)
    run_agent("帮我看看北京和上海的天气，顺便告诉我现在几点了")

    # 演示3：不需要工具时直接回答
    print("\n" + "=" * 60)
    print("演示3：不需要工具时 Claude 直接回答")
    print("=" * 60)
    run_agent("什么是 ReAct 循环？请简单解释")
