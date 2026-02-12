# 安全最佳实践指南

本文档提供了 PyWindows 桌面应用程序的安全最佳实践指南。

## 目录

- [1. 密码安全](#1-密码安全)
- [2. 数据库安全](#2-数据库安全)
- [3. 输入验证](#3-输入验证)
- [4. 配置安全](#4-配置安全)
- [5. 日志与监控](#5-日志与监控)

---

## 1. 密码安全

### 1.1 密码强度要求

应用程序使用 PBKDF2-SHA256 算法进行密码加密，迭代次数为 100,000 次。

**密码强度要求**:
- 最小长度: 8 个字符
- 最大长度: 128 个字符
- 建议包含: 大写字母、小写字母、数字、特殊字符

### 1.2 密码强度检查

```python
from src.infrastructure.security.security_utils import SecurityUtils

# 检查密码强度
result = SecurityUtils.check_password_strength("MySecure@123")

# 结果示例
# {
#   "strength": "strong",      # very_weak, weak, medium, strong
#   "score": 6,                # 0-7 分
#   "suggestions": ["密码强度良好"]
# }
```

### 1.3 密码加密

```python
# 加密密码（自动生成随机盐值）
encrypted = SecurityUtils.encrypt_password("MyPassword123")

# 加密密码（使用自定义盐值）
encrypted = SecurityUtils.encrypt_password("MyPassword123", salt="custom_salt")

# 验证密码
is_valid = SecurityUtils.verify_password("MyPassword123", encrypted)
```

### 1.4 密码策略最佳实践

1. **永远不要存储明文密码**
2. **使用唯一的盐值**
3. **实施密码最小长度策略**
4. **定期更新加密算法**

---

## 2. 数据库安全

### 2.1 连接池配置

```json
{
  "database": {
    "config": {
      "maxConnections": 10,
      "connectionTimeout": 30,
      "queryTimeout": 30,
      "autoReconnect": true
    }
  }
}
```

### 2.2 查询超时

所有数据库查询都应该设置超时时间：

```python
# 执行带超时的查询
results = repository.executeQuery(
  query="SELECT * FROM users",
  params=None,
  timeout=30.0  # 30秒超时
)
```

### 2.3 SQL 注入防护

**永远使用参数化查询**：

```python
# ✅ 正确 - 参数化查询
result = data_service.get_data(
  "SELECT * FROM users WHERE id = ?",
  [user_id]
)

# ❌ 错误 - 字符串拼接
result = data_service.get_data(
  f"SELECT * FROM users WHERE id = {user_id}"
)
```

---

## 3. 输入验证

### 3.1 Schema 验证

```python
from src.business.services.data_service import InputValidator

# 验证 schema 名称
result = InputValidator.validate_schema_name("public")
# Result: ValidationResult(is_valid=True, message="Valid schema name")

# 防范 SQL 注入
result = InputValidator.validate_schema_name("test'; DROP TABLE users;--")
# Result: ValidationResult(is_valid=False, message="Invalid schema name format")
```

### 3.2 SQL 参数验证

```python
# 验证查询参数
is_valid = InputValidator.validate_sql_query_params(("test", 123))

# 检测危险模式
is_valid = InputValidator.validate_sql_query_params(("test'; DROP",))
# 返回 False，检测到危险模式
```

### 3.3 查询安全检查

```python
# 检查查询是否安全
result = InputValidator.validate_query_not_dangerous("SELECT * FROM users")
# Result: ValidationResult(is_valid=True, message="Query passed safety check")

# 检测危险查询
result = InputValidator.validate_query_not_dangerous("DROP TABLE users")
# Result: ValidationResult(is_valid=False, message="Query contains dangerous keyword: DROP")
```

**禁止的 SQL 操作**:
- `DROP` - 删除表/数据库
- `DELETE` - 删除数据
- `TRUNCATE` - 清空表
- `ALTER` - 修改表结构
- `CREATE` - 创建表/数据库
- `INSERT` - 插入数据
- `UPDATE` - 更新数据
- `EXEC` / `EXECUTE` - 执行存储过程
- `xp_` / `sp_` - 系统存储过程前缀

---

## 4. 配置安全

### 4.1 服务配置文件

使用 `config/services.json` 进行服务配置：

```json
{
  "version": "1.0",
  "services": {
    "security": {
      "classPath": "src.infrastructure.security.security_utils.SecurityUtils",
      "enabled": true,
      "config": {
        "encryptionAlgorithm": "PBKDF2-SHA256",
        "hashIterations": 100000
      }
    }
  }
}
```

### 4.2 敏感信息保护

1. **不要在代码中硬编码密码**
2. **使用环境变量存储敏感信息**
3. **加密配置文件中的敏感字段**

### 4.3 配置验证

```python
from src.infrastructure.utils.service_factory import ServiceRegistry

# 加载服务配置
ServiceRegistry.load_from_json_file("config/services.json")

# 获取服务配置
config = ServiceRegistry.get_config("security")
```

---

## 5. 日志与监控

### 5.1 安全日志级别

| 级别 | 场景 |
|------|------|
| `DEBUG` | 密码加密/验证操作 |
| `INFO` | 登录成功、配置加载 |
| `WARNING` | 密码强度不足、登录失败、SQL注入尝试 |
| `ERROR` | 加密失败、数据库连接失败 |

### 5.2 安全事件监控

监控以下安全相关事件：

1. **认证事件**
   - 登录成功/失败
   - 密码修改
   - 账户锁定

2. **数据访问事件**
   - 敏感数据查询
   - 批量数据导出
   - 架构变更

3. **系统事件**
   - 配置变更
   - 服务重启
   - 异常错误

### 5.3 日志示例

```python
import logging

logger = logging.getLogger(__name__)

# 记录安全事件
logger.info("用户登录成功: user_id=123")
logger.warning(f"密码强度不足: user_id=123, score=2")
logger.error(f"密码加密失败: {str(e)}", exc_info=True)
```

---

## 安全检查清单

### 部署前检查

- [ ] cryptography 库版本 >= 3.4.8
- [ ] 密码最小长度设置为 8
- [ ] 数据库连接超时配置合理
- [ ] SQL 查询使用参数化
- [ ] 敏感配置已加密
- [ ] 日志级别设置为 INFO 或更高

### 定期检查

- [ ] 检查日志中的异常事件
- [ ] 更新依赖库版本
- [ ] 审查用户权限
- [ ] 备份配置文件
- [ ] 测试恢复流程

---

## 相关文档

- [代码审查修复指南](docs/code-review-fix-guide.md)
- [项目架构文档](docs/architecture.md)
- [数据库操作规范](docs/database-guidelines.md)
