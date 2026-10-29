"""
评估引擎 - 评估的核心逻辑

4个关键部分（评估流程2-5步）：
1. Detector: 模拟 Agent 检测（离线规则/在线LLM）
2. Metrics: 精确率/召回率/F1
3. Consistency: 多次运行测一致性（LLM随机性）
4. LLMJudge: LLM-as-Judge 裁判模式

核心概念：精确率(Precision) vs 召回率(Recall)
- 精确率 = 报告里多少是真问题    TP/(TP+FP)  → 不报假警
- 召回率 = 真问题多少被找到      TP/(TP+FN)  → 不漏报
- 安全审查更看重召回率（漏掉漏洞代价大）
"""

import re
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from test_cases import TEST_CASES


class Detector:
    """模拟 Agent 检测。加 miss_prob 模拟 LLM 随机漏检。"""

    RULES = [
        ("hardcoded_secret", "CRITICAL",
         [r"API_KEY\s*=", r"PASSWORD\s*=", r"SECRET\s*=", r"password\s*=\s*['\"]"]),
        ("sql_injection", "CRITICAL",
         [r"SELECT.*\+.*\+", r"WHERE.*\+.*\+", r"execute\(.*\+"]),
        ("empty_except", "MEDIUM",
         [r"except\s*:\s*\n\s*pass", r"except.*:\s*pass"]),
        ("debug_print", "LOW",
         [r"print\(['\"]debug"]),
        # --- Java rules (v2 suite); kept deliberately WIDE so trap cases
        #     produce real false positives and Precision has room to improve ---
        ("hardcoded_secret", "CRITICAL",
         [r"String\s+\w*(API_KEY|apiKey|SECRET|secret|PASSWORD|password|token|TOKEN)\w*\s*=\s*['\"]"]),
        ("sql_injection", "CRITICAL",
         [r"(SELECT|INSERT|UPDATE|DELETE)[^\"%\n]*['\"]\s*\+",
          r"StringBuilder[^\n]*(SELECT|INSERT|UPDATE|DELETE)",
          r"String\.format\(\s*\"(SELECT|INSERT|UPDATE|DELETE)"]),
        ("empty_except", "MEDIUM",
         [r"catch\s*\([^)]*\)\s*\{\s*\}",
          r"catch\s*\([^)]*\)\s*\{\s*(//[^\n]*)?\s*\}",
          r"catch\s*\([^)]*\)\s*\{\s*return\s+[^;]+;\s*\}"]),
        ("debug_print", "LOW",
         [r"System\.out\.print", r"printStackTrace\(\)"]),
    ]

    # Context-aware exemptions (Day 9): file-level signals that a matched
    # pattern is legal in this context. Each entry: (signal regex, category
    # to exempt, human-readable reason). Kept deliberately narrow — an
    # over-broad exemption buys Precision by silently costing Recall.
    EXEMPTIONS = [
        (r"\bclass\s+\w*Test\b", "hardcoded_secret",
         "secret-looking constant lives in a test fixture class"),
        (r"static\s+void\s+main\s*\(", "debug_print",
         "println in a CLI main method is program output, not debug"),
        (r"return\s+\"[^\"]*(SELECT|INSERT|UPDATE|DELETE)", "sql_injection",
         "SQL keywords inside a returned string literal are documentation"),
    ]

    def __init__(self, miss_prob=0.0, rng=None):
        self.miss_prob = miss_prob
        self.rng = rng

    def detect(self, code):
        exempted = {cat for sig, cat, _ in self.EXEMPTIONS if re.search(sig, code)}
        findings = []
        for category, severity, patterns in self.RULES:
            if category in exempted:
                continue
            for pat in patterns:
                if re.search(pat, code):
                    if self.rng and self.rng.random() < self.miss_prob:
                        continue
                    findings.append((category, severity))
                    break
        return findings


class Metrics:
    """评估指标"""

    @staticmethod
    def confusion_matrix(detected, truth):
        det_set = set(d[0] for d in detected)
        truth_set = set(t[0] for t in truth)
        return {
            "tp": len(det_set & truth_set),
            "fp": len(det_set - truth_set),
            "fn": len(truth_set - det_set),
        }

    @staticmethod
    def precision(cm):
        if cm["tp"] + cm["fp"] == 0:
            return 1.0
        return cm["tp"] / (cm["tp"] + cm["fp"])

    @staticmethod
    def recall(cm):
        if cm["tp"] + cm["fn"] == 0:
            return 1.0
        return cm["tp"] / (cm["tp"] + cm["fn"])

    @staticmethod
    def f1(cm):
        p, r = Metrics.precision(cm), Metrics.recall(cm)
        return 0.0 if p + r == 0 else 2 * p * r / (p + r)

    @staticmethod
    def severity_accuracy(detected, truth):
        det_map = {d[0]: d[1] for d in detected}
        truth_map = {t[0]: t[1] for t in truth}
        correct = sum(1 for c in det_map if c in truth_map and det_map[c] == truth_map[c])
        total = sum(1 for c in det_map if c in truth_map)
        return correct / total if total > 0 else 1.0


class LLMJudge:
    """LLM-as-Judge: 离线规则打分 / 在线真实LLM裁判"""

    def __init__(self, config=None):
        self.config = config or {}

    def score_report(self, code, report, ground_truth):
        if self.config.get("api_key"):
            return self._llm_score(code, report)
        return self._rule_score(report, ground_truth)

    def _rule_score(self, report, ground_truth):
        if not ground_truth:
            return 5 if "无问题" in report or len(report) < 20 else 3
        covered = sum(1 for cat, _ in ground_truth if cat in report.lower())
        ratio = covered / len(ground_truth)
        return 5 if ratio >= 0.9 else 4 if ratio >= 0.6 else 3 if ratio >= 0.3 else 2

    def _llm_score(self, code, report):
        import anthropic
        client = anthropic.Anthropic(api_key=self.config["api_key"])
        resp = client.messages.create(
            model=self.config.get("reviewer_model", "claude-sonnet-4-20250514"),
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": f"给代码审查报告打分(1-5整数)。只返回数字。\n代码:{code[:200]}\n报告:{report[:200]}",
            }],
        )
        try:
            return int(resp.content[0].text.strip())
        except ValueError:
            return 3


class EvalHarness:
    """评估主程序：跑测试集 → 打分 → 统计"""

    def __init__(self, config=None, rng=None, cases=None):
        self.config = config or {}
        self.rng = rng
        # Injectable test suite: v1 (Python) by default, v2 (Java) via run_eval --suite v2
        self.cases = cases if cases is not None else TEST_CASES

    def run_once(self, detector):
        results = []
        for case in self.cases:
            detected = detector.detect(case["code"])
            cm = Metrics.confusion_matrix(detected, case["ground_truth"])
            results.append({
                "case_id": case["id"],
                "detected": detected,
                "ground_truth": case["ground_truth"],
                "precision": Metrics.precision(cm),
                "recall": Metrics.recall(cm),
                "f1": Metrics.f1(cm),
                "severity_acc": Metrics.severity_accuracy(detected, case["ground_truth"]),
            })
        return results

    def run_consistency(self, miss_prob, runs=5):
        all_runs = [self.run_once(Detector(miss_prob, self.rng)) for _ in range(runs)]
        return all_runs

    def aggregate(self, all_runs):
        n_cases, n_runs = len(self.cases), len(all_runs)
        count = n_cases * n_runs
        total_p = sum(r["precision"] for run in all_runs for r in run)
        total_r = sum(r["recall"] for run in all_runs for r in run)
        total_f1 = sum(r["f1"] for run in all_runs for r in run)
        total_sev = sum(r["severity_acc"] for run in all_runs for r in run)
        return {
            "precision": total_p / count,
            "recall": total_r / count,
            "f1": total_f1 / count,
            "severity_accuracy": total_sev / count,
            "consistency": self._calc_consistency(all_runs),
            "runs": n_runs,
            "cases": n_cases,
        }

    def _calc_consistency(self, all_runs):
        n_cases = len(self.cases)
        stable = 0
        for i in range(n_cases):
            results = [tuple(sorted(r["detected"])) for run in all_runs for r in [run[i]]]
            if len(set(results)) == 1:
                stable += 1
        return stable / n_cases
