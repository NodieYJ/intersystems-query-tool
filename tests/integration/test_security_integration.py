#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全功能集成测试模块

测试安全功能之间的集成和端到端场景
"""

import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.infrastructure.security.security_utils import SecurityUtils
from src.infrastructure.security.rate_limiter import RateLimiter, RateLimitConfig
from src.infrastructure.logging.security_audit import SecurityAuditLogger, SecurityEventType
from src.business.services.data_service import InputValidator, DataService


class TestSecurityIntegration(unittest.TestCase):
  """安全功能集成测试类"""

  def setUp(self):
    """设置测试环境"""
    self.test_dir = tempfile.mkdtemp()
    
    # 创建审计日志器
    self.audit_log_file = os.path.join(self.test_dir, "audit.log")
    self.audit_logger = SecurityAuditLogger(
      log_file=self.audit_log_file,
      level=10  # DEBUG
    )
    
    # 创建速率限制器
    self.rate_config = RateLimitConfig(
      max_requests=10,
      window_seconds=60
    )
    self.rate_limiter = RateLimiter(default_config=self.rate_config)

  def tearDown(self):
    """清理测试环境"""
    if os.path.exists(self.test_dir):
      shutil.rmtree(self.test_dir)

  def test_password_flow_with_audit(self):
    """测试密码流程与审计日志集成"""
    # 1. 加密密码
    password = "SecureP@ss123!"
    encrypted = SecurityUtils.encrypt_password(password)
    
    # 2. 验证密码
    self.assertTrue(SecurityUtils.verify_password(password, encrypted))
    
    # 3. 记录审计日志
    event = self.audit_logger.log_event(
      event_type=SecurityEventType.PASSWORD_CHANGE,
      user_id="test_user",
      success=True
    )
    
    # 4. 验证日志文件
    self.assertTrue(os.path.exists(self.audit_log_file))
    
    with open(self.audit_log_file, 'r', encoding='utf-8') as f:
      content = f.read()
      self.assertIn("PASSWORD_CHANGE", content)

  def test_sql_injection_detection_with_rate_limit(self):
    """测试 SQL 注入检测与速率限制集成"""
    # 1. 检测 SQL 注入
    malicious_query = "'; DROP TABLE users;--"
    result = InputValidator.validate_query_not_dangerous(malicious_query)
    
    self.assertFalse(result.is_valid)
    self.assertIn("DROP", result.message)
    
    # 2. 记录安全事件
    event = self.audit_logger.log_sql_injection_attempt(
      ip_address="192.168.1.100",
      query=malicious_query,
      user_id=None
    )
    
    self.assertEqual(event["event_type"], "SQL_INJECTION_ATTEMPT")
    
    # 3. 检查速率限制
    allowed, remaining, _ = self.rate_limiter.check_rate_limit("192.168.1.100")
    self.assertTrue(allowed)
    
    # 4. 多次尝试触发速率限制
    for i in range(9):
      self.rate_limiter.check_rate_limit("192.168.1.100")
    
    # 下一个应该被限制
    allowed, remaining, blocked_for = self.rate_limiter.check_rate_limit("192.168.1.100")
    self.assertFalse(allowed)
    self.assertIsNotNone(blocked_for)

  def test_password_strength_affects_audit(self):
    """测试密码强度与审计日志集成"""
    # 弱密码
    weak_result = SecurityUtils.check_password_strength("123")
    
    # 记录警告日志
    self.audit_logger.log_event(
      event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
      user_id="test_user",
      success=True,
      details={"reason": "Weak password", "score": weak_result["score"]}
    )
    
    # 验证日志
    with open(self.audit_log_file, 'r', encoding='utf-8') as f:
      content = f.read()
      self.assertIn("SUSPICIOUS_ACTIVITY", content)
      self.assertIn("Weak password", content)

  def test_login_flow_complete(self):
    """测试完整的登录流程"""
    user_id = "user123"
    ip_address = "192.168.1.50"
    
    # 1. 检查速率限制
    allowed, remaining, _ = self.rate_limiter.check_rate_limit(ip_address)
    self.assertTrue(allowed)
    
    # 2. 模拟登录成功
    self.audit_logger.log_login_success(user_id, ip_address)
    
    # 3. 验证日志
    with open(self.audit_log_file, 'r', encoding='utf-8') as f:
      content = f.read()
      self.assertIn("LOGIN_SUCCESS", content)
      self.assertIn(user_id, content)

  def test_brute_force_protection(self):
    """测试暴力破解保护"""
    ip_address = "10.0.0.100"
    user_id = "admin"
    
    # 模拟多次失败登录
    for i in range(5):
      self.audit_logger.log_login_failed(
        user_id=user_id,
        ip_address=ip_address,
        reason="Invalid password"
      )
    
    # 检查速率限制（应该还有剩余）
    allowed, remaining, _ = self.rate_limiter.check_rate_limit(ip_address)
    self.assertTrue(allowed)
    self.assertEqual(remaining, 4)  # 10 - 5 failed - 1 check = 4
    
    # 继续触发限制
    for i in range(10):
      self.rate_limiter.check_rate_limit(ip_address)
    
    # 应该被限制
    allowed, remaining, blocked_for = self.rate_limiter.check_rate_limit(ip_address)
    self.assertFalse(allowed)
    self.assertIsNotNone(blocked_for)

  def test_config_change_audit(self):
    """测试配置变更审计"""
    admin_id = "admin_user"
    
    # 记录配置变更
    self.audit_logger.log_config_change(
      user_id=admin_id,
      config_key="security.max_login_attempts",
      old_value=5,
      new_value=10
    )
    
    # 验证日志
    with open(self.audit_log_file, 'r', encoding='utf-8') as f:
      content = f.read()
      self.assertIn("CONFIG_CHANGE", content)
      self.assertIn("security.max_login_attempts", content)

  def test_sensitive_data_access_audit(self):
    """测试敏感数据访问审计"""
    user_id = "data_analyst"
    
    # 记录敏感数据访问
    self.audit_logger.log_sensitive_data_access(
      user_id=user_id,
      data_type="user_credentials",
      ip_address="192.168.1.200"
    )
    
    # 验证日志
    with open(self.audit_log_file, 'r', encoding='utf-8') as f:
      content = f.read()
      self.assertIn("SENSITIVE_DATA_ACCESS", content)
      self.assertIn("user_credentials", content)


class TestSecurityPerformanceIntegration(unittest.TestCase):
  """安全性能集成测试类"""

  def test_password_encryption_performance(self):
    """测试密码加密性能"""
    import time
    
    password = "Test@SecurePassword123!"
    iterations = 100
    
    # 测量加密时间
    start = time.time()
    for _ in range(iterations):
      SecurityUtils.encrypt_password(password)
    encryption_time = time.time() - start
    
    # 应该在合理时间内（100次 < 5秒）
    self.assertLess(encryption_time, 5.0)
    
    # 测量验证时间
    encrypted = SecurityUtils.encrypt_password(password)
    start = time.time()
    for _ in range(iterations):
      SecurityUtils.verify_password(password, encrypted)
    verification_time = time.time() - start
    
    # 应该在合理时间内（100次 < 1秒）
    self.assertLess(verification_time, 1.0)

  def test_rate_limiter_performance(self):
    """测试速率限制器性能"""
    import time
    
    limiter = RateLimiter(RateLimitConfig(max_requests=1000))
    iterations = 10000
    
    # 测量速率限制检查时间
    start = time.time()
    for i in range(iterations):
      limiter.check_rate_limit(f"client_{i % 100}")
    elapsed = time.time() - start
    
    # 10000次检查应该 < 1秒
    self.assertLess(elapsed, 1.0)

  def test_input_validation_performance(self):
    """测试输入验证性能"""
    import time
    
    queries = [
      "SELECT * FROM users WHERE id = ?",
      "INSERT INTO orders (user_id, product) VALUES (?, ?)",
      "UPDATE products SET price = ? WHERE id = ?",
    ] * 100
    
    start = time.time()
    for query in queries:
      InputValidator.validate_query_not_dangerous(query)
    elapsed = time.time() - start
    
    # 300次验证应该 < 1秒
    self.assertLess(elapsed, 1.0)


class TestSecurityFailureScenarios(unittest.TestCase):
  """安全失败场景测试类"""

  def setUp(self):
    """设置测试环境"""
    self.test_dir = tempfile.mkdtemp()
    self.audit_log_file = os.path.join(self.test_dir, "audit.log")
    self.audit_logger = SecurityAuditLogger(
      log_file=self.audit_log_file,
      level=10
    )

  def tearDown(self):
    """清理测试环境"""
    if os.path.exists(self.test_dir):
      shutil.rmtree(self.test_dir)

  def test_encryption_failure_audit(self):
    """测试加密失败审计"""
    # 模拟加密失败
    self.audit_logger.log_encryption_failure(
      operation="encrypt",
      error="Invalid key length",
      user_id="test_user"
    )
    
    # 验证日志
    with open(self.audit_log_file, 'r', encoding='utf-8') as f:
      content = f.read()
      self.assertIn("ENCRYPTION_FAILURE", content)
      self.assertIn("Invalid key length", content)

  def test_multiple_failed_logins_audit(self):
    """测试多次失败登录审计"""
    user_id = "hacker"
    ip_address = "1.2.3.4"
    
    # 多次失败登录
    for i in range(10):
      self.audit_logger.log_login_failed(
        user_id=user_id,
        ip_address=ip_address,
        reason=f"Attempt {i + 1}"
      )
    
    # 验证所有失败都被记录
    with open(self.audit_log_file, 'r', encoding='utf-8') as f:
      content = f.read()
      count = content.count("LOGIN_FAILED")
      self.assertEqual(count, 10)

  def test_blocked_ip_logged(self):
    """测试被封禁 IP 的日志记录"""
    limiter = RateLimiter(RateLimitConfig(
      max_requests=3,
      window_seconds=60,
      block_duration_seconds=300
    ))
    
    ip_address = "5.6.7.8"
    
    # 触发封禁
    for i in range(3):
      limiter.check_rate_limit(ip_address)
    
    # 验证被封禁
    allowed, remaining, blocked_for = limiter.check_rate_limit(ip_address)
    self.assertFalse(allowed)
    self.assertIsNotNone(blocked_for)


if __name__ == "__main__":
  unittest.main()
