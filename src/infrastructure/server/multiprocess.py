#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多进程服务器架构

实现Master-Worker模式支持5000+并发:
- Master进程: 监听管理、连接分发
- Worker进程池: 实际请求处理
- 进程间通信: Queue机制
- 共享内存: Manager.dict
"""

import asyncio
import logging
import multiprocessing as mp
import os
import queue
import signal
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class WorkerState(Enum):
    """Worker进程状态"""
    IDLE = "idle"
    BUSY = "busy"
    STOPPING = "stopping"
    DEAD = "dead"


@dataclass 
class WorkerTask:
    """Worker任务"""
    task_id: str
    task_type: str
    data: Any
    timestamp: float = field(default_factory=time.time)


@dataclass
class WorkerResult:
    """Worker处理结果"""
    task_id: str
    success: bool
    data: Any
    error: Optional[str] = None


def _default_worker_handler(task: WorkerTask) -> WorkerResult:
    """默认任务处理器 - 在worker进程中执行"""
    # 模拟处理
    time.sleep(0.001)
    return WorkerResult(
        task_id=task.task_id,
        success=True,
        data=f"Processed: {task.data}"
    )


def worker_entry(
    worker_id: str,
    task_queue: mp.Queue,
    result_queue: mp.Queue,
    shared_stats: Any
):
    """
    Worker进程入口函数
    
    Args:
        worker_id: Worker ID
        task_queue: 任务队列
        result_queue: 结果队列
        shared_stats: 共享统计 (Manager.dict)
    """
    logger.info(f"Worker {worker_id} started, PID={os.getpid()}")
    
    # 更新状态
    shared_stats[f'worker_{worker_id}_state'] = 'IDLE'
    
    running = True
    request_count = 0
    
    def signal_handler(signum, frame):
        nonlocal running
        logger.info(f"Worker {worker_id} received signal {signum}")
        running = False
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    while running:
        try:
            # 接收任务
            try:
                task_dict = task_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            
            if task_dict is None:  # 退出信号
                break
            
            # 重建任务对象
            task = WorkerTask(**task_dict)
            
            # 更新状态为忙碌
            shared_stats[f'worker_{worker_id}_state'] = 'BUSY'
            
            # 处理任务 (使用默认handler)
            try:
                result = _default_worker_handler(task)
            except Exception as e:
                result = WorkerResult(
                    task_id=task.task_id,
                    success=False,
                    data=None,
                    error=str(e)
                )
            
            # 更新统计
            request_count += 1
            shared_stats['total_requests'] = shared_stats.get('total_requests', 0) + 1
            if not result.success:
                shared_stats['total_errors'] = shared_stats.get('total_errors', 0) + 1
            
            # 发送结果
            result_queue.put({
                'task_id': result.task_id,
                'success': result.success,
                'data': result.data,
                'error': result.error
            })
            
            # 更新状态为空闲
            shared_stats[f'worker_{worker_id}_state'] = 'IDLE'
            shared_stats[f'worker_{worker_id}_requests'] = request_count
            
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}")
            shared_stats['total_errors'] = shared_stats.get('total_errors', 0) + 1
    
    shared_stats[f'worker_{worker_id}_state'] = 'STOPPED'
    logger.info(f"Worker {worker_id} stopped, processed {request_count} requests")


class MasterProcess:
    """
    Master进程 - 管理Worker进程池
    
    示例:
        >>> master = MasterProcess(num_workers=4)
        >>> await master.start()
        >>> result = await master.submit_task(task_data)
        >>> await master.stop()
    """
    
    def __init__(
        self,
        num_workers: int = 4,
        max_connections: int = 5000
    ):
        self._num_workers = num_workers
        self._max_connections = max_connections
        
        self._workers: Dict[str, mp.Process] = {}
        self._task_queues: Dict[str, mp.Queue] = {}
        self._result_queue: Optional[mp.Queue] = None
        
        self._manager: Optional[mp.Manager] = None
        self._shared_stats: Optional[Any] = None
        
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None  # 新增: 健康检查任务
        self._pending_tasks: Dict[str, asyncio.Future] = {}
        self._task_counter = 0
        
        logger.info(f"MasterProcess initialized: workers={num_workers}")
    
    async def start(self) -> None:
        """启动Master和Worker进程"""
        if self._running:
            return
        
        self._running = True
        
        # 创建Manager和共享状态
        self._manager = mp.Manager()
        self._shared_stats = self._manager.dict()
        self._shared_stats['total_requests'] = 0
        self._shared_stats['total_errors'] = 0
        
        # 创建结果队列
        self._result_queue = mp.Queue(maxsize=10000)
        
        # 启动Worker进程
        for i in range(self._num_workers):
            worker_id = f"worker_{i}"
            await self._start_worker(worker_id)
        
        # 启动监控任务
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        # 启动健康检查任务
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info(f"MasterProcess started with {self._num_workers} workers")
    
    async def _start_worker(self, worker_id: str) -> bool:
        """启动单个Worker进程"""
        try:
            # 创建任务队列
            task_queue = mp.Queue(maxsize=1000)
            self._task_queues[worker_id] = task_queue
            
            # 启动进程
            process = mp.Process(
                target=worker_entry,
                args=(
                    worker_id,
                    task_queue,
                    self._result_queue,
                    self._shared_stats
                ),
                name=f"Worker-{worker_id}",
                daemon=True
            )
            process.start()
            
            self._workers[worker_id] = process
            logger.info(f"Worker {worker_id} started, PID={process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start worker {worker_id}: {e}")
            return False
    
    async def stop(self) -> None:
        """停止Master和所有Worker"""
        if not self._running:
            return
        
        self._running = False
        
        # 停止监控任务
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # 停止健康检查任务
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # 停止所有Worker
        for worker_id in list(self._workers.keys()):
            await self._stop_worker(worker_id)
        
        # 关闭Manager
        if self._manager:
            self._manager.shutdown()
        
        logger.info("MasterProcess stopped")
    
    async def _stop_worker(self, worker_id: str) -> None:
        """停止单个Worker"""
        if worker_id not in self._workers:
            return
        
        # 发送退出信号
        if worker_id in self._task_queues:
            try:
                self._task_queues[worker_id].put(None, timeout=1.0)
            except:
                pass
        
        # 等待进程结束
        process = self._workers[worker_id]
        if process.is_alive():
            process.join(timeout=5.0)
            if process.is_alive():
                process.terminate()
                process.join()
        
        del self._workers[worker_id]
        if worker_id in self._task_queues:
            del self._task_queues[worker_id]
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def submit_task(
        self,
        task_data: Any,
        task_type: str = "default",
        timeout: float = 30.0
    ) -> Optional[WorkerResult]:
        """提交任务"""
        if not self._running:
            return None
        
        # 生成任务ID
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{int(time.time()*1000)}"
        
        # 创建任务
        task = WorkerTask(
            task_id=task_id,
            task_type=task_type,
            data=task_data
        )
        
        # 选择Worker (轮询)
        worker_id = self._select_worker()
        if not worker_id:
            logger.warning("No available worker")
            return None
        
        # 创建Future等待结果
        future = asyncio.get_event_loop().create_future()
        self._pending_tasks[task_id] = future
        
        # 发送任务
        try:
            self._task_queues[worker_id].put({
                'task_id': task.task_id,
                'task_type': task.task_type,
                'data': task.data,
                'timestamp': task.timestamp
            }, timeout=1.0)
        except queue.Full:
            del self._pending_tasks[task_id]
            return None
        
        # 等待结果
        try:
            result_dict = await asyncio.wait_for(future, timeout=timeout)
            return WorkerResult(**result_dict)
        except asyncio.TimeoutError:
            # 修复: 取消Future避免内存泄漏
            if task_id in self._pending_tasks:
                future = self._pending_tasks.pop(task_id)
                if not future.done():
                    future.cancel()
            return WorkerResult(
                task_id=task_id,
                success=False,
                data=None,
                error="Task timeout"
            )
    
    def _select_worker(self) -> Optional[str]:
        """选择可用的Worker (轮询)"""
        if not self._workers:
            return None
        
        worker_ids = list(self._workers.keys())
        index = self._task_counter % len(worker_ids)
        return worker_ids[index]
    
    async def _monitor_loop(self) -> None:
        """监控循环 - 收集结果"""
        while self._running:
            try:
                # 修复: 使用阻塞get替代empty()检查，避免竞争条件
                try:
                    result_dict = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self._result_queue.get,
                        True,   # block
                        0.1     # timeout
                    )
                    
                    task_id = result_dict.get('task_id')
                    if task_id and task_id in self._pending_tasks:
                        future = self._pending_tasks.pop(task_id)
                        if not future.done():
                            future.set_result(result_dict)
                            
                except queue.Empty:
                    await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
    
    async def _health_check_loop(self) -> None:
        """健康检查循环 - 监控Worker状态并自动重启"""
        check_interval = 10.0  # 每10秒检查一次
        
        while self._running:
            try:
                await asyncio.sleep(check_interval)
                
                if not self._running:
                    break
                
                # 检查每个Worker的状态
                for worker_id in list(self._workers.keys()):
                    process = self._workers.get(worker_id)
                    
                    if process is None:
                        continue
                    
                    # 检查进程是否还在运行
                    if not process.is_alive():
                        logger.warning(f"Worker {worker_id} is dead, restarting...")
                        
                        # 停止死掉的Worker
                        await self._stop_worker(worker_id)
                        
                        # 重启Worker
                        success = await self._start_worker(worker_id)
                        if success:
                            logger.info(f"Worker {worker_id} restarted successfully")
                        else:
                            logger.error(f"Failed to restart worker {worker_id}")
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self._shared_stats:
            return {}
        
        stats = {
            'running': self._running,
            'num_workers': self._num_workers,
            'active_workers': len(self._workers),
            'pending_tasks': len(self._pending_tasks),
            'total_requests': self._shared_stats.get('total_requests', 0),
            'total_errors': self._shared_stats.get('total_errors', 0),
        }
        
        # Worker状态
        for worker_id in self._workers.keys():
            stats[f'{worker_id}_state'] = self._shared_stats.get(f'worker_{worker_id}_state', 'unknown')
            stats[f'{worker_id}_requests'] = self._shared_stats.get(f'worker_{worker_id}_requests', 0)
        
        return stats


class MultiProcessServer:
    """多进程服务器 - 对外提供统一接口"""
    
    def __init__(
        self,
        num_workers: int = 4,
        max_connections: int = 5000
    ):
        self._master = MasterProcess(
            num_workers=num_workers,
            max_connections=max_connections
        )
    
    async def start(self) -> None:
        await self._master.start()
    
    async def stop(self) -> None:
        await self._master.stop()
    
    async def handle_request(
        self,
        data: Any,
        task_type: str = "default",
        timeout: float = 30.0
    ) -> Optional[WorkerResult]:
        return await self._master.submit_task(data, task_type, timeout)
    
    def get_stats(self) -> Dict[str, Any]:
        return self._master.get_stats()


def create_multiprocess_server(
    num_workers: int = 4,
    **kwargs
) -> MultiProcessServer:
    """创建多进程服务器"""
    return MultiProcessServer(num_workers=num_workers, **kwargs)
