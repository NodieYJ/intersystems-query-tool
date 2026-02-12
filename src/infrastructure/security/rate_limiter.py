#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
速率限制模块

提供 API 请求速率限制功能，防止暴力破解和拒绝服务攻击
"""

import time
import threading
import logging
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
  """速率限制策略"""

  SLIDING_WINDOW = "sliding_window"
  FIXED_WINDOW = "fixed_window"
  TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitConfig:
  """速率限制配置"""

  max_requests: int = 100  # 最大请求数
  window_seconds: int = 60  # 时间窗口（秒）
  strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
  block_duration_seconds: int = 300  # 封禁时长（秒）
  message: str = "Too many requests"


class RateLimitEntry:
  """速率限制条目"""

  def __init__(self, config: RateLimitConfig):
    self.config = config
    self.requests: deque = deque()
    self.blocked_until: Optional[float] = None
    self.lock = threading.Lock()

  def is_blocked(self) -> bool:
    """检查是否被封禁"""
    if self.blocked_until is None:
      return False
    return time.time() < self.blocked_until

  def get_remaining_requests(self) -> int:
    """获取剩余请求数"""
    if self.is_blocked():
      return 0

    now = time.time()
    window_start = now - self.config.window_seconds

    # 清理过期请求
    while self.requests and self.requests[0] < window_start:
      self.requests.popleft()

    return max(0, self.config.max_requests - len(self.requests))

  def record_request(self) -> Tuple[bool, int, Optional[float]]:
    """
    记录请求

    Returns:
        Tuple[是否允许, 剩余请求数, 封禁解除时间]
    """
    with self.lock:
      now = time.time()

      # 检查是否被封禁
      if self.is_blocked():
        remaining = 0
        blocked_for = self.blocked_until - now if self.blocked_until else 0
        return False, remaining, blocked_for

      # 清理过期请求
      window_start = now - self.config.max_requests
      while self.requests and self.requests[0] < window_start:
        self.requests.popleft()

      # 检查是否超过限制
      if len(self.requests) >= self.config.max_requests:
        # 触发封禁
        self.blocked_until = now + self.config.block_duration_seconds
        logger.warning(
          f"Rate limit exceeded, blocking for {self.config.block_duration_seconds}s"
        )
        return False, 0, self.config.block_duration_seconds

      # 记录请求
      self.requests.append(now)

      remaining = self.config.max_requests - len(self.requests)
      return True, remaining, None


class RateLimiter:
  """
  速率限制器

  基于客户端 IP 或用户 ID 进行速率限制
  """

  def __init__(self, default_config: Optional[RateLimitConfig] = None):
    """
    初始化速率限制器

    Args:
        default_config: 默认配置
    """
    self.default_config = default_config or RateLimitConfig()
    self.entries: Dict[str, RateLimitEntry] = {}
    self.lock = threading.Lock()

  def _get_entry(self, client_id: str) -> RateLimitEntry:
    """获取或创建速率限制条目"""
    with self.lock:
      if client_id not in self.entries:
        self.entries[client_id] = RateLimitEntry(self.default_config)
      return self.entries[client_id]

  def check_rate_limit(
    self,
    client_id: str,
    config: Optional[RateLimitConfig] = None
  ) -> Tuple[bool, int, Optional[float]]:
    """
    检查速率限制

    Args:
        client_id: 客户端 ID（IP 或用户 ID）
        config: 可选的特定配置

    Returns:
        Tuple[是否允许, 剩余请求数, 封禁解除时间]
    """
    entry = self._get_entry(client_id)

    # 如果有特定配置，使用它
    if config:
      temp_entry = RateLimitEntry(config)
      temp_entry.requests = entry.requests.copy()
      temp_entry.blocked_until = entry.blocked_until
      return temp_entry.record_request()

    return entry.record_request()

  def is_allowed(self, client_id: str) -> bool:
    """检查是否允许请求"""
    allowed, _, _ = self.check_rate_limit(client_id)
    return allowed

  def get_remaining(self, client_id: str) -> int:
    """获取剩余请求数"""
    entry = self._get_entry(client_id)
    return entry.get_remaining_requests()

  def reset(self, client_id: Optional[str] = None) -> None:
    """
    重置速率限制

    Args:
        client_id: 指定客户端 ID，为 None 则重置所有
    """
    with self.lock:
      if client_id:
        if client_id in self.entries:
          del self.entries[client_id]
      else:
        self.entries.clear()

  def get_stats(self) -> Dict[str, Dict]:
    """获取统计信息"""
    stats = {}
    for client_id, entry in self.entries.items():
      if not entry.is_blocked() and entry.requests:
        stats[client_id] = {
          "request_count": len(entry.requests),
          "remaining": entry.get_remaining_requests(),
          "is_blocked": False
        }
      elif entry.is_blocked():
        stats[client_id] = {
          "request_count": len(entry.requests),
          "remaining": 0,
          "is_blocked": True,
          "blocked_until": entry.blocked_until
        }
    return stats


class RateLimitMiddleware:
  """
  速率限制中间件

  可用于装饰函数或集成到 Web 框架
  """

  def __init__(
    self,
    limiter: Optional[RateLimiter] = None,
    default_config: Optional[RateLimitConfig] = None
  ):
    self.limiter = limiter or RateLimiter(default_config)

  def limit(
    self,
    client_id: str,
    config: Optional[RateLimitConfig] = None
  ):
    """
    速率限制装饰器

    Args:
        client_id: 客户端 ID 来源（可以是函数或字符串）

    Returns:
        装饰器函数
    """
    def decorator(func):
      def wrapper(*args, **kwargs):
        # 获取客户端 ID
        actual_client_id = client_id
        if callable(client_id):
          actual_client_id = client_id(*args, **kwargs)

        # 检查速率限制
        allowed, remaining, blocked_for = self.limiter.check_rate_limit(
          actual_client_id, config
        )

        if not allowed:
          raise RateLimitExceededError(
            message="Too many requests",
            retry_after=blocked_for
          )

        # 添加速率限制头信息
        if hasattr(args[0], '_rate_limit_headers') if args else False:
          pass

        return func(*args, **kwargs)

      return wrapper
    return decorator

  def check_and_wait(self, client_id: str, config: Optional[RateLimitConfig] = None) -> bool:
    """
    检查并等待（如果需要）

    Args:
        client_id: 客户端 ID
        config: 可选的特定配置

    Returns:
        bool: 是否允许
    """
    allowed, remaining, blocked_for = self.limiter.check_rate_limit(client_id, config)

    if not allowed and blocked_for:
      # 可选：等待后重试
      # time.sleep(min(blocked_for, 5))  # 最多等待5秒
      pass

    return allowed


class RateLimitExceededError(Exception):
  """速率限制超出异常"""

  def __init__(self, message: str = "Too many requests", retry_after: Optional[float] = None):
    super().__init__(message)
    self.message = message
    self.retry_after = retry_after


# 创建全局速率限制器实例
rate_limiter = RateLimiter(
  default_config=RateLimitConfig(
    max_requests=100,
    window_seconds=60,
    block_duration_seconds=300
  )
)


def get_rate_limiter() -> RateLimiter:
  """
  获取速率限制器实例

  Returns:
      RateLimiter: 速率限制器实例
  """
  return rate_limiter
