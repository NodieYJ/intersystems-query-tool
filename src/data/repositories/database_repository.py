#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库仓库模块

用于管理数据库连接和执行数据库操作。
实现 IQueryRepository 接口。
"""

import logging
import threading
import time
import traceback
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from contextlib import contextmanager

from src.infrastructure.config.config_manager import get_config_manager
from src.infrastructure.config.constants import DatabaseDefaults, DatabaseTypes
from src.data.repositories.driver_factory import (
  DatabaseDriverFactory,
  DatabaseDriverType,
  get_driver_factory,
)
from src.infrastructure.interfaces import IQueryRepository
from src.infrastructure.exceptions import (
  QueryExecutionException,
  ConnectionException,
)

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


class DatabaseRepository(IQueryRepository):
  """
  数据库仓库类

  实现 IQueryRepository 接口。
  负责数据库连接管理和SQL执行。
  支持重试机制和连接池管理。
  """

  # 默认重试配置
  DEFAULT_MAX_RETRIES = 3
  DEFAULT_RETRY_DELAY = 1.0  # 秒

  def __init__(self):
    """
    初始化数据库仓库
    """
    self.config_manager = get_config_manager()
    self.connection_pool = ConnectionPool()
    self.logger = logging.getLogger(__name__)

    # 统计信息
    self._query_count = 0
    self._error_count = 0
    self._last_query_time = None

    # 查询取消支持
    self._cancel_events: Dict[str, threading.Event] = {}

    # 性能监控
    self._query_metrics = {
      'total_queries': 0,
      'slow_queries': 0,
      'total_duration': 0.0,
      'max_duration': 0.0,
      'min_duration': float('inf')
    }
    self._slow_query_threshold = 1.0  # 1秒以上的查询视为慢查询

  def get_statistics(self) -> Dict[str, Any]:
    """
    获取仓库统计信息

    Returns:
        Dict[str, Any]: 统计信息字典
    """
    return {
      "query_count": self._query_count,
      "error_count": self._error_count,
      "success_rate": (
        (self._query_count - self._error_count) / self._query_count * 100
        if self._query_count > 0 else 100
      ),
      "pool_size": len(self.connection_pool.connections),
      "last_query_time": self._last_query_time
    }

  def cancel_query(self, query_id: str) -> bool:
    """
    取消指定查询

    Args:
        query_id: 查询ID

    Returns:
        bool: 是否成功取消
    """
    if query_id in self._cancel_events:
      self._cancel_events[query_id].set()
      self.logger.info(f"查询 {query_id} 已取消")
      return True
    return False

  def get_query_metrics(self) -> Dict[str, Any]:
    """
    获取查询性能指标

    Returns:
        Dict[str, Any]: 性能指标字典
    """
    total = self._query_metrics['total_queries']
    avg_duration = self._query_metrics['total_duration'] / total if total > 0 else 0

    return {
      'total_queries': total,
      'slow_queries': self._query_metrics['slow_queries'],
      'slow_query_rate': self._query_metrics['slow_queries'] / total if total > 0 else 0,
      'total_duration': self._query_metrics['total_duration'],
      'avg_duration': avg_duration,
      'max_duration': self._query_metrics['max_duration'],
      'min_duration': self._query_metrics['min_duration'] if self._query_metrics['min_duration'] != float('inf') else 0
    }

  def _execute_with_retry(
    self,
    operation: Callable,
    max_retries: Optional[int] = None,
    timeout: Optional[float] = None
  ) -> Any:
    """
    执行带重试机制的操作

    Args:
        operation: 要执行的操作函数
        max_retries: 最大重试次数
        timeout: 超时时间（秒）

    Returns:
        Any: 操作结果
    """
    import time
    max_retries = max_retries or self.DEFAULT_MAX_RETRIES
    timeout = timeout or self.connection_pool.query_timeout
    start_time = time.time()

    last_exception = None

    for attempt in range(max_retries + 1):
      try:
        # 检查超时
        if time.time() - start_time > timeout:
          raise TimeoutError(f"操作超时（{timeout}秒）")

        result = operation()
        return result

      except TimeoutError:
        self._error_count += 1
        if attempt < max_retries:
          delay = self.DEFAULT_RETRY_DELAY * (2 ** attempt)
          self.logger.warning(f"查询超时，{delay:.1f}秒后重试...")
          time.sleep(delay)
        else:
          raise

      except Exception as e:
        last_exception = e
        self._error_count += 1

        if attempt < max_retries:
          delay = self.DEFAULT_RETRY_DELAY * (2 ** attempt)
          self.logger.warning(f"查询失败，{delay:.1f}秒后重试: {str(e)}")
          time.sleep(delay)

    self._error_count += 1
    if last_exception:
      raise last_exception
    raise RuntimeError("数据库操作失败，所有重试都已尝试")

  def get_connection_params(self) -> Dict[str, Any]:
    """
    获取连接参数

    Returns:
      Dict[str, Any]: 连接参数
    """
    try:
      self.logger.debug("开始获取数据库连接参数")
      # 获取配置
      server = self.config_manager.get("database.server", "localhost")
      port = self.config_manager.get("database.port", DatabaseDefaults.PORT_DEFAULT)
      namespace = self.config_manager.get("database.namespace", "USER")
      username = self.config_manager.get("database.username", "")
      password = self.config_manager.get("database.password", "")
      db_type = self.config_manager.get("database.db_type", DatabaseTypes.IRIS)

      connection_params = {
        "server": server,
        "port": port,
        "namespace": namespace,
        "username": username,
        "password": "******",  # 日志中隐藏密码
        "db_type": db_type,
      }

      self.logger.debug(f"获取连接参数完成: {connection_params}")

      return {
        "server": server,
        "port": port,
        "namespace": namespace,
        "username": username,
        "password": password,
        "db_type": db_type,
      }
    except Exception as e:
      self.logger.error(f"获取连接参数失败: {str(e)}")
      self.logger.debug(f"异常详情: {traceback.format_exc()}")
      return {
        "server": "localhost",
        "port": DatabaseDefaults.PORT_DEFAULT,
        "namespace": "USER",
        "username": "",
        "password": "",
        "db_type": DatabaseTypes.IRIS,
      }

  def execute_query(
    self,
    query: str,
    params: Optional[List[Any]] = None,
    timeout: Optional[float] = None
  ) -> List[Dict[str, Any]]:
    """
    执行SQL查询

    实现 IQueryRepository 接口。

    Args:
      query: SQL查询语句
      params: 查询参数
      timeout: 查询超时时间（秒），默认使用连接池配置

    Returns:
      List[Dict[str, Any]]: 查询结果列表

    Raises:
      QueryExecutionException: 查询执行失败
      QueryTimeoutException: 查询超时
    """
    # 使用默认值或传入的超时时间
    query_timeout = timeout if timeout is not None else self.connection_pool.query_timeout

    try:
      self.logger.debug("开始执行SQL查询操作")

      # 使用驱动工厂检测可用驱动
      factory = get_driver_factory()
      driverType = factory.detect_available_driver()

      if driverType == DatabaseDriverType.UNKNOWN:
        self.logger.error("没有可用的数据库驱动")
        raise ConnectionException(
          message="没有可用的数据库驱动",
          connectionInfo=self.get_connection_params()
        )

      self.logger.debug(f"使用驱动: {driverType.value}")
      self.logger.debug(f"查询超时设置: {query_timeout}秒")

      self.logger.debug("获取数据库连接参数")
      connectionParams = self.get_connection_params()
      self.logger.debug("从连接池获取数据库连接")
      connCursor = self.connection_pool.get_connection(connectionParams)

      if not connCursor:
        self.logger.error("无法获取数据库连接")
        raise ConnectionException(
          message="无法获取数据库连接",
          connectionInfo=connectionParams
        )

      conn, cursor = connCursor
      self.logger.debug(f"成功获取数据库连接: {conn}")

      # 判断是否为IRIS驱动
      isIrisDriver = hasattr(conn, "iris") or hasattr(conn, "isIRIS")

      try:
        # 执行查询
        self.logger.debug("准备执行SQL查询")
        if params:
          self.logger.debug(f"执行参数化查询，参数数量: {len(params)}")
          if isIrisDriver:
            self.logger.debug("使用IRIS驱动执行参数化查询")
            cursor.execute(query, *params)
          else:
            self.logger.debug("使用pyodbc执行参数化查询")
            cursor.execute(query, params)
        else:
          self.logger.debug("执行普通查询")
          cursor.execute(query)

        # 获取查询结果
        self.logger.debug("开始获取查询结果")
        if isIrisDriver:
          # IRIS驱动获取结果的方式
          self.logger.debug("使用IRIS驱动获取结果")
          try:
            resultSet = cursor
            results = []

            if hasattr(resultSet, "next"):
              self.logger.debug("使用IRIS驱动的next()方法获取结果")
              while resultSet.next():
                rowDict = {}
                for i in range(resultSet.getColumnCount()):
                  columnName = resultSet.getColumnName(i + 1)
                  columnValue = resultSet.getString(i + 1)
                  rowDict[columnName] = columnValue
                results.append(rowDict)
            else:
              self.logger.debug("尝试使用fetchall获取结果")
              rows = cursor.fetchall()
              if rows:
                if isinstance(rows[0], tuple) and len(rows) > 1:
                  columns = rows[0]
                  dataRows = rows[1:]
                  for row in dataRows:
                    results.append(dict(zip(columns, row)))
                else:
                  for row in rows:
                    if isinstance(row, tuple):
                      rowDict = {}
                      for i, value in enumerate(row):
                        rowDict[f"COLUMN_{i+1}"] = value
                      results.append(rowDict)
            self.logger.debug(f"IRIS驱动获取结果完成，共{len(results)}条记录")
          except Exception as e:
            self.logger.error(f"使用IRIS驱动获取结果失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            raise QueryExecutionException(
              message=f"获取查询结果失败: {str(e)}",
              sql=query,
              parameters=self._sanitize_params(params)
            )
        else:
          # pyodbc获取结果的方式
          self.logger.debug("使用pyodbc获取结果")
          try:
            columns = [column[0] for column in cursor.description]
            results = []

            for row in cursor.fetchall():
              results.append(dict(zip(columns, row)))
            self.logger.debug(f"pyodbc获取结果完成，共{len(results)}条记录")
          except Exception as e:
            self.logger.error(f"使用pyodbc获取结果失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            raise QueryExecutionException(
              message=f"获取查询结果失败: {str(e)}",
              sql=query,
              parameters=self._sanitize_params(params)
            )

        if not results:
          self.logger.warning("查询执行成功，但未返回任何记录")
        self.logger.info(f"查询执行成功，返回{len(results)}条记录")
        # 只输出前10条记录，避免日志过大
        preview = results[:10]
        self.logger.debug(f"查询结果预览: {preview}" + ("..." if len(results) > 10 else ""))
        return results

      except QueryExecutionException:
        raise
      except Exception as e:
        self.logger.error(f"查询执行失败: {str(e)}")
        self.logger.debug(f"异常详情: {traceback.format_exc()}")
        raise QueryExecutionException(
          message=f"查询执行失败: {str(e)}",
          sql=query,
          parameters=self._sanitize_params(params)
        )
      finally:
        # 释放连接回连接池
        self.logger.debug("释放连接回连接池")
        self.connection_pool.release_connection(conn)
        self.logger.debug("连接释放完成")

    except QueryExecutionException:
      raise
    except ConnectionException:
      raise
    except Exception as e:
      self.logger.error(f"SQL查询操作失败: {str(e)}")
      self.logger.debug(f"异常详情: {traceback.format_exc()}")
      raise QueryExecutionException(
        message=f"SQL查询操作失败: {str(e)}",
        sql=query,
        parameters=self._sanitize_params(params)
      )

  def execute_non_query(self, query: str, params: Optional[List[Any]] = None) -> bool:
    """
    执行非查询SQL语句

    实现 IQueryRepository 接口。

    Args:
      query: SQL语句
      params: 查询参数

    Returns:
      bool: 执行是否成功

    Raises:
      QueryExecutionException: 执行失败
    """
    try:
      self.logger.debug("开始执行非查询SQL操作")

      # 使用驱动工厂检测可用驱动
      factory = get_driver_factory()
      driverType = factory.detect_available_driver()

      if driverType == DatabaseDriverType.UNKNOWN:
        self.logger.error("没有可用的数据库驱动")
        raise ConnectionException(
          message="没有可用的数据库驱动",
          connectionInfo=self.get_connection_params()
        )

      self.logger.debug(f"使用驱动: {driverType.value}")

      self.logger.debug("获取数据库连接参数")
      connectionParams = self.get_connection_params()
      self.logger.debug("从连接池获取数据库连接")
      connCursor = self.connection_pool.get_connection(connectionParams)

      if not connCursor:
        self.logger.error("无法获取数据库连接")
        raise ConnectionException(
          message="无法获取数据库连接",
          connectionInfo=connectionParams
        )

      conn, cursor = connCursor
      self.logger.debug(f"成功获取数据库连接: {conn}")

      # 判断是否为IRIS驱动
      isIrisDriver = hasattr(conn, "iris") or hasattr(conn, "isIRIS")

      try:
        # 执行非查询语句
        self.logger.debug("准备执行非查询SQL语句")
        if params:
          self.logger.debug(f"执行参数化非查询语句，参数数量: {len(params)}")
          if isIrisDriver:
            self.logger.debug("使用IRIS驱动执行参数化非查询语句")
            cursor.execute(query, *params)
          else:
            self.logger.debug("使用pyodbc执行参数化非查询语句")
            cursor.execute(query, params)
        else:
          self.logger.debug("执行普通非查询语句")
          cursor.execute(query)

        # 提交事务
        self.logger.debug("开始提交事务")
        if isIrisDriver:
          self.logger.debug("使用IRIS驱动提交事务")
          try:
            if hasattr(conn, "commit"):
              conn.commit()
              self.logger.debug("IRIS驱动执行commit()")
            self.logger.info("IRIS驱动事务提交成功")
          except Exception as e:
            self.logger.warning(f"IRIS驱动事务提交失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            self.logger.debug("IRIS驱动可能不需要显式提交")
        else:
          # pyodbc的事务提交
          self.logger.debug("使用pyodbc提交事务")
          try:
            conn.commit()
            self.logger.debug("pyodbc执行commit()")
            self.logger.info("pyodbc事务提交成功")
          except Exception as e:
            self.logger.error(f"pyodbc事务提交失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            self.logger.debug("执行事务回滚")
            conn.rollback()
            self.logger.debug("事务回滚完成")
            raise QueryExecutionException(
              message=f"事务提交失败: {str(e)}",
              sql=query,
              parameters=self._sanitize_params(params)
            )

        self.logger.info("非查询语句执行成功")
        self.logger.debug("非查询操作完成")
        return True

      except QueryExecutionException:
        raise
      except Exception as e:
        self.logger.error(f"非查询语句执行失败: {str(e)}")
        self.logger.debug(f"异常详情: {traceback.format_exc()}")
        # 回滚事务
        if not isIrisDriver and hasattr(conn, "rollback"):
          try:
            self.logger.debug("执行事务回滚")
            conn.rollback()
            self.logger.debug("事务回滚完成")
          except Exception as rollbackE:
            self.logger.warning(f"事务回滚失败: {str(rollbackE)}")
            self.logger.debug(f"回滚异常详情: {traceback.format_exc()}")
        raise QueryExecutionException(
          message=f"非查询语句执行失败: {str(e)}",
          sql=query,
          parameters=self._sanitize_params(params)
        )
      finally:
        # 释放连接回连接池
        self.logger.debug("释放连接回连接池")
        self.connection_pool.release_connection(conn)
        self.logger.debug("连接释放完成")

    except (QueryExecutionException, ConnectionException):
      raise
    except Exception as e:
      self.logger.error(f"非查询SQL操作失败: {str(e)}")
      self.logger.debug(f"异常详情: {traceback.format_exc()}")
      raise QueryExecutionException(
        message=f"非查询SQL操作失败: {str(e)}",
        sql=query,
        parameters=self._sanitize_params(params)
      )

  def execute_scalar(self, query: str, params: Optional[List[Any]] = None) -> Any:
    """
    执行标量查询（返回单个值）

    实现 IQueryRepository 接口。

    Args:
      query: SQL查询语句
      params: 查询参数

    Returns:
      Any: 查询结果（单个值）

    Raises:
      QueryExecutionException: 查询执行失败
    """
    try:
      results = self.executeQuery(query, params)
      if results and len(results) > 0:
        firstRow = results[0]
        if firstRow:
          # 返回第一个值
          return list(firstRow.values())[0]
      return None
    except QueryExecutionException:
      raise
    except Exception as e:
      self.logger.error(f"标量查询失败: {str(e)}")
      raise QueryExecutionException(
        message=f"标量查询失败: {str(e)}",
        sql=query,
        parameters=self._sanitize_params(params)
      )

  def close(self):
    """
    关闭所有连接
    """
    self.connection_pool.close_all_connections()


# 创建全局数据库仓库实例
db_repository = DatabaseRepository()


def get_db_repository() -> DatabaseRepository:
  """
  获取数据库仓库实例

  Returns:
    DatabaseRepository: 数据库仓库实例
  """
  return db_repository
