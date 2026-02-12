# PyWindows 安全功能示例

本文档提供安全功能的使用示例。

## 目录

- [1. 密码安全](#1-密码安全)
- [2. 输入验证](#2-输入验证)
- [3. 速率限制](#3-速率限制)
- [4. 安全审计](#4-安全审计)
- [5. 监控指标](#5-监控指标)

---

## 1. 密码安全

### 1.1 基本使用

```python
from src.infrastructure.security.security_utils import SecurityUtils

# 加密密码
password = "MySecure@Password123!"
encrypted = SecurityUtils.encrypt_password(password)
print(f"加密后: {encrypted}")

# 验证密码
is_valid = SecurityUtils.verify_password(password, encrypted)
print(f"验证结果: {is_valid}")  # True

# 检查密码强度
strength = SecurityUtils.check_password_strength(password)
print(f"强度: {strength['strength']}")  # strong
print(f"分数: {strength['score']}")  # 6
```

### 1.2 使用自定义盐值

```python
from src.infrastructure.security.security_utils import SecurityUtils

# 使用自定义盐值
custom_salt = "my_custom_salt_value"
encrypted = SecurityUtils.encrypt_password("password123", salt=custom_salt)

# 验证时需要相同的盐值
is_valid = SecurityUtils.verify_password("password123", encrypted)
```

### 1.3 密码强度策略

```python
from src.infrastructure.security.security_utils import SecurityUtils

# 强密码示例
strong_password = "MyStr0ng!@#Password$2024"
result = SecurityUtils.check_password_strength(strong_password)
# 结果: {'strength': 'strong', 'score': 7, 'suggestions': ['密码强度良好']}

# 弱密码示例
weak_password = "123456"
result = SecurityUtils.check_password_strength(weak_password)
# 结果: {'strength': 'very_weak', 'score': 0, 'suggestions': ['密码太常见', '包含连续字符']}
```

---

## 2. 输入验证

### 2.1 Schema 验证

```python
from src.business.services.data_service import InputValidator

# 验证 schema 名称
result = InputValidator.validate_schema_name("public")
print(f"有效: {result.is_valid}")  # True
print(f"净化后: {result.sanitized_value}")  # public

# 防范 SQL 注入
malicious = "test'; DROP TABLE users;--"
result = InputValidator.validate_schema_name(malicious)
print(f"有效: {result.is_valid}")  # False
print(f"消息: {result.message}")  # Invalid schema name format
```

### 2.2 SQL 查询验证

```python
from src.business.services.data_service import InputValidator

# 安全查询
safe_query = "SELECT * FROM users WHERE id = ?"
result = InputValidator.validate_query_not_dangerous(safe_query)
print(f"安全: {result.is_valid}")  # True

# 危险查询
dangerous_query = "DROP TABLE users"
result = InputValidator.validate_query_not_dangerous(dangerous_query)
print(f"安全: {result.is_valid}")  # False
print(f"消息: {result.message}")  # Query contains dangerous keyword: DROP
```

### 2.3 参数验证

```python
from src.business.services.data_service import InputValidator

# 验证参数
valid_params = ("user123", 42, True, None)
is_valid = InputValidator.validate_sql_query_params(valid_params)
print(f"有效: {is_valid}")  # True

# 检测危险模式
dangerous_params = ("test'; DROP TABLE users--",)
is_valid = InputValidator.validate_sql_query_params(dangerous_params)
print(f"有效: {is_valid}")  # False
```

---

## 3. 速率限制

### 3.1 基本使用

```python
from src.infrastructure.security.rate_limiter import RateLimiter, RateLimitConfig

# 创建速率限制器
config = RateLimitConfig(
  max_requests=10,  # 10次请求
  window_seconds=60,  # 在60秒内
  block_duration_seconds=300  # 封禁5分钟
)
limiter = RateLimiter(default_config=config)

# 检查请求
client_id = "192.168.1.100"
allowed, remaining, blocked_for = limiter.check_rate_limit(client_id)

print(f"允许: {allowed}")  # True
print(f"剩余: {remaining}")  # 9
print(f"封禁时间: {blocked_for}")  # None

# 超过限制后
allowed, remaining, blocked_for = limiter.check_rate_limit(client_id)
print(f"允许: {allowed}")  # False
print(f"剩余: {remaining}")  # 0
print(f"封禁时间: {blocked_for}")  # 300.0 (5分钟)
```

### 3.2 重置限制

```python
# 重置特定客户端
limiter.reset("192.168.1.100")

# 重置所有客户端
limiter.reset()
```

### 3.3 获取统计信息

```python
stats = limiter.get_stats()
print(f"客户端数: {len(stats)}")
for client_id, info in stats.items():
  print(f"  {client_id}: {info['request_count']} 请求")
```

---

## 4. 安全审计

### 4.1 基本使用

```python
from src.infrastructure.logging.security_audit import (
  SecurityAuditLogger,
  SecurityEventType
)

# 创建审计日志器
logger = SecurityAuditLogger(
  log_file="logs/security_audit.log",
  level=10  # DEBUG
)

# 记录登录成功
logger.log_login_success(
  user_id="user123",
  ip_address="192.168.1.100"
)

# 记录登录失败
logger.log_login_failed(
  user_id="user123",
  ip_address="192.168.1.100",
  reason="Invalid password"
)

# 记录 SQL 注入尝试
logger.log_sql_injection_attempt(
  ip_address="1.2.3.4",
  query="'; DROP TABLE users;--"
)

# 记录敏感数据访问
logger.log_sensitive_data_access(
  user_id="admin",
  data_type="user_passwords",
  ip_address="192.168.1.200"
)
```

### 4.2 自定义事件

```python
from src.infrastructure.logging.security_audit import SecurityAuditLogger, SecurityEventType

logger = SecurityAuditLogger()

# 记录自定义事件
logger.log_event(
  event_type=SecurityEventType.CONFIG_CHANGE,
  user_id="admin",
  details={
    "config_key": "security.max_login_attempts",
    "old_value": 5,
    "new_value": 10
  }
)
```

---

## 5. 监控指标

### 5.1 记录指标

```python
from monitoring.security_metrics import (
  record_login_attempt,
  record_sql_injection_attempt,
  record_password_strength,
  record_rate_limit_hit,
  record_query_validation
)

# 记录登录尝试
record_login_attempt(success=True, user_id="user123")
record_login_attempt(success=False, user_id="user123")

# 记录 SQL 注入尝试
record_sql_injection_attempt(ip_address="1.2.3.4")

# 记录密码强度
record_password_strength(score=6)

# 记录速率限制命中
record_rate_limit_hit(client_id="192.168.1.100")

# 记录查询验证
record_query_validation(result=True, query_type="SELECT")
record_query_validation(result=False, query_type="DROP")
```

### 5.2 获取指标摘要

```python
from monitoring.security_metrics import get_metrics_collector

collector = get_metrics_collector()
summary = collector.get_summary()
print(f"计数器: {summary['total_counters']}")
print(f"仪表: {summary['total_gauges']}")
print(f"直方图: {summary['total_histograms']}")
```

---

## 完整示例

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全功能完整示例
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.infrastructure.security.security_utils import SecurityUtils
from src.infrastructure.security.rate_limiter import RateLimiter, RateLimitConfig
from src.infrastructure.logging.security_audit import SecurityAuditLogger
from src.business.services.data_service import InputValidator

def main():
  print("=" * 60)
  print("PyWindows 安全功能示例")
  print("=" * 60)
  
  # 1. 密码安全
  print("\n1. 密码安全")
  password = "Test@SecurePassword123!"
  encrypted = SecurityUtils.encrypt_password(password)
  print(f"   加密: {encrypted[:50]}...")
  print(f"   验证: {SecurityUtils.verify_password(password, encrypted)}")
  strength = SecurityUtils.check_password_strength(password)
  print(f"   强度: {strength['strength']} ({strength['score']}分)")
  
  # 2. 输入验证
  print("\n2. 输入验证")
  safe_query = "SELECT * FROM users WHERE id = ?"
  result = InputValidator.validate_query_not_dangerous(safe_query)
  print(f"   安全查询: {result.is_valid}")
  
  dangerous = "DROP TABLE users"
  result = InputValidator.validate_query_not_dangerous(dangerous)
  print(f"   危险查询: {result.is_valid} - {result.message}")
  
  # 3. 速率限制
  print("\n3. 速率限制")
  limiter = RateLimiter(RateLimitConfig(max_requests=5))
  for i in range(7):
    allowed, remaining, _ = limiter.check_rate_limit("test_ip")
    print(f"   请求 {i+1}: 允许={allowed}, 剩余={remaining}")
  
  # 4. 安全审计
  print("\n4. 安全审计")
  logger = SecurityAuditLogger(log_file="logs/demo_audit.log")
  logger.log_login_success("demo_user", "127.0.0.1")
  print(f"   已记录登录事件")
  
  print("\n" + "=" * 60)
  print("示例完成!")
  print("=" * 60)

if __name__ == "__main__":
  main()
```

运行示例:
```bash
python docs/examples/security_example.py
```
