#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
策略模式模块

提供策略模式实现，支持算法的动态切换。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Type, TypeVar
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class StrategyInfo:
  """策略信息"""
  name: str
  description: str
  version: str = "1.0.0"


class IStrategy(ABC, Generic[T]):
  """策略接口"""

  @abstractmethod
  def execute(self, *args, **kwargs) -> T:
    """
    执行策略

    Args:
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      T: 执行结果
    """
    pass

  @abstractmethod
  def getInfo(self) -> StrategyInfo:
    """
    获取策略信息

    Returns:
      StrategyInfo: 策略信息
    """
    pass

  @abstractmethod
  def validate(self, *args, **kwargs) -> bool:
    """
    验证参数

    Args:
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      bool: 是否有效
    """
    pass


class StrategyContext:
  """策略上下文

  管理策略的执行和切换。
  """

  def __init__(self, defaultStrategy: Optional[IStrategy] = None):
    """
    初始化策略上下文

    Args:
      defaultStrategy: 默认策略
    """
    self._strategies: Dict[str, IStrategy] = {}
    self._currentStrategy: Optional[IStrategy] = None
    self._defaultStrategy = defaultStrategy

    if defaultStrategy:
      self._currentStrategy = defaultStrategy

  def register(self, strategy: IStrategy, name: str = None) -> None:
    """
    注册策略

    Args:
      strategy: 策略实例
      name: 策略名称（默认使用info.name）
    """
    strategyName = name or strategy.getInfo().name
    self._strategies[strategyName] = strategy
    logger.debug(f"策略已注册: {strategyName}")

    # 如果没有当前策略，使用第一个注册的
    if self._currentStrategy is None:
      self._currentStrategy = strategy

  def unregister(self, name: str) -> bool:
    """
    注销策略

    Args:
      name: 策略名称

    Returns:
      bool: 是否注销成功
    """
    if name in self._strategies:
      del self._strategies[name]

      # 如果注销的是当前策略，切换到默认
      if self._currentStrategy and self._currentStrategy.getInfo().name == name:
        self._currentStrategy = self._defaultStrategy or (list(self._strategies.values())[0] if self._strategies else None)

      return True

    return False

  def setStrategy(self, name: str) -> bool:
    """
    设置当前策略

    Args:
      name: 策略名称

    Returns:
      bool: 是否设置成功
    """
    if name in self._strategies:
      self._currentStrategy = self._strategies[name]
      logger.info(f"策略已切换: {name}")
      return True

    logger.warning(f"策略不存在: {name}")
    return False

  def getStrategy(self, name: str) -> Optional[IStrategy]:
    """
    获取策略

    Args:
      name: 策略名称

    Returns:
      Optional[IStrategy]: 策略实例
    """
    return self._strategies.get(name)

  def getCurrentStrategy(self) -> Optional[IStrategy]:
    """
    获取当前策略

    Returns:
      Optional[IStrategy]: 当前策略
    """
    return self._currentStrategy

  def execute(self, *args, **kwargs) -> Any:
    """
    执行当前策略

    Args:
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      Any: 执行结果
    """
    if not self._currentStrategy:
      raise ValueError("没有可用的策略")

    # 验证参数
    if not self._currentStrategy.validate(*args, **kwargs):
      raise ValueError("策略参数无效")

    return self._currentStrategy.execute(*args, **kwargs)

  def executeWith(self, strategyName: str, *args, **kwargs) -> Any:
    """
    使用指定策略执行

    Args:
      strategyName: 策略名称
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      Any: 执行结果
    """
    strategy = self._strategies.get(strategyName)

    if not strategy:
      raise ValueError(f"策略不存在: {strategyName}")

    if not strategy.validate(*args, **kwargs):
      raise ValueError("策略参数无效")

    return strategy.execute(*args, **kwargs)

  def listStrategies(self) -> Dict[str, StrategyInfo]:
    """
    列出所有策略

    Returns:
      Dict[str, StrategyInfo]: 策略名称到信息的映射
    """
    return {name: strategy.getInfo() for name, strategy in self._strategies.items()}


class StrategyFactory:
  """策略工厂

  用于创建和管理策略实例。
  """

  _instance = None
  _lock = None

  def __init__(self):
    """初始化策略工厂"""
    self._registry: Dict[str, Type[IStrategy]] = {}
    self._lock = logging.getLogger(__name__).handlers[0] if logging.getLogger(__name__).handlers else None

  @classmethod
  def getInstance(cls) -> 'StrategyFactory':
    """获取单例实例"""
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def register(self, strategyClass: Type[IStrategy], name: str = None) -> None:
    """
    注册策略类

    Args:
      strategyClass: 策略类
      name: 策略名称
    """
    strategyName = name or strategyClass.__name__
    self._registry[strategyName] = strategyClass
    logger.debug(f"策略类已注册: {strategyName}")

  def create(self, name: str, *args, **kwargs) -> Optional[IStrategy]:
    """
    创建策略实例

    Args:
      name: 策略名称
      *args: 构造参数
      **kwargs: 构造关键字参数

    Returns:
      Optional[IStrategy]: 策略实例
    """
    if name not in self._registry:
      logger.warning(f"策略类未注册: {name}")
      return None

    strategyClass = self._registry[name]
    return strategyClass(*args, **kwargs)

  def hasStrategy(self, name: str) -> bool:
    """
    检查策略是否存在

    Args:
      name: 策略名称

    Returns:
      bool: 是否存在
    """
    return name in self._registry


# 便捷函数
def create_context(defaultStrategy: IStrategy = None) -> StrategyContext:
  """
  创建策略上下文

  Args:
    defaultStrategy: 默认策略

  Returns:
    StrategyContext: 策略上下文
  """
  return StrategyContext(defaultStrategy)


def register(name: str) -> callable:
  """
  注册策略的装饰器

  Args:
    name: 策略名称

  Returns:
    装饰器函数
  """
  def decorator(strategyClass):
    StrategyFactory.getInstance().register(strategyClass, name)
    return strategyClass
  return decorator


# 导出
__all__ = [
  'IStrategy',
  'StrategyInfo',
  'StrategyContext',
  'StrategyFactory',
  'create_context',
  'register',
  'T',
]
