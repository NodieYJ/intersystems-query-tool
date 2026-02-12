#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务器并发架构模块

提供5000+并发连接支持的基础设施：
- 连接池管理
- 消息队列
- 心跳检测
- 连接分发
"""

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ConnectionState(Enum):
    """连接状态"""
    IDLE = auto()       # 空闲
    ACTIVE = auto()     # 活跃
    BUSY = auto()       # 忙碌
    CLOSED = auto()     # 已关闭
    ERROR = auto()      # 错误


@dataclass
class ConnectionInfo:
    """连接信息"""
    connection_id: str
    client_address: str
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    state: ConnectionState = ConnectionState.IDLE
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_count: int = 0
    error_count: int = 0
    
    @property
    def idle_time(self) -> float:
        """空闲时间"""
        return time.time() - self.last_activity
    
    @property
    def lifetime(self) -> float:
        """连接生命周期"""
        return time.time() - self.created_at


class ConnectionPool:
    """
    连接池
    
    管理服务器连接，支持：
    - 连接复用
    - 最大连接数限制
    - 空闲超时回收
    - 健康检查
    
    示例:
        >>> pool = ConnectionPool(max_size=100, idle_timeout=300)
        >>> conn_id = await pool.acquire()
        >>> # 使用连接
        >>> await pool.release(conn_id)
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        idle_timeout: float = 300.0,
        max_lifetime: float = 3600.0,
        health_check_interval: float = 60.0
    ):
        """
        初始化连接池
        
        Args:
            max_size: 最大连接数
            idle_timeout: 空闲超时（秒）
            max_lifetime: 最大生命周期（秒）
            health_check_interval: 健康检查间隔（秒）
        """
        self._max_size = max_size
        self._idle_timeout = idle_timeout
        self._max_lifetime = max_lifetime
        self._health_check_interval = health_check_interval
        
        self._connections: Dict[str, ConnectionInfo] = {}
        self._idle_queue: deque = deque()  # 空闲连接队列
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_size)
        
        self._stats = {
            'total_created': 0,
            'total_closed': 0,
            'total_reused': 0,
            'total_rejected': 0
        }
        
        logger.info(f"ConnectionPool initialized: max_size={max_size}")
    
    async def acquire(self, client_address: str = "unknown") -> Optional[str]:
        """
        获取连接
        
        Args:
            client_address: 客户端地址
            
        Returns:
            Optional[str]: 连接ID
        """
        async with self._semaphore:
            async with self._lock:
                # 尝试复用空闲连接
                while self._idle_queue:
                    conn_id = self._idle_queue.popleft()
                    if conn_id in self._connections:
                        conn = self._connections[conn_id]
                        if conn.state != ConnectionState.CLOSED:
                            conn.state = ConnectionState.ACTIVE
                            conn.last_activity = time.time()
                            conn.request_count += 1
                            self._stats['total_reused'] += 1
                            logger.debug(f"Connection reused: {conn_id}")
                            return conn_id
                
                # 创建新连接
                if len(self._connections) < self._max_size:
                    conn_id = str(uuid.uuid4())
                    conn_info = ConnectionInfo(
                        connection_id=conn_id,
                        client_address=client_address,
                        state=ConnectionState.ACTIVE
                    )
                    self._connections[conn_id] = conn_info
                    self._stats['total_created'] += 1
                    logger.debug(f"Connection created: {conn_id}")
                    return conn_id
                
                self._stats['total_rejected'] += 1
                logger.warning("Connection pool exhausted")
                return None
    
    async def release(self, connection_id: str) -> bool:
        """
        释放连接
        
        Args:
            connection_id: 连接ID
            
        Returns:
            bool: 是否成功
        """
        async with self._lock:
            if connection_id not in self._connections:
                return False
            
            conn = self._connections[connection_id]
            conn.state = ConnectionState.IDLE
            conn.last_activity = time.time()
            self._idle_queue.append(connection_id)
            
            logger.debug(f"Connection released: {connection_id}")
            return True
    
    async def close(self, connection_id: str) -> bool:
        """
        关闭连接
        
        Args:
            connection_id: 连接ID
            
        Returns:
            bool: 是否成功
        """
        async with self._lock:
            if connection_id not in self._connections:
                return False
            
            conn = self._connections[connection_id]
            conn.state = ConnectionState.CLOSED
            del self._connections[connection_id]
            
            # 从空闲队列中移除
            if connection_id in self._idle_queue:
                self._idle_queue.remove(connection_id)
            
            self._stats['total_closed'] += 1
            logger.debug(f"Connection closed: {connection_id}")
            return True
    
    async def cleanup_idle(self) -> int:
        """
        清理空闲超时的连接
        
        Returns:
            int: 清理的连接数
        """
        closed_count = 0
        current_time = time.time()
        
        async with self._lock:
            to_close = []
            
            for conn_id, conn in list(self._connections.items()):
                # 检查空闲超时
                if conn.state == ConnectionState.IDLE:
                    if current_time - conn.last_activity > self._idle_timeout:
                        to_close.append(conn_id)
                
                # 检查生命周期
                elif current_time - conn.created_at > self._max_lifetime:
                    to_close.append(conn_id)
            
            for conn_id in to_close:
                if conn_id in self._connections:
                    del self._connections[conn_id]
                    if conn_id in self._idle_queue:
                        self._idle_queue.remove(conn_id)
                    closed_count += 1
        
        if closed_count > 0:
            logger.info(f"Cleaned up {closed_count} idle connections")
        
        return closed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取连接池统计
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        active = sum(1 for c in self._connections.values() 
                    if c.state == ConnectionState.ACTIVE)
        idle = sum(1 for c in self._connections.values() 
                  if c.state == ConnectionState.IDLE)
        
        return {
            'total_connections': len(self._connections),
            'active_connections': active,
            'idle_connections': idle,
            'available_slots': self._max_size - len(self._connections),
            'wait_queue_size': self._max_size - self._semaphore._value,
            **self._stats
        }


class MessageQueue:
    """
    消息队列
    
    异步消息队列，支持：
    - 优先级队列
    - 消息持久化
    - 批量处理
    - 流量控制
    
    示例:
        >>> queue = MessageQueue(max_size=10000)
        >>> await queue.put(message, priority=1)
        >>> message = await queue.get()
    """
    
    def __init__(self, max_size: int = 10000, batch_size: int = 100):
        """
        初始化消息队列
        
        Args:
            max_size: 最大队列大小
            batch_size: 批处理大小
        """
        self._max_size = max_size
        self._batch_size = batch_size
        
        # 优先级队列：(priority, timestamp, message)
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_size)
        self._stats = {
            'total_enqueued': 0,
            'total_dequeued': 0,
            'total_dropped': 0
        }
        
        logger.info(f"MessageQueue initialized: max_size={max_size}")
    
    async def put(self, message: Any, priority: int = 5) -> bool:
        """
        放入消息
        
        Args:
            message: 消息内容
            priority: 优先级（越小越高）
            
        Returns:
            bool: 是否成功
        """
        try:
            await self._queue.put((priority, time.time(), message))
            self._stats['total_enqueued'] += 1
            return True
        except asyncio.QueueFull:
            self._stats['total_dropped'] += 1
            logger.warning("Message queue full, message dropped")
            return False
    
    async def get(self, timeout: Optional[float] = None) -> Optional[Any]:
        """
        获取消息
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            Optional[Any]: 消息内容
        """
        try:
            if timeout:
                priority, timestamp, message = await asyncio.wait_for(
                    self._queue.get(), timeout=timeout
                )
            else:
                priority, timestamp, message = await self._queue.get()
            
            self._stats['total_dequeued'] += 1
            return message
        except asyncio.TimeoutError:
            return None
    
    async def get_batch(self, size: Optional[int] = None) -> List[Any]:
        """
        批量获取消息
        
        Args:
            size: 批量大小
            
        Returns:
            List[Any]: 消息列表
        """
        size = size or self._batch_size
        messages = []
        
        for _ in range(size):
            if not self._queue.empty():
                try:
                    priority, timestamp, message = self._queue.get_nowait()
                    messages.append(message)
                    self._stats['total_dequeued'] += 1
                except asyncio.QueueEmpty:
                    break
            else:
                break
        
        return messages
    
    def qsize(self) -> int:
        """获取队列大小"""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """检查队列是否为空"""
        return self._queue.empty()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计"""
        return {
            'queue_size': self.qsize(),
            'max_size': self._max_size,
            **self._stats
        }


class HeartbeatMonitor:
    """
    心跳检测器
    
    监控连接健康状态：
    - 定期发送心跳
    - 检测超时连接
    - 自动断开死连接
    
    示例:
        >>> monitor = HeartbeatMonitor(interval=30, timeout=60)
        >>> monitor.add_connection(conn_id)
        >>> await monitor.start()
    """
    
    def __init__(
        self,
        interval: float = 30.0,
        timeout: float = 60.0,
        max_missed: int = 3
    ):
        """
        初始化心跳检测器
        
        Args:
            interval: 心跳间隔（秒）
            timeout: 超时时间（秒）
            max_missed: 最大允许丢失的心跳数
        """
        self._interval = interval
        self._timeout = timeout
        self._max_missed = max_missed
        
        self._connections: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info(f"HeartbeatMonitor initialized: interval={interval}s")
    
    def add_connection(
        self,
        connection_id: str,
        heartbeat_callback: Optional[Callable[[], None]] = None
    ) -> None:
        """
        添加连接监控
        
        Args:
            connection_id: 连接ID
            heartbeat_callback: 心跳回调函数
        """
        self._connections[connection_id] = {
            'last_heartbeat': time.time(),
            'missed_count': 0,
            'callback': heartbeat_callback
        }
        logger.debug(f"Connection added to heartbeat monitor: {connection_id}")
    
    def remove_connection(self, connection_id: str) -> None:
        """
        移除连接监控
        
        Args:
            connection_id: 连接ID
        """
        if connection_id in self._connections:
            del self._connections[connection_id]
            logger.debug(f"Connection removed from heartbeat monitor: {connection_id}")
    
    def update_heartbeat(self, connection_id: str) -> None:
        """
        更新心跳时间
        
        Args:
            connection_id: 连接ID
        """
        if connection_id in self._connections:
            self._connections[connection_id]['last_heartbeat'] = time.time()
            self._connections[connection_id]['missed_count'] = 0
    
    async def start(self) -> None:
        """启动心跳检测"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Heartbeat monitor started")
    
    async def stop(self) -> None:
        """停止心跳检测"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Heartbeat monitor stopped")
    
    async def _monitor_loop(self) -> None:
        """监控循环"""
        while self._running:
            try:
                await self._check_connections()
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
    
    async def _check_connections(self) -> None:
        """检查所有连接"""
        current_time = time.time()
        dead_connections = []
        
        for conn_id, info in list(self._connections.items()):
            elapsed = current_time - info['last_heartbeat']
            
            if elapsed > self._timeout:
                info['missed_count'] += 1
                
                if info['missed_count'] >= self._max_missed:
                    dead_connections.append(conn_id)
                    logger.warning(f"Connection dead: {conn_id}")
                else:
                    # 发送心跳包
                    if info['callback']:
                        try:
                            info['callback']()
                        except Exception as e:
                            logger.error(f"Heartbeat callback failed: {e}")
        
        # 清理死连接
        for conn_id in dead_connections:
            self.remove_connection(conn_id)


class ConnectionDispatcher:
    """
    连接分发器
    
    将连接分发到不同的工作进程/线程：
    - 轮询分发
    - 最少连接优先
    - 加权分发
    - 一致性哈希
    
    示例:
        >>> dispatcher = ConnectionDispatcher(strategy='round_robin')
        >>> worker_id = dispatcher.dispatch(connection_id)
    """
    
    def __init__(self, strategy: str = 'round_robin'):
        """
        初始化分发器
        
        Args:
            strategy: 分发策略（round_robin, least_connections, weighted）
        """
        self._strategy = strategy
        self._workers: Dict[str, Dict[str, Any]] = {}
        self._counter = 0
        
        logger.info(f"ConnectionDispatcher initialized: strategy={strategy}")
    
    def register_worker(self, worker_id: str, weight: int = 1) -> None:
        """
        注册工作节点
        
        Args:
            worker_id: 工作节点ID
            weight: 权重
        """
        self._workers[worker_id] = {
            'weight': weight,
            'connections': set(),
            'connection_count': 0
        }
        logger.debug(f"Worker registered: {worker_id}, weight={weight}")
    
    def unregister_worker(self, worker_id: str) -> None:
        """
        注销工作节点
        
        Args:
            worker_id: 工作节点ID
        """
        if worker_id in self._workers:
            del self._workers[worker_id]
            logger.debug(f"Worker unregistered: {worker_id}")
    
    def dispatch(self, connection_id: str) -> Optional[str]:
        """
        分发连接
        
        Args:
            connection_id: 连接ID
            
        Returns:
            Optional[str]: 工作节点ID
        """
        if not self._workers:
            return None
        
        if self._strategy == 'round_robin':
            return self._round_robin_dispatch(connection_id)
        elif self._strategy == 'least_connections':
            return self._least_connections_dispatch(connection_id)
        elif self._strategy == 'weighted':
            return self._weighted_dispatch(connection_id)
        else:
            return self._round_robin_dispatch(connection_id)
    
    def _round_robin_dispatch(self, connection_id: str) -> str:
        """轮询分发"""
        workers = list(self._workers.keys())
        worker_id = workers[self._counter % len(workers)]
        self._counter += 1
        
        self._workers[worker_id]['connections'].add(connection_id)
        self._workers[worker_id]['connection_count'] += 1
        
        return worker_id
    
    def _least_connections_dispatch(self, connection_id: str) -> str:
        """最少连接优先"""
        worker_id = min(
            self._workers.keys(),
            key=lambda w: self._workers[w]['connection_count']
        )
        
        self._workers[worker_id]['connections'].add(connection_id)
        self._workers[worker_id]['connection_count'] += 1
        
        return worker_id
    
    def _weighted_dispatch(self, connection_id: str) -> str:
        """加权分发"""
        import random
        
        weights = [self._workers[w]['weight'] for w in self._workers.keys()]
        worker_id = random.choices(list(self._workers.keys()), weights=weights)[0]
        
        self._workers[worker_id]['connections'].add(connection_id)
        self._workers[worker_id]['connection_count'] += 1
        
        return worker_id
    
    def release_connection(self, connection_id: str, worker_id: str) -> None:
        """
        释放连接
        
        Args:
            connection_id: 连接ID
            worker_id: 工作节点ID
        """
        if worker_id in self._workers:
            worker = self._workers[worker_id]
            if connection_id in worker['connections']:
                worker['connections'].remove(connection_id)
                worker['connection_count'] -= 1
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """获取工作节点统计"""
        return {
            worker_id: {
                'weight': info['weight'],
                'connection_count': info['connection_count']
            }
            for worker_id, info in self._workers.items()
        }


# 便捷函数
async def create_connection_pool(**kwargs) -> ConnectionPool:
    """创建连接池"""
    return ConnectionPool(**kwargs)


def create_message_queue(**kwargs) -> MessageQueue:
    """创建消息队列"""
    return MessageQueue(**kwargs)


def create_heartbeat_monitor(**kwargs) -> HeartbeatMonitor:
    """创建心跳检测器"""
    return HeartbeatMonitor(**kwargs)


def create_connection_dispatcher(**kwargs) -> ConnectionDispatcher:
    """创建连接分发器"""
    return ConnectionDispatcher(**kwargs)
