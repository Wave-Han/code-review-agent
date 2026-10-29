"""
高级 Claude API 实战 - 演示 5 大生产级特性

每个 demo: 离线可演示(无key用模拟) / 在线可真实调用(配key)

5大特性:
1. Streaming   流式输出 - 边生成边显示
2. Caching     提示缓存 - 重复上下文省90%
3. Thinking    扩展思考 - 复杂推理先想后答
4. Vision      视觉     - 分析图片
5. Batches     批处理   - 批量任务省50%

运行:
  python learn_advanced_api.py            # 离线演示
  set ANTHROPIC_API_KEY=your-key
  python learn_advanced_api.py --live     # 在线真实运行
"""

import os
import sys
import time
import base64


def get_client():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return None
    import anthropic
    return anthropic.Anthropic(api_key=key)


MODEL = "claude-sonnet-4-20250514"


def demo_streaming(live=False):
    print("\n" + "=" * 50)
    print("Demo 1: Streaming 流式输出")
    print("=" * 50)
    print("效果: 答案一个个蹦出来，不用等全部生成完\n")
    if not live:
        print("[离线模拟] ", end="")
        for ch in "Claude 流式输出就像打字机一样...":
            print(ch, end="", flush=True)
            time.sleep(0.03)
        print("\n  >> 真实代码: with client.messages.stream(...) as stream:")
        return
    client = get_client()
    with client.messages.stream(
        model=MODEL, max_tokens=100,
        messages=[{"role": "user", "content": "用一句话解释什么是 Agent"}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print()


LARGE_RULES = (
    "# 安全审查规则 (模拟一个大知识库)\n"
    + "\n".join(f"规则{i}: 检查项目{i}的安全问题..." for i in range(1, 50))
)


def demo_caching(live=False):
    print("\n" + "=" * 50)
    print("Demo 2: Prompt Caching 提示缓存 (省90%)")
    print("=" * 50)
    print(f"场景: 每次都带 {len(LARGE_RULES)} 字符的固定规则\n")
    if not live:
        print("[离线模拟]")
        print("  第1次: cache_creation=1200 tokens (首次写入, 正常计费)")
        print("  第2次: cache_read=1200 tokens (命中缓存, 只算10%!)")
        print("  >> 真实代码: system=[{..., 'cache_control': {'type':'ephemeral'}}]")
        return
    client = get_client()
    cached_system = [{"type": "text", "text": LARGE_RULES,
                      "cache_control": {"type": "ephemeral"}}]
    for i in range(1, 3):
        msg = client.messages.create(
            model=MODEL, max_tokens=50, system=cached_system,
            messages=[{"role": "user", "content": f"第{i}个问题: 简单回答"}],
        )
        u = msg.usage
        print(f"  第{i}次: cache_read={u.cache_read_input_tokens}, "
              f"cache_creation={u.cache_creation_input_tokens}")


def demo_thinking(live=False):
    print("\n" + "=" * 50)
    print("Demo 3: Extended Thinking 扩展思考")
    print("=" * 50)
    print("场景: 复杂推理任务，让Claude先想后答\n")
    if not live:
        print("[离线模拟]")
        print("  [thinking] 先分析问题... 考虑边界... 验证逻辑...")
        print("  [text] 最终答案: ...")
        print("  >> 真实代码: thinking={'type':'enabled','budget_tokens':10000}")
        return
    client = get_client()
    msg = client.messages.create(
        model=MODEL, max_tokens=16000,
        thinking={"type": "enabled", "budget_tokens": 5000},
        messages=[{"role": "user", "content": "设计一个分布式锁，分析3种方案的权衡"}],
    )
    for block in msg.content:
        if block.type == "thinking":
            print(f"  [思考] {block.thinking[:150]}...")
        elif block.type == "text":
            print(f"  [答案] {block.text[:150]}...")


def demo_vision(live=False):
    print("\n" + "=" * 50)
    print("Demo 4: Vision 视觉 (多模态)")
    print("=" * 50)
    print("场景: 发图片给Claude分析\n")
    print("  content = [{'type':'image','source':{'type':'base64',")
    print("    'media_type':'image/png','data': img_b64}}, {'type':'text','text':'...'}]")
    if not live:
        print("  [离线模式] (在线模式才真正发图片)")
        return
    img_path = "../微信图片_2026-05-03_000735_632.png"
    if not os.path.exists(img_path):
        print("  (未找到示例图片, 跳过)")
        return
    with open(img_path, "rb") as f:
        img_b64 = base64.standard_b64encode(f.read()).decode()
    client = get_client()
    msg = client.messages.create(
        model=MODEL, max_tokens=300,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}},
            {"type": "text", "text": "用一句话描述这张图的内容"},
        ]}],
    )
    print(f"  分析: {msg.content[0].text}")


def demo_batches(live=False):
    print("\n" + "=" * 50)
    print("Demo 5: Batches 批处理 (省50%)")
    print("=" * 50)
    print("场景: 批量处理100个测试用例\n")
    if not live:
        print("[离线模拟]")
        print("  batch = client.messages.batches.create(requests=[100个请求])")
        print("  >> 异步处理, 24小时内返回, 价格减半")
        print("  >> 适用: 评估工具批量跑测试集 / 离线标注")
        return
    client = get_client()
    prompts = [f"分类这段文本的情感: 文本{i}" for i in range(3)]
    batch = client.messages.batches.create(
        requests=[{"custom_id": f"req-{i}",
                   "params": {"model": MODEL, "max_tokens": 50,
                              "messages": [{"role": "user", "content": p}]}}
                  for i, p in enumerate(prompts)],
    )
    print(f"  批次已提交: {batch.id}")


def main():
    live = "--live" in sys.argv
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    mode = "在线真实调用" if (live and has_key) else "离线模拟"
    print(f"\n高级 Claude API 实战演示 | 模式: {mode}")
    print("(配 ANTHROPIC_API_KEY 并加 --live 可真实运行)")

    demo_streaming(live and has_key)
    demo_caching(live and has_key)
    demo_thinking(live and has_key)
    demo_vision(live and has_key)
    demo_batches(live and has_key)

    print("\n" + "=" * 50)
    print("5大特性速查:")
    print("  Streaming  流式  - 体验好, 价格持平")
    print("  Caching    缓存  - 省最多(90%), 固定上下文必备")
    print("  Thinking   思考  - 复杂推理质量高, 成本升(值得)")
    print("  Vision     视觉  - 多模态, 价格持平")
    print("  Batches    批处理- 批量省50%, 异步")
    print("=" * 50)


if __name__ == "__main__":
    main()
