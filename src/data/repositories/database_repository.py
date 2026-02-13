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
from src.data.repositories.connection_pool import ConnectionPool
from src.infrastructure.interfaces import IQueryRepository
from src.infrastructure.exceptions import (
  QueryExecutionException,
  ConnectionException,
)

logger = logging.getLogger(__name__)

# 连接最大存活时间（秒）
CONNECTION_MAX_LIFETIME = 3600


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
      results = self.execute_query(query, params)
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

  # ============================================================================
  # IQueryRepository 接口方法（camelCase别名）
  # ============================================================================

  def executeQuery(
    self,
    sql: str,
    parameters: Optional[List[Any]] = None
  ) -> List[Dict[str, Any]]:
    """
    执行查询SQL（IQueryRepository接口方法）

    Args:
      sql: SQL查询语句
      parameters: 查询参数列表

    Returns:
      List[Dict[str, Any]]: 查询结果列表
    """
    return self.execute_query(sql, parameters)

  def executeNonQuery(
    self,
    sql: str,
    parameters: Optional[List[Any]] = None
  ) -> int:
    """
    执行非查询SQL（IQueryRepository接口方法）

    Args:
      sql: SQL语句
      parameters: 参数列表

    Returns:
      int: 受影响的行数（固定返回1表示成功）
    """
    success = self.execute_non_query(sql, parameters)
    return 1 if success else 0

  def executeScalar(
    self,
    sql: str,
    parameters: Optional[List[Any]] = None
  ) -> Any:
    """
    执行查询并返回单个值（IQueryRepository接口方法）

    Args:
      sql: SQL语句
      parameters: 参数列表

    Returns:
      Any: 查询结果的第一个值
    """
    return self.execute_scalar(sql, parameters)

  def test_connection(self) -> bool:
    """
    测试数据库连接（IQueryRepository接口方法）

    Returns:
      bool: 连接是否成功
    """
    try:
      connectionParams = self.get_connection_params()
      connCursor = self.connection_pool.get_connection(connectionParams)
      if connCursor:
        conn, _ = connCursor
        self.connection_pool.release_connection(conn)
        return True
      return False
    except Exception as e:
      self.logger.error(f"连接测试失败: {str(e)}")
      return False

  def get_connection_info(self) -> Dict[str, Any]:
    """
    获取连接信息（IQueryRepository接口方法）

    Returns:
      Dict[str, Any]: 连接信息字典
    """
    return self.get_connection_params()

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
