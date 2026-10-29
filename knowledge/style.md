# 代码风格规则

## 命名规范（MEDIUM）
- 函数和变量：snake_case
- 类名：PascalCase
- 常量：UPPER_SNAKE_CASE

## 函数长度（MEDIUM）
- 单个函数不超过 50 行
- 超过应拆分为更小的函数

## 嵌套深度（MEDIUM）
- 嵌套不超过 4 层
- 超过应使用 early return

## 导入规范（LOW）
- 不使用 from module import *
- 删除未使用的导入

## 注释（LOW）
- 删除被注释掉的代码
- 避免无意义的注释
