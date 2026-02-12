#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
异步执行框架

提供在UI线程中安全执行耗时操作的能力，包括：
- 异步任务执行
- 任务队列管理
- 进度回调
- 取消操作
"""

import logging
import threading
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = auto()      # 等待中
    RUNNING = auto()      # 运行中
    COMPLETED = auto()    # 已完成
    FAILED = auto()       # 失败
    CANCELLED = auto()    # 已取消


@dataclass
class TaskInfo:
    """
    任务信息
    
    Attributes:
        task_id: 任务唯一ID
        name: 任务名称
        status: 当前状态
        progress: 进度(0-100)
        result: 执行结果
        error: 错误信息
        created_at: 创建时间
        started_at: 开始时间
        completed_at: 完成时间
    """
    task_id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=lambda: __import__('time').time())
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """获取执行时长"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return __import__('time').time() - self.started_at
        return None


class IAsyncExecutor(ABC):
    """
    异步执行器接口
    
    定义异步任务执行的标准接口。
    """
    
    @abstractmethod
    def submit(
        self,
        task: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> str:
        """
        提交任务
        
        Args:
            task: 要执行的任务函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            str: 任务ID
        """
        pass
    
    @abstractmethod
    def cancel(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        pass
    
    @abstractmethod
    def get_status(self, task_id: str) -> Optional[TaskInfo]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskInfo]: 任务信息
        """
        pass


class AsyncExecutor(IAsyncExecutor):
    """
    异步执行器实现
    
    使用线程池执行异步任务，支持：
    - 任务提交和管理
    - 进度回调
    - 取消操作
    - 结果获取
    
    单例模式确保全局唯一。
    
    示例:
        >>> executor = AsyncExecutor.get_instance()
        >>> 
        >>> def long_task(progress_callback):
        ...     for i in range(100):
        ...         progress_callback(i)
        ...         time.sleep(0.1)
        ...     return "Done"
        >>> 
        >>> task_id = executor.submit(long_task)
        >>> status = executor.get_status(task_id)
    """
    
    _instance: Optional['AsyncExecutor'] = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool = False
    
    def __new__(cls, max_workers: int = 4) -> 'AsyncExecutor':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    logger.debug("AsyncExecutor instance created")
        return cls._instance
    
    def __init__(self, max_workers: int = 4):
        """初始化执行器（仅执行一次）"""
        if AsyncExecutor._initialized:
            return
        
        self._max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: Dict[str, TaskInfo] = {}
        self._futures: Dict[str, Future] = {}
        self._callbacks: Dict[str, List[Callable[[TaskInfo], None]]] = defaultdict(list)
        self._progress_callbacks: Dict[str, Callable[[float], None]] = {}
        
        AsyncExecutor._initialized = True
        logger.info(f"AsyncExecutor initialized with {max_workers} workers")
    
    @classmethod
    def get_instance(cls, max_workers: int = 4) -> 'AsyncExecutor':
        """
        获取单例实例
        
        Args:
            max_workers: 最大工作线程数（首次创建时有效）
            
        Returns:
            AsyncExecutor: 执行器实例
        """
        return cls(max_workers)
    
    def submit(
        self,
        task: Callable[..., Any],
        *args: Any,
        name: Optional[str] = None,
        on_complete: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_progress: Optional[Callable[[float], None]] = None,
        **kwargs: Any
    ) -> str:
        """
        提交任务
        
        Args:
            task: 要执行的任务函数
            *args: 位置参数
            name: 任务名称
            on_complete: 完成回调
            on_error: 错误回调
            on_progress: 进度回调
            **kwargs: 关键字参数
            
        Returns:
            str: 任务ID
        """
        task_id = str(uuid.uuid4())
        task_name = name or f"Task-{task_id[:8]}"
        
        # 创建任务信息
        task_info = TaskInfo(task_id=task_id, name=task_name)
        self._tasks[task_id] = task_info
        
        # 保存回调
        if on_progress:
            self._progress_callbacks[task_id] = on_progress
        
        # 包装任务函数
        def wrapped_task():
            return self._execute_task(task_id, task, *args, **kwargs)
        
        # 提交到线程池
        future = self._executor.submit(wrapped_task)
        self._futures[task_id] = future
        
        # 添加完成回调
        def on_future_done(f: Future):
            try:
                result = f.result()
                self._on_task_complete(task_id, result)
                if on_complete:
                    on_complete(result)
            except Exception as e:
                self._on_task_error(task_id, e)
                if on_error:
                    on_error(e)
        
        future.add_done_callback(on_future_done)
        
        logger.debug(f"Task submitted: {task_name} (ID: {task_id})")
        return task_id
    
    def _execute_task(
        self,
        task_id: str,
        task: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        执行任务
        
        Args:
            task_id: 任务ID
            task: 任务函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 任务结果
        """
        import time
        
        task_info = self._tasks[task_id]
        task_info.status = TaskStatus.RUNNING
        task_info.started_at = time.time()
        
        # 创建进度回调函数
        def progress_callback(value: float):
            task_info.progress = min(max(value, 0.0), 100.0)
            if task_id in self._progress_callbacks:
                self._progress_callbacks[task_id](task_info.progress)
        
        # 如果任务接受进度回调，传递给它
        if 'progress_callback' in task.__code__.co_varnames:
            kwargs['progress_callback'] = progress_callback
        
        try:
            result = task(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            raise
    
    def _on_task_complete(self, task_id: str, result: Any) -> None:
        """
        任务完成处理
        
        Args:
            task_id: 任务ID
            result: 执行结果
        """
        import time
        
        task_info = self._tasks.get(task_id)
        if task_info:
            task_info.status = TaskStatus.COMPLETED
            task_info.result = result
            task_info.progress = 100.0
            task_info.completed_at = time.time()
            
            logger.debug(f"Task completed: {task_info.name} (ID: {task_id})")
    
    def _on_task_error(self, task_id: str, error: Exception) -> None:
        """
        任务错误处理
        
        Args:
            task_id: 任务ID
            error: 异常对象
        """
        import time
        
        task_info = self._tasks.get(task_id)
        if task_info:
            task_info.status = TaskStatus.FAILED
            task_info.error = str(error)
            task_info.completed_at = time.time()
            
            logger.error(f"Task failed: {task_info.name} (ID: {task_id}): {error}")
    
    def cancel(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        future = self._futures.get(task_id)
        if future and not future.done():
            cancelled = future.cancel()
            if cancelled:
                task_info = self._tasks.get(task_id)
                if task_info:
                    import time
                    task_info.status = TaskStatus.CANCELLED
                    task_info.completed_at = time.time()
                
                logger.debug(f"Task cancelled: {task_id}")
            return cancelled
        return False
    
    def get_status(self, task_id: str) -> Optional[TaskInfo]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskInfo]: 任务信息
        """
        return self._tasks.get(task_id)
    
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        获取任务结果（阻塞）
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            
        Returns:
            Any: 任务结果
            
        Raises:
            TimeoutError: 超时
            Exception: 任务执行异常
        """
        future = self._futures.get(task_id)
        if not future:
            raise ValueError(f"Task {task_id} not found")
        
        return future.result(timeout=timeout)
    
    def get_all_tasks(self) -> List[TaskInfo]:
        """
        获取所有任务信息
        
        Returns:
            List[TaskInfo]: 任务列表
        """
        return list(self._tasks.values())
    
    def get_active_tasks(self) -> List[TaskInfo]:
        """
        获取活跃任务列表
        
        Returns:
            List[TaskInfo]: 活跃任务列表
        """
        return [
            task for task in self._tasks.values()
            if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
        ]
    
    def shutdown(self, wait: bool = True) -> None:
        """
        关闭执行器
        
        Args:
            wait: 是否等待所有任务完成
        """
        self._executor.shutdown(wait=wait)
        logger.info("AsyncExecutor shutdown")


# 便捷函数
def get_async_executor(max_workers: int = 4) -> AsyncExecutor:
    """
    获取全局异步执行器
    
    Args:
        max_workers: 最大工作线程数
        
    Returns:
        AsyncExecutor: 异步执行器
    """
    return AsyncExecutor.get_instance(max_workers)


def run_in_background(
    task: Callable[..., Any],
    *args: Any,
    **kwargs: Any
) -> str:
    """
    便捷函数：在后台运行任务
    
    Args:
        task: 任务函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        str: 任务ID
    """
    executor = get_async_executor()
    return executor.submit(task, *args, **kwargs)


# 导入defaultdict
from collections import defaultdict
