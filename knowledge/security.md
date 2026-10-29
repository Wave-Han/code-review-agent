# 安全审查规则

## 硬编码密钥（CRITICAL）
- 不允许在源代码中硬编码 API Key、密码、Token
- 搜索模式：password、secret、api_key、token、credential

## SQL 注入（CRITICAL）
- 不允许使用字符串拼接构造 SQL 查询
- 必须使用参数化查询

## 命令注入（CRITICAL）
- 不允许使用 os.system 执行用户输入
- 必须使用参数列表形式调用外部命令

## 不安全的随机数（HIGH）
- 安全相关场景不允许使用 random 模块
- 必须使用 secrets 模块

## 异常处理（MEDIUM）
- 不允许空的 except 块
- 不允许过于宽泛的 except Exception
