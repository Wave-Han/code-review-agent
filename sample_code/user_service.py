"""示例代码 — 包含多种问题用于测试 Code Review Agent"""


import os
import random

# CRITICAL: 硬编码密钥
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"

# HIGH: 可变全局变量
user_cache = {}


def get_user(user_id):
    if user_id:
        if user_id in user_cache:
            data = user_cache[user_id]
            if data:
                if data.get("active"):
                    if data.get("premium"):
                        return data
                    else:
                        return data
                else:
                    return None
            else:
                return None
        else:
            result = query_db("SELECT * FROM users WHERE id = " + user_id)  # CRITICAL: SQL注入
            if result:
                user_cache[user_id] = result
                return result
            else:
                return None
    else:
        return None


def query_db(sql):
    session_id = random.randint(1000, 9999)  # HIGH: 不安全随机数
    print(f"Executing: {sql} with session {session_id}")
    return {"id": 1, "name": "test", "active": True, "premium": True}


def send_notification(email, message):
    os.system(f"echo '{message}' | mail -s 'Notification' {email}")  # CRITICAL: 命令注入


def generate_token():
    return str(random.randint(100000, 999999))  # HIGH: 不安全随机数


def process_users(user_ids):
    results = []
    for uid in user_ids:
        user = query_db("SELECT * FROM users WHERE id = " + str(uid))  # HIGH: N+1
        log_msg = "Processing user: " + str(uid) + " name: " + str(user.get("name"))  # MEDIUM: 字符串拼接
        print(log_msg)
        results.append(user)
    return results


def validate_input(data):
    try:
        value = int(data)
    except:  # MEDIUM: 空 except
        value = 0
    return value


# LOW: 调试语句
print("Module loaded")
# LOW: 注释掉的代码
# old_function()
