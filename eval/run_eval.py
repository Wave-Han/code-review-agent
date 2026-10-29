"""
评估入口 - 对应评估流程的完整5步

用法:
  python run_eval.py              # 离线完整评估
  python run_eval.py --runs 10    # 跑10次取统计
  python run_eval.py --miss 0.3   # 模拟30%漏检率(演示随机性影响)
"""

import argparse
import random
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from eval_harness import EvalHarness, Detector, LLMJudge


def print_per_case(results):
    print(f"\n{'用例':<28} {'精确率':>6} {'召回率':>6} {'F1':>6} {'级别正确':>8}")
    print("-" * 60)
    for r in results:
        print(f"{r['case_id']:<28} {r['precision']:>6.2f} {r['recall']:>6.2f} "
              f"{r['f1']:>6.2f} {r['severity_acc']:>8.2f}")


def print_summary(metrics, label=""):
    print(f"\n{'='*50}")
    if label:
        print(f"  {label}")
        print(f"{'='*50}")
    print(f"  精确率(Precision):   {metrics['precision']:.1%}   <- 报告里多少是真问题")
    print(f"  召回率(Recall):      {metrics['recall']:.1%}   <- 真问题多少被找到")
    print(f"  F1分数:              {metrics['f1']:.1%}   <- 综合指标")
    print(f"  严重级别准确率:      {metrics['severity_accuracy']:.1%}")
    print(f"  一致性(Consistency): {metrics['consistency']:.1%}   <- 多次运行稳定率")
    print(f"  测试集: {metrics['cases']} 用例 x {metrics['runs']} 次")


def main():
    parser = argparse.ArgumentParser(description="Code Review Agent 评估工具")
    parser.add_argument("--runs", type=int, default=5, help="每个用例跑几次(默认5)")
    parser.add_argument("--miss", type=float, default=0.0, help="模拟漏检率0-1(演示随机性)")
    parser.add_argument("--seed", type=int, default=42, help="随机种子(可复现)")
    parser.add_argument("--suite", choices=["v1", "v2"], default="v1",
                        help="v1=Python 6用例, v2=Java 30用例(含干净+陷阱)")
    args = parser.parse_args()

    cases = None
    if args.suite == "v2":
        from test_cases_v2 import TEST_CASES_V2
        cases = TEST_CASES_V2

    rng = random.Random(args.seed)
    harness = EvalHarness(rng=rng, cases=cases)

    print("=" * 50)
    print("  Code Review Agent 评估工具")
    print(f"  参数: runs={args.runs}, miss_prob={args.miss}, seed={args.seed}")
    print("=" * 50)

    print("\n>> 第1次运行的逐用例结果:")
    single = harness.run_once(Detector(args.miss, rng))
    print_per_case(single)

    print(f"\n>> 一致性测试: 跑 {args.runs} 次 (miss_prob={args.miss})")
    all_runs = harness.run_consistency(args.miss, runs=args.runs)
    metrics = harness.aggregate(all_runs)
    print_summary(metrics, f"评估结果 (miss={args.miss})")

    print(f"\n{'='*50}")
    print("  LLM-as-Judge 演示 (离线规则打分)")
    print(f"{'='*50}")
    judge = LLMJudge()
    from test_cases import TEST_CASES
    for case in TEST_CASES[:3]:
        det = Detector().detect(case["code"])
        report = f"发现: {[d[0] for d in det]}" if det else "无问题"
        score = judge.score_report(case["code"], report, case["ground_truth"])
        print(f"  {case['id']:<28} 裁判打分: {score}/5")

    if args.miss == 0.0:
        print(f"\n{'='*50}")
        print("  对比演示: 完美 vs 30%漏检 (展示评估的对比价值)")
        print(f"{'='*50}")
        perfect = harness.aggregate(harness.run_consistency(0.0, runs=args.runs))
        noisy = harness.aggregate(harness.run_consistency(0.3, runs=args.runs))
        print_summary(perfect, "完美检测 (miss=0.0)")
        print_summary(noisy, "有噪声检测 (miss=0.3)")
        print(f"\n  >> 召回率从 {perfect['recall']:.1%} 降到 {noisy['recall']:.1%}")
        print(f"  >> 这就是评估的价值: 改了Agent后能量化对比好坏")

    sys.exit(0)


if __name__ == "__main__":
    main()
