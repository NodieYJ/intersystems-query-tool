#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
异步执行器模块

提供在Qt UI线程中安全执行耗时操作的机制。
支持QThread池和进度报告。
"""

import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from src.infrastructure.interfaces import IAsyncExecutor

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
  """任务状态枚举"""
  PENDING = "pending"
  RUNNING = "running"
  COMPLETED = "completed"
  FAILED = "failed"
  CANCELLED = "cancelled"


@dataclass
class TaskResult:
  """任务结果类"""
  taskId: str
  status: TaskStatus
  result: Any = None
  error: Exception = None
  progress: int = 0
  message: str = ""
  startTime: float = field(default_factory=time.time)
  endTime: float = None

  def toDict(self) -> Dict[str, Any]:
    """转换为字典"""
    return {
      "taskId": self.taskId,
      "status": self.status.value,
      "result": self.result,
      "error": str(self.error) if self.error else None,
      "progress": self.progress,
      "message": self.message,
      "duration": self.endTime - self.startTime if self.endTime else None
    }


class IProgressReporter(ABC):
  """进度报告器接口"""

  @abstractmethod
  def reportProgress(self, progress: int, message: str = "") -> None:
    """
    报告进度

    Args:
      progress: 进度百分比 (0-100)
      message: 进度消息
    """
    pass


class ProgressReporter(IProgressReporter):
  """默认进度报告器"""

  def __init__(self, callback: Callable[[int, str], None] = None):
    """
    初始化进度报告器

    Args:
      callback: 进度回调函数
    """
    self.callback = callback
    self.progress = 0

  def reportProgress(self, progress: int, message: str = "") -> None:
    """
    报告进度

    Args:
      progress: 进度百分比
      message: 进度消息
    """
    self.progress = progress
    if self.callback:
      self.callback(progress, message)
    logger.debug(f"进度: {progress}% - {message}")


class QtAsyncExecutor(IAsyncExecutor):
  """
  Qt异步执行器

  在Qt应用程序中安全执行耗时操作。
  使用QThread避免阻塞UI线程。
  """

  def __init__(
    self,
    maxWorkers: int = 4,
    taskTimeout: float = 300.0
  ):
    """
    初始化异步执行器

    Args:
      maxWorkers: 最大工作线程数
      taskTimeout: 任务超时时间（秒）
    """
    self.maxWorkers = maxWorkers
    self.taskTimeout = taskTimeout
    self._executor = ThreadPoolExecutor(max_workers=maxWorkers)
    self._tasks: Dict[str, Future] = {}
    self._taskResults: Dict[str, TaskResult] = {}
    self._taskCallbacks: Dict[str, Dict[str, Any]] = {}
    self._lock = threading.Lock()
    self._taskCounter = 0
    self.logger = logging.getLogger(__name__)

  def executeAsync(
    self,
    task: Callable,
    *args,
    **kwargs
  ) -> str:
    """
    异步执行任务

    实现 IAsyncExecutor 接口。

    Args:
      task: 要执行的任务函数
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      str: 任务ID
    """
    taskId = self._generateTaskId()

    # 创建任务包装器
    def wrappedTask():
      try:
        # 更新任务状态
        self._updateTaskStatus(taskId, TaskStatus.RUNNING)

        # 执行任务
        result = task(*args, **kwargs)

        # 更新任务状态
        self._updateTaskStatus(taskId, TaskStatus.COMPLETED, result=result)
        return result

      except Exception as e:
        self.logger.error(f"任务执行失败: {taskId}, 错误: {e}")
        self._updateTaskStatus(taskId, TaskStatus.FAILED, error=e)
        raise

    # 提交任务
    future = self._executor.submit(wrappedTask)
    self._tasks[taskId] = future

    # 初始化任务结果
    self._taskResults[taskId] = TaskResult(
      taskId=taskId,
      status=TaskStatus.PENDING
    )

    self.logger.info(f"任务已提交: {taskId}")
    return taskId

  def submitTask(
    self,
    taskId: str,
    task: Callable,
    *args,
    **kwargs
  ) -> bool:
    """
    提交异步任务（带进度回调）

    实现 IAsyncExecutor 接口。

    Args:
      taskId: 任务唯一标识
      task: 要执行的任务函数
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      bool: 是否提交成功
    """
    if taskId in self._tasks:
      self.logger.warning(f"任务ID已存在: {taskId}")
      return False

    # 获取进度回调
    progressCallback = kwargs.pop('progressCallback', None)
    resultCallback = kwargs.pop('resultCallback', None)
    errorCallback = kwargs.pop('errorCallback', None)

    # 初始化任务回调
    self._taskCallbacks[taskId] = {
      'progressCallback': progressCallback,
      'resultCallback': resultCallback,
      'errorCallback': errorCallback
    }

    # 创建进度报告器
    progressReporter = ProgressReporter(
      callback=progressCallback
    )

    # 创建包装任务
    def wrappedTask():
      try:
        self._updateTaskStatus(taskId, TaskStatus.RUNNING)
        result = task(*args, progressReporter=progressReporter, **kwargs)
        self._updateTaskStatus(taskId, TaskStatus.COMPLETED, result=result)

        # 调用结果回调
        if resultCallback:
          resultCallback(result)

        return result

      except Exception as e:
        self.logger.error(f"任务执行失败: {taskId}, 错误: {e}")
        self._updateTaskStatus(taskId, TaskStatus.FAILED, error=e)

        # 调用错误回调
        if errorCallback:
          errorCallback(e)

        raise

    # 提交任务
    future = self._executor.submit(wrappedTask)
    self._tasks[taskId] = future

    # 初始化任务结果
    self._taskResults[taskId] = TaskResult(
      taskId=taskId,
      status=TaskStatus.PENDING
    )

    self.logger.info(f"任务已提交: {taskId}")
    return True

  def cancelTask(self, taskId: str) -> bool:
    """
    取消异步任务

    实现 IAsyncExecutor 接口。

    Args:
      taskId: 任务唯一标识

    Returns:
      bool: 是否取消成功
    """
    with self._lock:
      if taskId not in self._tasks:
        self.logger.warning(f"任务不存在: {taskId}")
        return False

      future = self._tasks[taskId]

      if future.done():
        self.logger.warning(f"任务已完成，无法取消: {taskId}")
        return False

      # 尝试取消任务
      cancelled = future.cancel()

      if cancelled:
        self._updateTaskStatus(taskId, TaskStatus.CANCELLED)
        self.logger.info(f"任务已取消: {taskId}")
      else:
        self.logger.warning(f"任务取消失败: {taskId}")

      return cancelled

  def getTaskStatus(self, taskId: str) -> Dict[str, Any]:
    """
    获取任务状态

    实现 IAsyncExecutor 接口。

    Args:
      taskId: 任务唯一标识

    Returns:
      Dict[str, Any]: 任务状态信息
    """
    if taskId not in self._taskResults:
      return {"error": "任务不存在"}

    result = self._taskResults[taskId]

    # 如果任务还在运行，尝试获取实际状态
    if taskId in self._tasks:
      future = self._tasks[taskId]
      if future.done():
        if result.status == TaskStatus.RUNNING:
          if future.exception():
            result.status = TaskStatus.FAILED
          else:
            result.status = TaskStatus.COMPLETED
            try:
              result.result = future.result()
            except:
              pass

    return result.toDict()

  def waitForTask(self, taskId: str, timeout: float = None) -> bool:
    """
    等待任务完成

    Args:
      taskId: 任务ID
      timeout: 超时时间（秒）

    Returns:
      bool: 是否在超时前完成
    """
    if taskId not in self._tasks:
      return False

    future = self._tasks[taskId]
    try:
      future.result(timeout=timeout)
      return True
    except:
      return False

  def getAllTaskStatus(self) -> Dict[str, Dict[str, Any]]:
    """
    获取所有任务状态

    Returns:
      Dict[str, Dict[str, Any]]: 所有任务状态
    """
    return {taskId: self.getTaskStatus(taskId) for taskId in self._tasks}

  def cleanupCompletedTasks(self, keepCount: int = 10) -> int:
    """
    清理已完成的任务

    Args:
      keepCount: 保留的已完成任务数量

    Returns:
      int: 清理的任务数量
    """
    cleanedCount = 0

    with self._lock:
      completedTasks = [
        taskId for taskId, future in self._tasks.items()
        if future.done()
      ]

      # 保留最新的 keepCount 个已完成任务
      tasksToRemove = completedTasks[:-keepCount] if len(completedTasks) > keepCount else []

      for taskId in tasksToRemove:
        del self._tasks[taskId]
        if taskId in self._taskResults:
          del self._taskResults[taskId]
        if taskId in self._taskCallbacks:
          del self._taskCallbacks[taskId]
        cleanedCount += 1

    if cleanedCount > 0:
      self.logger.info(f"清理了 {cleanedCount} 个已完成任务")

    return cleanedCount

  def shutdown(self, wait: bool = True):
    """
    关闭执行器

    Args:
      wait: 是否等待所有任务完成
    """
    self.logger.info("正在关闭异步执行器...")
    self._executor.shutdown(wait=wait)
    self.logger.info("异步执行器已关闭")

  def _generateTaskId(self) -> str:
    """生成唯一任务ID"""
    self._taskCounter += 1
    return f"task_{self._taskCounter}_{uuid.uuid4().hex[:8]}"

  def _updateTaskStatus(
    self,
    taskId: str,
    status: TaskStatus,
    result: Any = None,
    error: Exception = None
  ):
    """
    更新任务状态

    Args:
      taskId: 任务ID
      status: 新状态
      result: 结果
      error: 错误
    """
    if taskId not in self._taskResults:
      return

    taskResult = self._taskResults[taskId]
    taskResult.status = status

    if result is not None:
      taskResult.result = result

    if error is not None:
      taskResult.error = error

    if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
      taskResult.endTime = time.time()


# 创建默认执行器实例
_defaultExecutor = None


def getAsyncExecutor() -> QtAsyncExecutor:
  """
  获取默认异步执行器实例

  Returns:
    QtAsyncExecutor: 异步执行器实例
  """
  global _defaultExecutor

  if _defaultExecutor is None:
    _defaultExecutor = QtAsyncExecutor()

  return _defaultExecutor


# 导出所有类和函数
__all__ = [
  'QtAsyncExecutor',
  'TaskStatus',
  'TaskResult',
  'IProgressReporter',
  'ProgressReporter',
  'getAsyncExecutor',
]
