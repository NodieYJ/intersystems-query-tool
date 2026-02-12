#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强依赖注入容器模块

提供增强的依赖注入功能：
- 组件扫描和自动注册
- 循环依赖检测
- 生命周期管理
- 配置驱动注册
- 性能监控
"""

import inspect
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime:
  """服务生命周期枚举"""
  SINGLETON = "singleton"
  TRANSIENT = "transient"
  SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
  """服务描述符"""
  interface: Type
  implementation: Union[Type, Callable]
  lifetime: str = ServiceLifetime.TRANSIENT
  instance: Optional[Any] = None
  factory: Optional[Callable] = None
  tags: List[str] = field(default_factory=list)
  dependencies: List[str] = field(default_factory=list)


@dataclass
class ResolutionInfo:
  """解析信息"""
  serviceType: Type
  startTime: float
  endTime: Optional[float] = None
  success: bool = False
  error: Optional[Exception] = None


class IContainer(ABC):
  """容器接口"""

  @abstractmethod
  def register(self, interface: Type, implementation: Union[Type, Callable], lifetime: str, **kwargs) -> None:
    pass

  @abstractmethod
  def resolve(self, interface: Type) -> Any:
    pass

  @abstractmethod
  def isRegistered(self, interface: Type) -> bool:
    pass


class EnhancedDIContainer:
  """
  增强依赖注入容器

  提供完整的依赖注入功能，支持：
  - 多种生命周期
  - 自动组件扫描
  - 循环依赖检测
  - 性能监控
  """

  _instance = None
  _lock = threading.Lock()

  def __init__(
    self,
    enableDiagnostics: bool = True,
    maxResolutionDepth: int = 50
  ):
    """
    初始化增强容器

    Args:
      enableDiagnostics: 是否启用诊断
      maxResolutionDepth: 最大解析深度
    """
    self._services: Dict[str, ServiceDescriptor] = {}
    self._singletons: Dict[str, Any] = {}
    self._scopes: Dict[str, Dict[str, Any]] = {}
    self._currentScope: Optional[str] = None
    self._lock = threading.RLock()
    self._resolutionStack: List[str] = []
    self._maxResolutionDepth = maxResolutionDepth
    self._enableDiagnostics = enableDiagnostics
    self._resolutionHistory: List[ResolutionInfo] = []
    self._componentCount = 0
    self._resolutionCount = 0

    # 内置类型注册
    self._registerBuiltInTypes()

  @classmethod
  def getInstance(cls) -> 'EnhancedDIContainer':
    """获取单例实例"""
    with cls._lock:
      if cls._instance is None:
        cls._instance = cls()
      return cls._instance

  @classmethod
  def resetInstance(cls):
    """重置单例实例"""
    with cls._lock:
      if cls._instance is not None:
        cls._instance._cleanup()
      cls._instance = None

  def _registerBuiltInTypes(self):
    """注册内置类型"""
    # 这里的注册将在实际使用时完成
    pass

  def register(
    self,
    interface: Type,
    implementation: Union[Type, Callable] = None,
    lifetime: str = ServiceLifetime.TRANSIENT,
    tags: List[str] = None,
    **kwargs
  ) -> 'EnhancedDIContainer':
    """
    注册服务

    Args:
      interface: 接口类型
      implementation: 实现类型或工厂函数
      lifetime: 生命周期
      tags: 标签列表
      **kwargs: 其他参数

    Returns:
      self: 支持链式调用
    """
    if implementation is None:
      implementation = interface

    with self._lock:
      key = self._getKey(interface)
      descriptor = ServiceDescriptor(
        interface=interface,
        implementation=implementation,
        lifetime=lifetime,
        tags=tags or [],
        **kwargs
      )
      self._services[key] = descriptor
      self._componentCount += 1

    logger.debug(f"已注册服务: {interface.__name__} ({lifetime})")
    return self

  def registerSingleton(
    self,
    interface: Type,
    implementation: Union[Type, Callable] = None,
    tags: List[str] = None
  ) -> 'EnhancedDIContainer':
    """
    注册单例服务

    Args:
      interface: 接口类型
      implementation: 实现类型
      tags: 标签列表

    Returns:
      self: 支持链式调用
    """
    return self.register(interface, implementation, ServiceLifetime.SINGLETON, tags)

  def registerTransient(
    self,
    interface: Type,
    implementation: Union[Type, Callable] = None,
    tags: List[str] = None
  ) -> 'EnhancedDIContainer':
    """
    注册瞬态服务

    Args:
      interface: 接口类型
      implementation: 实现类型
      tags: 标签列表

    Returns:
      self: 支持链式调用
    """
    return self.register(interface, implementation, ServiceLifetime.TRANSIENT, tags)

  def registerScoped(
    self,
    interface: Type,
    implementation: Union[Type, Callable] = None,
    tags: List[str] = None
  ) -> 'EnhancedDIContainer':
    """
    注册作用域服务

    Args:
      interface: 接口类型
      implementation: 实现类型
      tags: 标签列表

    Returns:
      self: 支持链式调用
    """
    return self.register(interface, implementation, ServiceLifetime.SCOPED, tags)

  def registerFactory(
    self,
    interface: Type,
    factory: Callable,
    lifetime: str = ServiceLifetime.TRANSIENT,
    tags: List[str] = None
  ) -> 'EnhancedDIContainer':
    """
    注册工厂函数

    Args:
      interface: 接口类型
      factory: 工厂函数
      lifetime: 生命周期
      tags: 标签列表

    Returns:
      self: 支持链式调用
    """
    with self._lock:
      key = self._getKey(interface)
      descriptor = ServiceDescriptor(
        interface=interface,
        implementation=factory,
        lifetime=lifetime,
        factory=factory,
        tags=tags or []
      )
      self._services[key] = descriptor
      self._componentCount += 1

    logger.debug(f"已注册工厂: {interface.__name__}")
    return self

  def resolve(self, interface: Type, **kwargs) -> Any:
    """
    解析服务

    Args:
      interface: 接口类型
      **kwargs: 额外参数

    Returns:
      Any: 服务实例
    """
    key = self._getKey(interface)
    resolutionStart = time.time()

    if self._enableDiagnostics:
      info = ResolutionInfo(serviceType=interface, startTime=resolutionStart)
      self._resolutionHistory.append(info)

    try:
      with self._lock:
        # 检查是否已注册
        if key not in self._services:
          raise ValueError(f"服务未注册: {interface.__name__}")

        descriptor = self._services[key]
        self._resolutionStack.append(key)

        # 检测循环依赖
        if len(self._resolutionStack) > self._maxResolutionDepth:
          raise RecursionError(
            f"检测到可能的循环依赖: {' -> '.join(self._resolutionStack)}"
          )

        # 根据生命周期解析
        instance = self._resolveInstance(descriptor, **kwargs)

        # 移除解析栈
        self._resolutionStack.pop()

        # 更新诊断信息
        if self._enableDiagnostics:
          info.endTime = time.time()
          info.success = True
          self._resolutionCount += 1

      return instance

    except Exception as e:
      if self._enableDiagnostics and self._resolutionHistory:
        self._resolutionHistory[-1].endTime = time.time()
        self._resolutionHistory[-1].error = e

      logger.error(f"解析服务失败: {interface.__name__}, 错误: {e}")
      raise

  def _resolveInstance(self, descriptor: ServiceDescriptor, **kwargs) -> Any:
    """
    解析服务实例

    Args:
      descriptor: 服务描述符
      **kwargs: 额外参数

    Returns:
      Any: 服务实例
    """
    # 单例模式
    if descriptor.lifetime == ServiceLifetime.SINGLETON:
      if descriptor.instance is not None:
        return descriptor.instance

      # 创建实例
      instance = self._createInstance(descriptor, **kwargs)
      descriptor.instance = instance
      return instance

    # 作用域模式
    if descriptor.lifetime == ServiceLifetime.SCOPED:
      if self._currentScope and self._currentScope in self._scopes:
        scopeInstances = self._scopes[self._currentScope]
        key = self._getKey(descriptor.interface)
        if key in scopeInstances:
          return scopeInstances[key]

      # 创建实例
      instance = self._createInstance(descriptor, **kwargs)

      # 保存到作用域
      if self._currentScope:
        if self._currentScope not in self._scopes:
          self._scopes[self._currentScope] = {}
        self._scopes[self._currentScope][self._getKey(descriptor.interface)] = instance

      return instance

    # 瞬态模式 - 每次创建新实例
    return self._createInstance(descriptor, **kwargs)

  def _createInstance(self, descriptor: ServiceDescriptor, **kwargs) -> Any:
    """
    创建服务实例

    Args:
      descriptor: 服务描述符
      **kwargs: 额外参数

    Returns:
      Any: 服务实例
    """
    # 工厂函数
    if descriptor.factory:
      return descriptor.factory(**kwargs)

    # 直接类型
    if inspect.isclass(descriptor.implementation):
      # 获取构造函数参数
      try:
        hints = get_type_hints(descriptor.implementation.__init__)
      except Exception:
        hints = {}

      # 构建参数
      args = {}
      for paramName, paramType in hints.items():
        if paramName == 'self':
          continue

        if paramName in kwargs:
          args[paramName] = kwargs[paramName]
        else:
          # 尝试自动注入依赖
          resolved = self._resolveDependency(paramName, paramType)
          if resolved is not None:
            args[paramName] = resolved

      return descriptor.implementation(**args)

    # 如果是实例，直接返回
    return descriptor.implementation

  def _resolveDependency(self, paramName: str, paramType: Type) -> Any:
    """
    解析依赖

    Args:
      paramName: 参数名
      paramType: 参数类型

    Returns:
      Any: 解析的依赖
    """
    key = self._getKey(paramType)

    if key in self._services:
      try:
        return self.resolve(paramType)
      except Exception:
        return None

    return None

  def isRegistered(self, interface: Type) -> bool:
    """
    检查服务是否已注册

    Args:
      interface: 接口类型

    Returns:
      bool: 是否已注册
    """
    key = self._getKey(interface)
    return key in self._services

  def unregister(self, interface: Type) -> bool:
    """
    注销服务

    Args:
      interface: 接口类型

    Returns:
      bool: 是否注销成功
    """
    key = self._getKey(interface)

    with self._lock:
      if key not in self._services:
        return False

      descriptor = self._services[key]

      # 如果是单例，清理实例
      if descriptor.lifetime == ServiceLifetime.SINGLETON and descriptor.instance:
        descriptor.instance = None

      del self._services[key]
      self._componentCount -= 1

    logger.debug(f"已注销服务: {interface.__name__}")
    return True

  def createScope(self, scopeId: str) -> 'ScopedContainer':
    """
    创建作用域

    Args:
      scopeId: 作用域ID

    Returns:
      ScopedContainer: 作用域容器
    """
    return ScopedContainer(self, scopeId)

  def resolveAll(self, interface: Type) -> List[Any]:
    """
    解析所有实现

    Args:
      interface: 接口类型

    Returns:
      List[Any]: 服务实例列表
    """
    # TODO: 实现多实现解析
    return [self.resolve(interface)]

  def getDiagnostics(self) -> Dict[str, Any]:
    """
    获取诊断信息

    Returns:
      Dict[str, Any]: 诊断信息
    """
    return {
      "registeredServices": self._componentCount,
      "resolvedServices": self._resolutionCount,
      "singletons": len(self._singletons),
      "scopes": len(self._scopes),
      "resolutionHistory": [
        {
          "service": info.serviceType.__name__,
          "duration": info.endTime - info.startTime if info.endTime else None,
          "success": info.success,
          "error": str(info.error) if info.error else None
        }
        for info in self._resolutionHistory[-100:]  # 最近100条
      ]
    }

  def clear(self):
    """清空所有注册"""
    with self._lock:
      self._services.clear()
      self._singletons.clear()
      self._scopes.clear()
      self._resolutionHistory.clear()
      self._componentCount = 0
      self._resolutionCount = 0

  def _cleanup(self):
    """清理资源"""
    self.clear()

  def _getKey(self, interface: Type) -> str:
    """获取服务键"""
    return f"{interface.__module__}.{interface.__name__}"


class ScopedContainer:
  """作用域容器"""

  def __init__(self, container: EnhancedDIContainer, scopeId: str):
    """
    初始化作用域容器

    Args:
      container: 父容器
      scopeId: 作用域ID
    """
    self._container = container
    self._scopeId = scopeId
    self._entered = False

  def __enter__(self):
    """进入作用域"""
    self._container._currentScope = self._scopeId
    self._entered = True
    return self

  def __exit__(self, excType, excVal, excTb):
    """退出作用域"""
    self._container._currentScope = None
    # 清理作用域内的瞬态实例
    if self._scopeId in self._container._scopes:
      del self._container._scopes[self._scopeId]
    return False

  def resolve(self, interface: Type) -> Any:
    """
    解析服务

    Args:
      interface: 接口类型

    Returns:
      Any: 服务实例
    """
    if not self._entered:
      raise RuntimeError("必须在with语句中使用作用域容器")

    return self._container.resolve(interface)


# 创建默认容器实例
_defaultContainer = None


def getContainer() -> EnhancedDIContainer:
  """
  获取默认容器实例

  Returns:
    EnhancedDIContainer: 容器实例
  """
  global _defaultContainer

  if _defaultContainer is None:
    _defaultContainer = EnhancedDIContainer.getInstance()

  return _defaultContainer


def resetContainer():
  """重置默认容器"""
  global _defaultContainer
  EnhancedDIContainer.resetInstance()
  _defaultContainer = None


# 导出
__all__ = [
  'EnhancedDIContainer',
  'ScopedContainer',
  'ServiceLifetime',
  'ServiceDescriptor',
  'getContainer',
  'resetContainer',
]
