# code-review-agent

AI 代码审查 Agent(Python),配套**评估驱动改进(Eval-Driven Improvement)** 完整实践:评测集设计 → 基线 → 定向改进 → 同集复测 → 归因。离线可运行。

## 核心交付:评估报告

👉 **[eval/eval_report.md](eval/eval_report.md)** — 完整评估报告,全部数字来自真实运行

| 指标(miss=0,30 用例 × 5 次) | 基线 | 改进后 |
|---|---|---|
| Precision | 90.0% | **100.0%** |
| Recall | 100% | **100%**(零损失) |
| F1 | 90.0% | **100.0%** |

改进手段:上下文感知豁免(测试类/main/return 字面量),**每个豁免配"正例仍报"回归钉**防误伤。噪声实验(30% 随机漏检)下一致性 +10pp,且可机制级精确归因(3/30 用例从随机波动转为确定)。

## 评测集设计(v2,30 条 Java 用例)

| 构成 | 数量 | 压力方向 |
|---|---|---|
| 缺陷用例(密钥/注入/空catch/调试输出,含多重缺陷) | 20 | Recall |
| 干净对照 | 6 | Precision |
| 陷阱用例(长得像缺陷的合法代码) | 4 | Precision |

## 运行

```bash
python -m pytest tests/                     # 豁免+回归钉 6 项
python eval/run_eval.py --suite v2          # 主结果(P/R/F1/一致性)
python eval/run_eval.py --suite v2 --miss 0.3   # 噪声实验
python eval/run_eval.py --suite v1          # Python 6 用例回归集
```

## 方法论说明(诚实边界)

- 离线 Detector 是真实 Agent 的**确定性替身**(regex 规则引擎),用于可复现地迭代评估方法本身;数字不可外推为线上 LLM 准确率
- `miss_prob` 注入漏检概率,模拟 LLM 非确定性 → 一致性研究(单次评估无统计意义的实证)
- 宏平均口径下噪声加大 Precision 反升的反直觉现象 → 聚合方式是设计决策,报数必须注明口径

## 目录

```
agent/      Agent 核心(工具/hook/skill 模拟)
eval/       评估框架 + v1/v2 评测集 + eval_report.md
knowledge/  审查知识库
sample_code/ 待审查样本(含刻意缺陷)
tests/      豁免与回归钉单元测试
```
