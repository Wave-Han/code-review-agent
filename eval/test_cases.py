"""
测试集 - 评估的核心数据

评估的好坏完全取决于测试集质量。每个用例含:
- code: 待审查代码（合成样本）
- ground_truth: 真实存在的问题（标准答案）
"""

# 每个问题: (类别, 严重级别)

TEST_CASES = [
    {
        "id": "TC1_clean",
        "description": "干净代码，应0个问题",
        "code": (
            "def add(a, b):\n"
            "    return a + b\n"
        ),
        "ground_truth": [],
    },
    {
        "id": "TC2_hardcoded_secret",
        "description": "硬编码密钥",
        "code": (
            "API_KEY = 'sk-1234567890abcdef'\n"
            "def get_data():\n"
            "    return request(API_KEY)\n"
        ),
        "ground_truth": [("hardcoded_secret", "CRITICAL")],
    },
    {
        "id": "TC3_sql_injection",
        "description": "SQL注入",
        "code": (
            "def get_user(name):\n"
            "    sql = \"SELECT * FROM users WHERE name='\" + name + \"'\"\n"
            "    return db.execute(sql)\n"
        ),
        "ground_truth": [("sql_injection", "CRITICAL")],
    },
    {
        "id": "TC4_empty_except",
        "description": "空except吞错误",
        "code": (
            "def parse(s):\n"
            "    try:\n"
            "        return int(s)\n"
            "    except:\n"
            "        pass\n"
        ),
        "ground_truth": [("empty_except", "MEDIUM")],
    },
    {
        "id": "TC5_debug_print",
        "description": "调试print语句",
        "code": (
            "def process(data):\n"
            "    print('debug:', data)\n"
            "    return data * 2\n"
        ),
        "ground_truth": [("debug_print", "LOW")],
    },
    {
        "id": "TC6_multi_issues",
        "description": "多重问题（密钥+注入+空except）",
        "code": (
            "PASSWORD = 'admin123'\n"
            "def login(u, p):\n"
            "    sql = \"SELECT * FROM u WHERE name='\" + u + \"'\"\n"
            "    try:\n"
            "        return db.execute(sql)\n"
            "    except:\n"
            "        pass\n"
        ),
        "ground_truth": [
            ("hardcoded_secret", "CRITICAL"),
            ("sql_injection", "CRITICAL"),
            ("empty_except", "MEDIUM"),
        ],
    },
]


def get_case(case_id):
    for c in TEST_CASES:
        if c["id"] == case_id:
            return c
    raise KeyError(f"未找到测试用例: {case_id}")
