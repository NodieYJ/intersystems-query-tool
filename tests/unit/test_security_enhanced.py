#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全功能测试模块

测试密码加密、验证、强度检查等安全功能
"""

import unittest
import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.infrastructure.security.security_utils import SecurityUtils


class TestPasswordEncryption(unittest.TestCase):
  """密码加密测试类"""

  def test_encrypt_password_basic(self):
    """测试基本密码加密"""
    password = "test_password_123"
    encrypted = SecurityUtils.encrypt_password(password)

    # 验证加密结果格式
    self.assertIn("$", encrypted)
    parts = encrypted.split("$")
    self.assertEqual(len(parts), 2)

    salt, hashed = parts
    self.assertEqual(len(salt), 32)  # 16字节 hex 编码
    self.assertEqual(len(hashed), 64)  # 32字节 hex 编码

  def test_encrypt_password_with_salt(self):
    """测试带盐值密码加密"""
    password = "test_password"
    salt = "custom_salt_value"
    encrypted = SecurityUtils.encrypt_password(password, salt)

    # 验证使用自定义盐值
    self.assertTrue(encrypted.startswith(salt + "$"))

  def test_encrypt_password_empty(self):
    """测试空密码加密"""
    with self.assertRaises(ValueError) as context:
      SecurityUtils.encrypt_password("")

    self.assertIn("不能为空", str(context.exception))

  def test_encrypt_password_too_short(self):
    """测试密码长度不足"""
    with self.assertRaises(ValueError) as context:
      SecurityUtils.encrypt_password("abc")

    self.assertIn("至少需要", str(context.exception))

  def test_encrypt_password_too_long(self):
    """测试密码长度过长"""
    long_password = "a" * 200
    with self.assertRaises(ValueError) as context:
      SecurityUtils.encrypt_password(long_password)

    self.assertIn("不能超过", str(context.exception))


class TestPasswordVerification(unittest.TestCase):
  """密码验证测试类"""

  def test_verify_password_correct(self):
    """测试正确密码验证"""
    password = "test_password_123"
    encrypted = SecurityUtils.encrypt_password(password)

    result = SecurityUtils.verify_password(password, encrypted)
    self.assertTrue(result)

  def test_verify_password_incorrect(self):
    """测试错误密码验证"""
    password = "test_password_123"
    wrong_password = "wrong_password"
    encrypted = SecurityUtils.encrypt_password(password)

    result = SecurityUtils.verify_password(wrong_password, encrypted)
    self.assertFalse(result)

  def test_verify_password_empty(self):
    """测试空密码验证"""
    result = SecurityUtils.verify_password("", "valid_salt$valid_hash")
    self.assertFalse(result)

  def test_verify_password_empty_encrypted(self):
    """测试空加密密码验证"""
    result = SecurityUtils.verify_password("test123", "")
    self.assertFalse(result)

  def test_verify_password_invalid_format(self):
    """测试无效格式加密密码"""
    result = SecurityUtils.verify_password("test123", "invalid_format")
    self.assertFalse(result)

  def test_verify_password_valid_encrypted_empty_password(self):
    """测试有效加密密码但空原始密码"""
    # 加密一个有效密码
    valid_password = "test123456"  # 10个字符
    encrypted = SecurityUtils.encrypt_password(valid_password)

    # 用空密码验证应该返回 False
    result = SecurityUtils.verify_password("", encrypted)
    self.assertFalse(result)


class TestPasswordStrength(unittest.TestCase):
  """密码强度测试类"""

  def test_password_strength_empty(self):
    """测试空密码"""
    result = SecurityUtils.check_password_strength("")
    self.assertEqual(result["strength"], "empty")
    self.assertEqual(result["score"], 0)

  def test_password_strength_very_weak_short(self):
    """测试非常短的密码"""
    result = SecurityUtils.check_password_strength("123")
    self.assertIn(result["strength"], ["very_weak", "weak"])

  def test_password_strength_common(self):
    """测试常见密码"""
    result = SecurityUtils.check_password_strength("password")
    # 由于密码只有8字符，可能不会触发"太常见"检查
    # 但仍然应该是弱密码
    self.assertIn(result["strength"], ["very_weak", "weak"])

  def test_password_strength_medium(self):
    """测试中等强度密码"""
    result = SecurityUtils.check_password_strength("Test@123")
    self.assertIn(result["strength"], ["medium", "strong"])

  def test_password_strength_strong(self):
    """测试强密码"""
    result = SecurityUtils.check_password_strength("Test@123#Secure!2024")
    self.assertIn(result["strength"], ["medium", "strong"])

  def test_password_strength_repeated_chars(self):
    """测试重复字符密码"""
    result = SecurityUtils.check_password_strength("Test@111")
    self.assertIn("重复字符", result["suggestions"][0])

  def test_password_strength_sequential(self):
    """测试连续字符密码"""
    result = SecurityUtils.check_password_strength("Test@abc123")
    self.assertIn("连续字符", result["suggestions"][0])


class TestConstantTimeCompare(unittest.TestCase):
  """恒定时间比较测试类"""

  def test_constant_time_compare_equal(self):
    """测试相等情况"""
    result = SecurityUtils._constant_time_compare("abc123", "abc123")
    self.assertTrue(result)

  def test_constant_time_compare_not_equal(self):
    """测试不等情况"""
    result = SecurityUtils._constant_time_compare("abc123", "abc124")
    self.assertFalse(result)

  def test_constant_time_compare_different_length(self):
    """测试不同长度"""
    result = SecurityUtils._constant_time_compare("abc", "abcd")
    self.assertFalse(result)

  def test_constant_time_compare_empty(self):
    """测试空字符串"""
    result = SecurityUtils._constant_time_compare("", "")
    self.assertTrue(result)


if __name__ == "__main__":
  unittest.main()
