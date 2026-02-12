#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全审计日志测试模块
"""

import unittest
import os
import sys
import json
import tempfile
import shutil

# 添加项目根目录
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.infrastructure.logging.security_audit import (
  SecurityAuditLogger,
  SecurityEventType,
  get_audit_logger
)


class TestSecurityAuditLogger(unittest.TestCase):
  """安全审计日志器测试类"""

  def setUp(self):
    """设置测试环境"""
    self.test_dir = tempfile.mkdtemp()
    self.test_log_file = os.path.join(self.test_dir, "security_audit.log")
    self.audit_logger = SecurityAuditLogger(
      log_file=self.test_log_file,
      level=logging.DEBUG
    )

  def tearDown(self):
    """清理测试环境"""
    if os.path.exists(self.test_dir):
      shutil.rmtree(self.test_dir)

  def test_log_login_success(self):
    """测试登录成功日志"""
    result = self.audit_logger.log_login_success(
      user_id="user123",
      ip_address="192.168.1.100"
    )

    self.assertEqual(result["event_type"], "LOGIN_SUCCESS")
    self.assertEqual(result["user_id"], "user123")
    self.assertEqual(result["ip_address"], "192.168.1.100")
    self.assertTrue(result["success"])

  def test_log_login_failed(self):
    """测试登录失败日志"""
    result = self.audit_logger.log_login_failed(
      user_id="user123",
      ip_address="192.168.1.100",
      reason="Invalid password"
    )

    self.assertEqual(result["event_type"], "LOGIN_FAILED")
    self.assertEqual(result["user_id"], "user123")
    self.assertFalse(result["success"])
    self.assertEqual(result["details"]["reason"], "Invalid password")

  def test_log_password_change(self):
    """测试密码修改日志"""
    result = self.audit_logger.log_password_change(
      user_id="user123",
      success=True
    )

    self.assertEqual(result["event_type"], "PASSWORD_CHANGE")
    self.assertEqual(result["user_id"], "user123")
    self.assertTrue(result["success"])

  def test_log_sql_injection_attempt(self):
    """测试 SQL 注入尝试日志"""
    result = self.audit_logger.log_sql_injection_attempt(
      ip_address="192.168.1.100",
      query="SELECT * FROM users WHERE id = 1; DROP TABLE users--",
      user_id=None
    )

    self.assertEqual(result["event_type"], "SQL_INJECTION_ATTEMPT")
    self.assertFalse(result["success"])
    self.assertEqual(result["ip_address"], "192.168.1.100")
    self.assertTrue(result["details"]["blocked"])

  def test_log_sensitive_data_access(self):
    """测试敏感数据访问日志"""
    result = self.audit_logger.log_sensitive_data_access(
      user_id="admin",
      data_type="user_passwords",
      ip_address="192.168.1.100"
    )

    self.assertEqual(result["event_type"], "SENSITIVE_DATA_ACCESS")
    self.assertEqual(result["user_id"], "admin")
    self.assertEqual(result["details"]["data_type"], "user_passwords")

  def test_log_config_change(self):
    """测试配置变更日志"""
    result = self.audit_logger.log_config_change(
      user_id="admin",
      config_key="database.password",
      old_value="old_password",
      new_value="new_password"
    )

    self.assertEqual(result["event_type"], "CONFIG_CHANGE")
    self.assertEqual(result["user_id"], "admin")
    self.assertEqual(result["details"]["config_key"], "database.password")

  def test_log_encryption_failure(self):
    """测试加密失败日志"""
    result = self.audit_logger.log_encryption_failure(
      operation="encrypt",
      error="Invalid key",
      user_id="user123"
    )

    self.assertEqual(result["event_type"], "ENCRYPTION_FAILURE")
    self.assertFalse(result["success"])
    self.assertEqual(result["details"]["operation"], "encrypt")

  def test_log_file_creation(self):
    """测试日志文件创建"""
    # 创建一些日志事件
    self.audit_logger.log_login_success(user_id="user1")
    self.audit_logger.log_login_failed(user_id="user2")

    # 验证文件存在
    self.assertTrue(os.path.exists(self.test_log_file))

    # 验证日志内容
    with open(self.test_log_file, 'r', encoding='utf-8') as f:
      lines = f.readlines()
      self.assertGreaterEqual(len(lines), 2)

  def test_get_audit_logger(self):
    """测试获取全局审计日志器"""
    logger = get_audit_logger()
    self.assertIsInstance(logger, SecurityAuditLogger)


class TestSecurityEventType(unittest.TestCase):
  """安全事件类型测试类"""

  def test_event_types_exist(self):
    """测试事件类型存在"""
    self.assertIsNotNone(SecurityEventType.LOGIN_SUCCESS)
    self.assertIsNotNone(SecurityEventType.LOGIN_FAILED)
    self.assertIsNotNone(SecurityEventType.SQL_INJECTION_ATTEMPT)
    self.assertIsNotNone(SecurityEventType.CONFIG_CHANGE)

  def test_event_value(self):
    """测试事件值"""
    self.assertEqual(SecurityEventType.LOGIN_SUCCESS.value, "LOGIN_SUCCESS")
    self.assertEqual(SecurityEventType.LOGIN_FAILED.value, "LOGIN_FAILED")


if __name__ == "__main__":
  import logging
  unittest.main()
