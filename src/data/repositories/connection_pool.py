#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库连接池模块

提供连接池管理功能，包括：
- 连接复用
- 健康检查
- 超时清理
- 泄漏检测
"""

import logging
import threading
import time
import traceback
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from contextlib import contextmanager

from src.data.repositories.driver_factory import (
  DatabaseDriverFactory,
  DatabaseDriverType,
  get_driver_factory,
)
from src.infrastructure.exceptions import ConnectionException

logger = logging.getLogger(__name__)

# 连接最大存活时间（秒）
CONNECTION_MAX_LIFETIME = 3600


class ConnectionPool:
  """
  数据库连接池类

  支持连接健康检查、超时清理、自动释放。
  使用信号量控制并发连接数，支持有界等待。
  """

  # 默认连接超时 (秒)
  DEFAULT_CONNECTION_TIMEOUT = 30
  # 默认查询超时 (秒)
  DEFAULT_QUERY_TIMEOUT = 30
  # 默认获取连接等待超时 (秒)
  DEFAULT_ACQUIRE_TIMEOUT = 5.0

  def __init__(
    self,
    max_connections: int = 10,
    timeout: int = 30,
    query_timeout: Optional[int] = None,
    acquire_timeout: Optional[float] = None
  ):
    """
    初始化连接池

    Args:
      max_connections: 最大连接数
      timeout: 连接超时时间（秒）
      query_timeout: 查询超时时间（秒），默认与连接超时相同
      acquire_timeout: 获取连接等待超时（秒），默认5秒
    """
    self.max_connections = max_connections
    self.timeout = timeout
    self.query_timeout = query_timeout if query_timeout is not None else timeout
    self.acquire_timeout = acquire_timeout if acquire_timeout is not None else self.DEFAULT_ACQUIRE_TIMEOUT
    self.connections = []
    self.lock = threading.RLock()
    self.logger = logging.getLogger(__name__)

    # 信号量控制并发连接获取
    self.semaphore = threading.Semaphore(max_connections)

    # 跟踪连接创建时间（用于总存活时间限制）
    self._creation_times: Dict[int, datetime] = {}

    # 活跃连接跟踪（用于泄漏检测）
    self._active_connections: Dict[int, Dict[str, Any]] = {}
    self._leak_check_threshold = 300  # 5秒

    # 启动定期清理线程
    self._cleanup_thread = None
    self._start_cleanup_thread()

  def get_connection(
    self, connection_params: Dict[str, Any]
  ) -> Optional[Tuple[Any, Any]]:
    """
    获取数据库连接（使用信号量控制，支持有界等待）

    Args:
      connection_params: 连接参数

    Returns:
      Optional[Tuple[Any, Any]]: (connection, cursor) 元组，超时返回 None
    """
    # 尝试获取信号量（控制同时获取的连接数）
    acquired = False
    try:
      if not self.semaphore.acquire(timeout=self.acquire_timeout):
        self.logger.warning(f"获取连接超时（等待{self.acquire_timeout}秒）")
        return None
      acquired = True
    except Exception as e:
      self.logger.error(f"获取信号量失败: {e}")
      return None

    with self.lock:
      # 尝试从连接池获取可用连接
      for conn_info in self.connections:
        conn, cursor, params, last_used = conn_info
        # 检查连接是否匹配参数且未超时
        if params == connection_params and self._is_connection_valid(conn):
          # 更新最后使用时间
          conn_info[3] = datetime.now()
          self.logger.debug("从连接池获取连接")
          self._track_active_connection(conn, connection_params)
          return conn, cursor

      # 如果没有可用连接且未达到最大连接数，创建新连接
      if len(self.connections) < self.max_connections:
        self.logger.info("创建新的数据库连接")
        conn_cursor = self._create_connection(connection_params)
        if conn_cursor:
          conn, cursor = conn_cursor
          self.connections.append([conn, cursor, connection_params, datetime.now()])
          self._creation_times[id(conn)] = datetime.now()
          self._track_active_connection(conn, connection_params)
          self.logger.debug("新连接已创建并加入连接池")
          return conn, cursor

      # 连接池已满，释放信号量并返回 None
      self.logger.warning("连接池已满，无法获取连接")
      return None

  def _track_active_connection(self, conn: Any, params: Dict[str, Any]) -> None:
    """
    跟踪活跃连接（用于泄漏检测）

    Args:
      conn: 数据库连接
      params: 连接参数（脱敏）
    """
    self._active_connections[id(conn)] = {
      'thread_id': threading.get_ident(),
      'timestamp': time.time(),
      'params': '***'  # 脱敏
    }

  def release_connection(self, connection: Any) -> None:
    """
    释放连接回连接池（不健康则关闭）

    Args:
      connection: 数据库连接
    """
    # 从活跃连接中移除
    self._active_connections.pop(id(connection), None)

    with self.lock:
      for i, conn_info in enumerate(self.connections):
        conn, cursor, _, _ = conn_info
        if conn == connection:
          # 检查连接健康状态
          if not self._is_connection_healthy(conn):
            # 不健康则关闭并移除
            self._close_connection_safe(conn, cursor, i)
            del self.connections[i]
            # 释放信号量
            self.semaphore.release()
            return

          # 健康的连接标记为未使用并更新时间
          conn_info[3] = datetime.now()
          self.logger.debug(f"连接 #{i} 已释放回连接池")
          break

    # 释放信号量
    self.semaphore.release()

  def _close_connection_safe(self, conn: Any, cursor: Any, index: int) -> None:
    """
    安全关闭连接

    Args:
      conn: 数据库连接
      cursor: 数据库游标
      index: 连接索引（用于日志）
    """
    for name, obj in [("cursor", cursor), ("connection", conn)]:
      if obj is not None:
        try:
          obj.close()
          self.logger.debug(f"已关闭 {name} #{index}")
        except Exception as e:
          self.logger.warning(f"关闭 {name} #{index} 时出现异常: {e}")

  def close_all_connections(self) -> None:
    """
    关闭所有连接
    """
    with self.lock:
      for conn_info in self.connections:
        conn, cursor, _, _ = conn_info
        self._close_connection_safe(conn, cursor, -1)

      self.connections.clear()
      self._creation_times.clear()
      self._active_connections.clear()
      self.logger.info("所有连接已关闭")

  def _sanitize_params(self, params: Optional[List[Any]]) -> Optional[List[Any]]:
    """
    脱敏参数用于日志和异常信息

    假设密码是第5个参数（索引4）

    Args:
      params: 原始参数列表

    Returns:
      Optional[List[Any]]: 脱敏后的参数列表
    """
    if not params:
      return None

    sanitized = []
    for i, param in enumerate(params):
      if i == 4:  # 密码参数（假设在第5个位置）
        sanitized.append("***")
      else:
        sanitized.append(param)

    return sanitized

  def _create_connection(
    self, connection_params: Dict[str, Any]
  ) -> Optional[Tuple[Any, Any]]:
    """
    创建数据库连接

    Args:
      connection_params: 连接参数

    Returns:
      Optional[Tuple[Any, Any]]: (connection, cursor) 元组
    """
    try:
      # 使用驱动工厂创建连接
      factory = get_driver_factory()
      return factory.create_connection(connection_params)

    except Exception as e:
      self.logger.error(f"创建连接失败: {str(e)}")
      return None

  def _is_connection_valid(self, connection: Any) -> bool:
    """
    检查连接是否有效

    Args:
      connection: 数据库连接

    Returns:
      bool: 连接是否有效
    """
    try:
      # 执行简单查询测试连接
      if hasattr(connection, "cursor"):
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
      elif hasattr(connection, "execute"):
        connection.execute("SELECT 1")
        # 根据不同驱动的API获取结果
        if hasattr(connection, "next"):
          connection.next()
        elif hasattr(connection, "fetchone"):
          connection.fetchone()
      return True
    except Exception as e:
      self.logger.warning(f"连接无效: {str(e)}")
      return False

  def _start_cleanup_thread(self) -> None:
    """启动定期清理线程"""
    def cleanup_worker():
      while True:
        time.sleep(60)  # 每分钟清理一次
        try:
          self.cleanup_expired_connections()
        except Exception as e:
          self.logger.error(f"清理线程出错: {e}")

    self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    self._cleanup_thread.start()
    self.logger.debug("连接池清理线程已启动")

  def _is_connection_healthy(self, connection: Any) -> bool:
    """
    检查连接是否健康（支持is_connected方法）

    Args:
      connection: 数据库连接对象

    Returns:
      bool: 连接是否健康
    """
    try:
      # 检查连接是否有is_connected方法
      if hasattr(connection, 'is_connected'):
        return connection.is_connected()

      # 否则使用现有的连接有效性检查
      return self._is_connection_valid(connection)
    except Exception as e:
      self.logger.warning(f"连接健康检查失败: {e}")
      return False

  def _get_expired_connections(self) -> List[int]:
    """
    获取已过期的连接索引列表

    检查空闲超时和总存活时间限制

    Returns:
      List[int]: 过期连接索引列表
    """
    expired = []
    current_time = datetime.now()

    for i, conn_info in enumerate(self.connections):
      conn, cursor, params, last_used = conn_info

      # 检查空闲超时
      idle_timeout = (current_time - last_used).total_seconds()
      if idle_timeout > self.timeout:
        expired.append(i)
        continue

      # 检查总存活时间
      conn_id = id(conn)
      if conn_id in self._creation_times:
        lifetime = (current_time - self._creation_times[conn_id]).total_seconds()
        if lifetime > CONNECTION_MAX_LIFETIME:
          self.logger.info(f"连接 #{i} 超过最大存活时间 ({CONNECTION_MAX_LIFETIME}秒)")
          expired.append(i)

    return expired

  def cleanup_expired_connections(self) -> int:
    """
    清理所有过期的连接

    Returns:
      int: 清理的连接数
    """
    cleaned_count = 0

    with self.lock:
      expired_indices = self._get_expired_connections()

      # 逆序删除，避免索引变化
      for i in sorted(expired_indices, reverse=True):
        try:
          conn_info = self.connections[i]
          conn, cursor, _, _ = conn_info

          # 从创建时间跟踪中移除
          conn_id = id(conn)
          self._creation_times.pop(conn_id, None)

          # 关闭连接
          self._close_connection_safe(conn, cursor, i)

          del self.connections[i]
          cleaned_count += 1
          self.logger.debug(f"清理过期连接 #{i}")
        except Exception as e:
          self.logger.error(f"清理连接失败 #{i}: {e}")

    if cleaned_count > 0:
      self.logger.info(f"清理了 {cleaned_count} 个过期连接")

    return cleaned_count

  def detect_leaks(self) -> List[Dict[str, Any]]:
    """
    检测潜在泄漏的连接

    Returns:
      List[Dict[str, Any]]: 泄漏连接信息列表
    """
    leaked = []
    current_time = time.time()

    for conn_id, info in self._active_connections.items():
      age = current_time - info['timestamp']
      if age > self._leak_check_threshold:
        leaked.append({
          'connection_id': conn_id,
          'thread_id': info['thread_id'],
          'age_seconds': age,
        })

    if leaked:
      self.logger.warning(f"检测到 {len(leaked)} 个潜在泄漏的连接:")
      for leak in leaked:
        self.logger.warning(
          f"  - 连接 #{leak['connection_id']}: "
          f"线程 {leak['thread_id']}, "
          f"已占用 {leak['age_seconds']:.1f}秒"
        )

    return leaked

  @contextmanager
  def connection_context(self, connection_params: Dict[str, Any]):
    """
    上下文管理器方式获取连接

    用法:
      with pool.connection_context(params) as (conn, cursor):
          cursor.execute(query, params)

    Args:
      connection_params: 连接参数
    """
    conn_cursor = self.get_connection(connection_params)
    if not conn_cursor:
      raise ConnectionException(
        message="无法获取数据库连接",
        connectionInfo=connection_params
      )

    try:
      yield conn_cursor
    finally:
      self.release_connection(conn_cursor[0])
