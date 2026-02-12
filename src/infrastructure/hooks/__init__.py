#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hook管理器模块

提供钩子机制，支持在关键代码点注入自定义逻辑。
支持同步和异步钩子执行。
"""

import logging
import threading
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HookStage(Enum):
  """钩子执行阶段"""
  BEFORE = "before"
  AFTER = "after"
  AROUND = "around"


@dataclass
class HookRegistration:
  """钩子注册信息"""
  hookName: str
  callback: Callable
  stage: HookStage = HookStage.BEFORE
  priority: int = 0
  enabled: bool = True
  once: bool = False
  id: str = ""


class HookContext:
  """钩子执行上下文"""

  def __init__(self, hookName: str, data: Dict[str, Any] = None):
    self.hookName = hookName
    self.data = data or {}
    self.result: Any = None
    self.error: Exception = None
    self.propagationStopped = False

  def setResult(self, result: Any):
    """设置结果"""
    self.result = result

  def getResult(self) -> Any:
    """获取结果"""
    return self.result

  def setError(self, error: Exception):
    """设置错误"""
    self.error = error

  def stopPropagation(self):
    """停止传播"""
    self.propagationStopped = True


class HookManager:
  """
  Hook管理器

  管理应用程序中的所有钩子点。
  支持钩子的注册、注销、执行和生命周期管理。
  """

  _instance = None
  _lock = threading.Lock()

  def __init__(self):
    """初始化Hook管理器"""
    self._hooks: Dict[str, List[HookRegistration]] = {}
    self._hookContext: Optional[HookContext] = None
    self._lock = threading.RLock()
    self._enabled = True
    self._executionHistory: List[Dict] = []
    self._maxHistorySize = 100

  @classmethod
  def getInstance(cls) -> 'HookManager':
    """获取单例实例"""
    with cls._lock:
      if cls._instance is None:
        cls._instance = cls()
      return cls._instance

  def register(
    self,
    hookName: str,
    callback: Callable,
    stage: HookStage = HookStage.BEFORE,
    priority: int = 0,
    once: bool = False
  ) -> str:
    """
    注册钩子

    Args:
      hookName: 钩子名称
      callback: 回调函数
      stage: 执行阶段
      priority: 优先级（数值越大越先执行）
      once: 是否只执行一次

    Returns:
      str: 注册ID
    """
    with self._lock:
      registration = HookRegistration(
        hookName=hookName,
        callback=callback,
        stage=stage,
        priority=priority,
        once=once,
        id=f"{hookName}_{id(callback)}"
      )

      if hookName not in self._hooks:
        self._hooks[hookName] = []

      self._hooks[hookName].append(registration)

      # 按优先级排序
      self._hooks[hookName].sort(key=lambda h: -h.priority)

      logger.debug(f"钩子已注册: {hookName}, 优先级: {priority}")
      return registration.id

  def unregister(self, registrationId: str) -> bool:
    """
    注销钩子

    Args:
      registrationId: 注册ID

    Returns:
      bool: 是否注销成功
    """
    with self._lock:
      for hookName, registrations in self._hooks.items():
        for registration in registrations:
          if registration.id == registrationId:
            registrations.remove(registration)
            logger.debug(f"钩子已注销: {hookName}")
            return True

      return False

  def unregisterAll(self, hookName: str) -> int:
    """
    注销所有钩子

    Args:
      hookName: 钩子名称

    Returns:
      int: 注销的钩子数量
    """
    with self._lock:
      count = len(self._hooks.get(hookName, []))
      self._hooks[hookName] = []
      return count

  def execute(self, hookName: str, data: Dict[str, Any] = None) -> Any:
    """
    执行钩子（同步）

    Args:
      hookName: 钩子名称
      data: 传递给钩子的数据

    Returns:
      Any: 最后一个钩子的返回值
    """
    if not self._enabled:
      return data

    context = HookContext(hookName, data)
    self._hookContext = context

    with self._lock:
      registrations = self._hooks.get(hookName, [])

    results = []

    try:
      # BEFORE 阶段
      for registration in registrations:
        if not registration.enabled or registration.stage != HookStage.BEFORE:
          continue

        if context.propagationStopped:
          break

        try:
          result = registration.callback(context)
          results.append(result)
          context.setResult(result)

          if registration.once:
            self.unregister(registration.id)

        except Exception as e:
          context.setError(e)
          logger.error(f"钩子执行失败: {hookName}, 错误: {e}")

      # AROUND 阶段（可以完全控制执行流程）
      aroundHooks = [r for r in registrations if r.enabled and r.stage == HookStage.AROUND]

      if aroundHooks:
        # 第一个around钩子可以调用下一个
        def createChain(hooks, index):
          if index >= len(hooks):
            return lambda ctx: None

          hook = hooks[index]

          def nextChain(ctx):
            return hook.callback(ctx, lambda: createChain(hooks, index + 1)(ctx))

          return nextChain

        chainStart = createChain(aroundHooks, 0)
        chainStart(context)
      else:
        # 没有around钩子，直接设置结果
        pass

      # AFTER 阶段
      for registration in registrations:
        if not registration.enabled or registration.stage != HookStage.AFTER:
          continue

        if context.propagationStopped:
          break

        try:
          result = registration.callback(context)
          results.append(result)
          context.setResult(result)

          if registration.once:
            self.unregister(registration.id)

        except Exception as e:
          context.setError(e)
          logger.error(f"钩子执行失败: {hookName}, 错误: {e}")

    finally:
      self._hookContext = None
      self._addToHistory(hookName, context, results)

    return context.result

  def executeAsync(self, hookName: str, data: Dict[str, Any] = None):
    """
    执行钩子（异步）

    Args:
      hookName: 钩子名称
      data: 传递给钩子的数据
    """
    import threading

    def _execute():
      try:
        self.execute(hookName, data)
      except Exception as e:
        logger.error(f"异步钩子执行失败: {hookName}, 错误: {e}")

    thread = threading.Thread(target=_execute, daemon=True)
    thread.start()

  def hasHooks(self, hookName: str) -> bool:
    """
    检查是否有钩子注册

    Args:
      hookName: 钩子名称

    Returns:
      bool: 是否有钩子
    """
    with self._lock:
      return hookName in self._hooks and len(self._hooks[hookName]) > 0

  def getHookCount(self, hookName: str = None) -> int:
    """
    获取钩子数量

    Args:
      hookName: 钩子名称（可选）

    Returns:
      int: 钩子数量
    """
    with self._lock:
      if hookName:
        return len(self._hooks.get(hookName, []))
      return sum(len(hooks) for hooks in self._hooks.values())

  def getRegistrations(self, hookName: str) -> List[HookRegistration]:
    """
    获取钩子注册列表

    Args:
      hookName: 钩子名称

    Returns:
      List[HookRegistration]: 注册列表
    """
    with self._lock:
      return list(self._hooks.get(hookName, []))

  def enableHook(self, registrationId: str, enabled: bool = True) -> bool:
    """
    启用或禁用钩子

    Args:
      registrationId: 注册ID
      enabled: 是否启用

    Returns:
      bool: 是否操作成功
    """
    with self._lock:
      for registrations in self._hooks.values():
        for registration in registrations:
          if registration.id == registrationId:
            registration.enabled = enabled
            return True

      return False

  def setEnabled(self, enabled: bool):
    """
    设置是否启用所有钩子

    Args:
      enabled: 是否启用
    """
    self._enabled = enabled

  def getExecutionHistory(self, hookName: str = None) -> List[Dict]:
    """
    获取执行历史

    Args:
      hookName: 钩子名称（可选）

    Returns:
      List[Dict]: 执行历史
    """
    if hookName:
      return [h for h in self._executionHistory if h['hookName'] == hookName]
    return list(self._executionHistory)

  def _addToHistory(self, hookName: str, context: HookContext, results: List[Any]):
    """添加执行历史"""
    self._executionHistory.append({
      'hookName': hookName,
      'timestamp': self._getTimestamp(),
      'success': context.error is None,
      'error': str(context.error) if context.error else None,
      'resultCount': len(results)
    })

    # 限制历史记录大小
    if len(self._executionHistory) > self._maxHistorySize:
      self._executionHistory = self._executionHistory[-self._maxHistorySize:]

  def _getTimestamp(self) -> str:
    """获取时间戳"""
    from datetime import datetime
    return datetime.now().isoformat()

  def clearHistory(self):
    """清空执行历史"""
    self._executionHistory.clear()


# 创建默认实例
_defaultHookManager = None


def getHookManager() -> HookManager:
  """
  获取Hook管理器实例

  Returns:
    HookManager: Hook管理器实例
  """
  global _defaultHookManager

  if _defaultHookManager is None:
    _defaultHookManager = HookManager.getInstance()

  return _defaultHookManager


# 便捷函数
def registerHook(
  hookName: str,
  callback: Callable,
  stage: HookStage = HookStage.BEFORE,
  priority: int = 0
) -> str:
  """
  注册钩子的便捷函数

  Args:
    hookName: 钩子名称
    callback: 回调函数
    stage: 执行阶段
    priority: 优先级

  Returns:
    str: 注册ID
  """
  return getHookManager().register(hookName, callback, stage, priority)


def executeHook(hookName: str, data: Dict[str, Any] = None) -> Any:
  """
  执行钩子的便捷函数

  Args:
    hookName: 钩子名称
    data: 数据

  Returns:
    Any: 钩子结果
  """
  return getHookManager().execute(hookName, data)


# 导出
__all__ = [
  'HookManager',
  'HookRegistration',
  'HookContext',
  'HookStage',
  'getHookManager',
  'registerHook',
  'executeHook',
]
