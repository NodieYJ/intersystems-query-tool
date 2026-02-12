#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
事件总线模块

提供事件驱动的通信机制。
支持同步和异步事件处理。
"""

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum, auto


logger = logging.getLogger(__name__)


class EventPriority(Enum):
  """事件优先级枚举"""
  LOW = auto()
  NORMAL = auto()
  HIGH = auto()


@dataclass(eq=False)
class EventHandler:
  """事件处理器定义"""
  callback: Callable
  priority: EventPriority = EventPriority.NORMAL
  once: bool = False
  id: str = field(default_factory=lambda: str(id(object())))

  def __hash__(self):
    return hash(self.id)


class Event:
  """事件基类"""

  def __init__(self, eventType: str, data: Dict[str, Any] = None):
    """
    初始化事件

    Args:
      eventType: 事件类型
      data: 事件数据
    """
    self.eventType = eventType
    self.data = data or {}
    self.timestamp = self._getTimestamp()
    self.source: Any = None
    self.propagationStopped = False

  def _getTimestamp(self) -> str:
    """获取事件时间戳"""
    from datetime import datetime
    return datetime.now().isoformat()

  def stopPropagation(self):
    """停止事件传播"""
    self.propagationStopped = True


class EventBus:
  """
  事件总线类

  提供事件的发布、订阅和取消订阅功能。
  支持同步和异步事件处理。
  """

  def __init__(self, name: str = "default"):
    """
    初始化事件总线

    Args:
      name: 事件总线名称
    """
    self.name = name
    self._handlers: Dict[str, Set[EventHandler]] = {}
    self._wildcardHandlers: Set[EventHandler] = set()
    self._lock = threading.RLock()
    self._eventHistory: List[Event] = []
    self._maxHistorySize = 100

  def subscribe(
    self,
    eventType: str,
    callback: Callable,
    priority: EventPriority = EventPriority.NORMAL,
    once: bool = False
  ) -> str:
    """
    订阅事件

    Args:
      eventType: 事件类型
      callback: 回调函数
      priority: 优先级
      once: 是否只处理一次

    Returns:
      str: 订阅ID
    """
    with self._lock:
      handler = EventHandler(
        callback=callback,
        priority=priority,
        once=once
      )

      if eventType == "*":
        self._wildcardHandlers.add(handler)
      else:
        if eventType not in self._handlers:
          self._handlers[eventType] = set()
        self._handlers[eventType].add(handler)

      logger.debug(f"订阅事件: {eventType}, 回调: {callback.__name__}")
      return handler.id

  def unsubscribe(self, eventType: str, handlerId: str = None) -> bool:
    """
    取消订阅

    Args:
      eventType: 事件类型
      handlerId: 处理器ID

    Returns:
      bool: 是否取消成功
    """
    with self._lock:
      # 移除通配符处理器
      if eventType == "*":
        for handler in list(self._wildcardHandlers):
          if handler.id == handlerId:
            self._wildcardHandlers.remove(handler)
            logger.debug(f"取消订阅通配符事件: {handlerId}")
            return True
        return False

      # 移除指定事件处理器
      if eventType in self._handlers:
        for handler in list(self._handlers[eventType]):
          if handler.id == handlerId:
            self._handlers[eventType].remove(handler)
            logger.debug(f"取消订阅事件: {eventType}, ID: {handlerId}")
            return True

      return False

  def publish(self, event: Event) -> List[Any]:
    """
    发布事件（同步）

    Args:
      event: 事件对象

    Returns:
      List[Any]: 处理结果列表
    """
    results = []

    with self._lock:
      # 记录事件历史
      self._addToHistory(event)

      # 获取处理器列表（按优先级排序）
      handlers = self._getHandlers(event.eventType)

    # 同步处理事件
    for handler in handlers:
      try:
        if event.propagationStopped:
          break

        result = handler.callback(event)
        results.append(result)

        if handler.once:
          self.unsubscribe(event.eventType, handler.id)

      except Exception as e:
        logger.error(f"事件处理失败: {event.eventType}, 错误: {e}")
        results.append(e)

    return results

  def publishAsync(self, event: Event) -> None:
    """
    发布事件（异步）

    Args:
      event: 事件对象
    """
    import threading

    def _process():
      try:
        self.publish(event)
      except Exception as e:
        logger.error(f"异步事件处理失败: {e}")

    thread = threading.Thread(target=_process, daemon=True)
    thread.start()

  def _getHandlers(self, eventType: str) -> List[EventHandler]:
    """
    获取事件处理器列表（按优先级排序）

    Args:
      eventType: 事件类型

    Returns:
      List[EventHandler]: 排序后的处理器列表
    """
    handlers = []

    # 添加通配符处理器
    handlers.extend(self._wildcardHandlers)

    # 添加指定事件处理器
    if eventType in self._handlers:
      handlers.extend(self._handlers[eventType])

    # 按优先级排序
    priorityOrder = {
      EventPriority.HIGH: 0,
      EventPriority.NORMAL: 1,
      EventPriority.LOW: 2
    }

    return sorted(handlers, key=lambda h: priorityOrder.get(h.priority, 1))

  def _addToHistory(self, event: Event) -> None:
    """添加事件到历史记录"""
    self._eventHistory.append(event)

    # 限制历史记录大小
    if len(self._eventHistory) > self._maxHistorySize:
      self._eventHistory = self._eventHistory[-self._maxHistorySize:]

  def getHistory(self, eventType: str = None) -> List[Event]:
    """
    获取事件历史

    Args:
      eventType: 事件类型（可选）

    Returns:
      List[Event]: 事件列表
    """
    if eventType:
      return [e for e in self._eventHistory if e.eventType == eventType]
    return list(self._eventHistory)

  def clearHistory(self):
    """清空事件历史"""
    self._eventHistory.clear()

  def getHandlerCount(self, eventType: str = None) -> int:
    """
    获取处理器数量

    Args:
      eventType: 事件类型（可选）

    Returns:
      int: 处理器数量
    """
    if eventType:
      if eventType in self._handlers:
        return len(self._handlers[eventType])
      return 0
    return sum(len(h) for h in self._handlers.values()) + len(self._wildcardHandlers)

  def createEvent(self, eventType: str, data: Dict[str, Any] = None) -> Event:
    """
    创建并发布事件

    Args:
      eventType: 事件类型
      data: 事件数据

    Returns:
      Event: 创建的事件对象
    """
    event = Event(eventType, data)
    self.publish(event)
    return event


# 创建默认事件总线实例
_defaultEventBus = None


def getEventBus(name: str = "default") -> EventBus:
  """
  获取事件总线实例

  Args:
    name: 事件总线名称

  Returns:
    EventBus: 事件总线实例
    """
  global _defaultEventBus

  if name == "default" and _defaultEventBus is not None:
    return _defaultEventBus

  return EventBus(name)


def publishEvent(eventType: str, data: Dict[str, Any] = None) -> List[Any]:
  """
  发布事件的便捷函数

    Args:
      eventType: 事件类型
      data: 事件数据

    Returns:
      List[Any]: 处理结果列表
    """
  event = Event(eventType, data)
  return getEventBus().publish(event)


def subscribeEvent(
  eventType: str,
  callback: Callable,
  priority: EventPriority = EventPriority.NORMAL
) -> str:
  """
  订阅事件的便捷函数

  Args:
    eventType: 事件类型
    callback: 回调函数
    priority: 优先级

  Returns:
    str: 订阅ID
  """
  return getEventBus().subscribe(eventType, callback, priority)


# 导出所有类和函数
__all__ = [
  'EventBus',
  'Event',
  'EventPriority',
  'EventHandler',
  'getEventBus',
  'publishEvent',
  'subscribeEvent',
]
