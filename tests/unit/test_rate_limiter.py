#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
速率限制测试模块
"""

import unittest
import time
import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.infrastructure.security.rate_limiter import (
  RateLimiter,
  RateLimitConfig,
  RateLimitEntry,
  RateLimitStrategy,
  RateLimitExceededError,
  RateLimitMiddleware,
  get_rate_limiter
)


class TestRateLimitConfig(unittest.TestCase):
  """速率限制配置测试类"""

  def test_default_config(self):
    """测试默认配置"""
    config = RateLimitConfig()

    self.assertEqual(config.max_requests, 100)
    self.assertEqual(config.window_seconds, 60)
    self.assertEqual(config.block_duration_seconds, 300)
    self.assertEqual(config.message, "Too many requests")

  def test_custom_config(self):
    """测试自定义配置"""
    config = RateLimitConfig(
      max_requests=50,
      window_seconds=30,
      block_duration_seconds=600,
      strategy=RateLimitStrategy.TOKEN_BUCKET
    )

    self.assertEqual(config.max_requests, 50)
    self.assertEqual(config.window_seconds, 30)
    self.assertEqual(config.block_duration_seconds, 600)
    self.assertEqual(config.strategy, RateLimitStrategy.TOKEN_BUCKET)


class TestRateLimitEntry(unittest.TestCase):
  """速率限制条目测试类"""

  def setUp(self):
    """设置测试环境"""
    self.config = RateLimitConfig(max_requests=5, window_seconds=60)
    self.entry = RateLimitEntry(self.config)

  def test_is_blocked_false(self):
    """测试未封禁状态"""
    self.assertFalse(self.entry.is_blocked())

  def test_get_remaining_requests(self):
    """测试剩余请求数"""
    self.assertEqual(self.entry.get_remaining_requests(), 5)

    # 添加一些请求
    for i in range(3):
      self.entry.record_request()

    self.assertEqual(self.entry.get_remaining_requests(), 2)

  def test_record_request_allowed(self):
    """测试记录请求（允许）"""
    allowed, remaining, blocked_for = self.entry.record_request()

    self.assertTrue(allowed)
    self.assertEqual(remaining, 4)
    self.assertIsNone(blocked_for)

  def test_record_request_exceeds_limit(self):
    """测试超过限制后封禁"""
    # 发送超过限制的请求
    for i in range(5):
      self.entry.record_request()

    # 下一个请求应该被封禁
    allowed, remaining, blocked_for = self.entry.record_request()

    self.assertFalse(allowed)
    self.assertEqual(remaining, 0)
    self.assertIsNotNone(blocked_for)
    self.assertTrue(self.entry.is_blocked())


class TestRateLimiter(unittest.TestCase):
  """速率限制器测试类"""

  def setUp(self):
    """设置测试环境"""
    self.config = RateLimitConfig(max_requests=3, window_seconds=60)
    self.limiter = RateLimiter(default_config=self.config)

  def test_check_rate_limit_allowed(self):
    """测试速率限制检查（允许）"""
    allowed, remaining, blocked_for = self.limiter.check_rate_limit("client1")

    self.assertTrue(allowed)
    self.assertEqual(remaining, 2)
    self.assertIsNone(blocked_for)

  def test_check_rate_limit_exceeded(self):
    """测试速率限制检查（超出）"""
    # 发送3个请求（达到限制）
    for i in range(3):
      self.limiter.check_rate_limit("client2")

    # 下一个请求应该被拒绝
    allowed, remaining, blocked_for = self.limiter.check_rate_limit("client2")

    self.assertFalse(allowed)
    self.assertEqual(remaining, 0)
    self.assertIsNotNone(blocked_for)

  def test_is_allowed(self):
    """测试 is_allowed 方法"""
    self.assertTrue(self.limiter.is_allowed("client3"))

    # 达到限制
    for i in range(3):
      self.limiter.is_allowed("client3")

    self.assertFalse(self.limiter.is_allowed("client3"))

  def test_reset_specific_client(self):
    """测试重置特定客户端"""
    # 消耗请求
    for i in range(3):
      self.limiter.check_rate_limit("client4")

    # 重置该客户端
    self.limiter.reset("client4")

    # 应该可以重新请求（check_rate_limit会消耗1个请求，所以剩余2）
    allowed, remaining, _ = self.limiter.check_rate_limit("client4")
    self.assertTrue(allowed)
    self.assertEqual(remaining, 2)

  def test_reset_all(self):
    """测试重置所有客户端"""
    # 多个客户端消耗请求
    for i in range(3):
      self.limiter.check_rate_limit(f"client{i}")

    # 重置所有
    self.limiter.reset()

    # 所有客户端应该可以重新请求
    for i in range(3):
      allowed, remaining, _ = self.limiter.check_rate_limit(f"client{i}")
      self.assertTrue(allowed)

  def test_get_stats(self):
    """测试获取统计信息"""
    # 发送一些请求
    self.limiter.check_rate_limit("client5")
    self.limiter.check_rate_limit("client5")
    self.limiter.check_rate_limit("client6")

    stats = self.limiter.get_stats()

    self.assertIn("client5", stats)
    self.assertIn("client6", stats)
    self.assertEqual(stats["client5"]["request_count"], 2)


class TestGetRateLimiter(unittest.TestCase):
  """获取速率限制器测试类"""

  def test_get_rate_limiter(self):
    """测试获取全局速率限制器"""
    limiter = get_rate_limiter()
    self.assertIsInstance(limiter, RateLimiter)

    # 应该返回同一个实例
    limiter2 = get_rate_limiter()
    self.assertEqual(limiter, limiter2)


class TestRateLimitMiddleware(unittest.TestCase):
  """速率限制中间件测试类"""

  def setUp(self):
    """设置测试环境"""
    config = RateLimitConfig(max_requests=2, window_seconds=60)
    self.limiter = RateLimiter(default_config=config)
    self.middleware = RateLimitMiddleware(limiter=self.limiter)

  def test_check_and_wait_allowed(self):
    """测试检查并等待（允许）"""
    allowed = self.middleware.check_and_wait("client7")
    self.assertTrue(allowed)

  def test_check_and_wait_blocked(self):
    """测试检查并等待（被封禁）"""
    # 达到限制
    for i in range(2):
      self.middleware.check_and_wait("client8")

    # 下一个应该被阻止
    allowed = self.middleware.check_and_wait("client8")
    self.assertFalse(allowed)


if __name__ == "__main__":
  unittest.main()
