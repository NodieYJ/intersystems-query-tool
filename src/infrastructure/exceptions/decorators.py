#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
异常处理装饰器模块

提供通用的异常处理装饰器和重试机制。
"""

import logging
from functools import wraps
from typing import Callable, Dict, Type

logger = logging.getLogger(__name__)


def handleExceptions(
  defaultReturn: any = None,
  exceptionMap: Dict[Type[Exception], Callable] = None,
  reraise: bool = False,
  logLevel: str = "error"
):
  """
  异常处理装饰器

  统一处理方法中的异常，提供灵活的异常处理策略。

  Args:
    defaultReturn: 默认返回值（发生异常时返回）
    exceptionMap: 异常类型到处理函数的映射
    reraise: 是否重新抛出异常
    logLevel: 日志级别

  Example:
    @handleExceptions(defaultReturn=None, logLevel="warning")
    def riskyOperation():
      ...
  """
  from src.infrastructure.exceptions import AppException

  def decorator(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
      try:
        return func(*args, **kwargs)

      except AppException as e:
        # 应用异常已包含完整信息，直接记录
        e.log(logger)

        if exceptionMap and type(e) in exceptionMap:
          return exceptionMap[type(e)](e)

        return defaultReturn

      except Exception as e:
        # 转换为应用异常
        appExc = AppException(
          message=str(e),
          errorCode="APP_999",
          cause=e
        )
        appExc.log(logger)

        if exceptionMap:
          for excType, handler in exceptionMap.items():
            if isinstance(e, excType):
              return handler(e)

        if reraise:
          raise

        return defaultReturn

    return wrapper
  return decorator


def retry(
  maxAttempts: int = 3,
  delay: float = 1.0,
  backoff: float = 2.0,
  exceptions: tuple = (Exception,)
):
  """
  重试装饰器

  在发生异常时自动重试操作。

  Args:
    maxAttempts: 最大重试次数
    delay: 初始延迟时间（秒）
    backoff: 延迟时间倍增因子
    exceptions: 需要重试的异常类型

  Example:
    @retry(maxAttempts=3, delay=1.0)
    def connectToDatabase():
      ...
  """
  import time

  def decorator(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
      currentDelay = delay
      lastException = None

      for attempt in range(maxAttempts):
        try:
          return func(*args, **kwargs)
        except exceptions as e:
          lastException = e

          if attempt == maxAttempts - 1:
            # 最后一次尝试，重新抛出
            raise

          logger.warning(
            f"第 {attempt + 1} 次尝试失败，"
            f"等待 {currentDelay:.1f} 秒后重试: {str(e)}"
          )

          time.sleep(currentDelay)
          currentDelay *= backoff

      raise lastException

    return wrapper
  return decorator


# 导出所有装饰器
__all__ = [
  'handleExceptions',
  'retry',
]
