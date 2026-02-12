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


class ConnectionPool:
  """
  数据库连接池类

  支持连接健康检查、超时清理和自动释放
  """

  # 默认连接超时 (秒)
  DEFAULT_CONNECTION_TIMEOUT = 30
  # 默认查询超时 (秒)
  DEFAULT_QUERY_TIMEOUT = 30

  def __init__(
    self,
    max_connections: int = 10,
    timeout: int = 30,
    query_timeout: Optional[int] = None
  ):
    """
    初始化连接池

    Args:
      max_connections: 最大连接数
      timeout: 连接超时时间（秒）
      query_timeout: 查询超时时间（秒），默认与连接超时相同
    """
    self.max_connections = max_connections
    self.timeout = timeout
    self.query_timeout = query_timeout if query_timeout is not None else timeout
    self.connections = []
    self.lock = threading.RLock()
    self.logger = logging.getLogger(__name__)

    # 启动定期清理线程
    self._cleanup_thread = None
    self._start_cleanup_thread()

  def get_connection(
    self, connection_params: Dict[str, Any]
  ) -> Optional[Tuple[Any, Any]]:
    """
    获取数据库连接

    Args:
      connection_params: 连接参数

    Returns:
      Optional[Tuple[Any, Any]]: (connection, cursor) 元组
    """
    with self.lock:
      # 尝试从连接池获取可用连接
      for conn_info in self.connections:
        conn, cursor, params, last_used = conn_info
        # 检查连接是否匹配参数且未超时
        if params == connection_params and self._is_connection_valid(conn):
          # 更新最后使用时间
          conn_info[3] = datetime.now()
          self.logger.info("从连接池获取连接")
          return conn, cursor

      # 如果没有可用连接且未达到最大连接数，创建新连接
      if len(self.connections) < self.max_connections:
        self.logger.info("创建新的数据库连接")
        conn_cursor = self._create_connection(connection_params)
        if conn_cursor:
          conn, cursor = conn_cursor
          self.connections.append(
            [conn, cursor, connection_params, datetime.now()]
          )
          return conn, cursor

      self.logger.warning("连接池已满，无法获取连接")
      return None

  def release_connection(self, connection: Any):
    """
    释放连接回连接池（不健康则关闭）

    Args:
      connection: 数据库连接
    """
    with self.lock:
      for i, conn_info in enumerate(self.connections):
        conn, cursor, _, _ = conn_info
        if conn == connection:
          # 检查连接健康状态
          if not self._is_connection_healthy(conn):
            # 不健康则关闭并移除
            self.logger.warning(f"关闭不健康连接 #{i}")
            try:
              if cursor:
                try:
                  cursor.close()
                except:
                  pass
              if conn:
                try:
                  conn.close()
                except:
                  pass
            except Exception as e:
              self.logger.error(f"关闭不健康连接失败: {e}")

            del self.connections[i]
            return

          # 健康的连接标记为未使用并更新时间
          conn_info[3] = datetime.now()
          self.logger.debug(f"连接 #{i} 已释放回连接池")
          break

  def close_all_connections(self):
    """
    关闭所有连接
    """
    with self.lock:
      for conn_info in self.connections:
        conn, cursor, _, _ = conn_info
        try:
          if cursor:
            cursor.close()
          if conn:
            conn.close()
          self.logger.info("连接已关闭")
        except Exception as e:
          self.logger.error(f"关闭连接失败: {str(e)}")
      self.connections.clear()

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

    Returns:
      List[int]: 过期连接索引列表
    """
    expired = []
    current_time = datetime.now()

    for i, conn_info in enumerate(self.connections):
      _, _, _, last_used = conn_info
      # 未使用且超时的连接
      if (current_time - last_used).total_seconds() > self.timeout:
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

          # 关闭连接
          if cursor:
            try:
              cursor.close()
            except:
              pass
          if conn:
            try:
              conn.close()
            except:
              pass

          del self.connections[i]
          cleaned_count += 1
          self.logger.debug(f"清理过期连接 #{i}")
        except Exception as e:
          self.logger.error(f"清理连接失败 #{i}: {e}")

    if cleaned_count > 0:
      self.logger.info(f"清理了 {cleaned_count} 个过期连接")

    return cleaned_count


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

  def executeQuery(
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
          connectionInfo=self.getConnectionParams()
        )

      self.logger.debug(f"使用驱动: {driverType.value}")
      self.logger.debug(f"查询超时设置: {query_timeout}秒")

      self.logger.debug("获取数据库连接参数")
      connectionParams = self.getConnectionParams()
      self.logger.debug("从连接池获取数据库连接")
      connCursor = self.connectionPool.getConnection(connectionParams)

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
          self.logger.debug(f"执行参数化查询，参数: {params}")
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
              parameters=params
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
              parameters=params
            )

        if not results:
          self.logger.warning("查询执行成功，但未返回任何记录")
        self.logger.info(f"查询执行成功，返回{len(results)}条记录")
        self.logger.debug(f"查询结果: {results}")
        return results

      except QueryExecutionException:
        raise
      except Exception as e:
        self.logger.error(f"查询执行失败: {str(e)}")
        self.logger.debug(f"异常详情: {traceback.format_exc()}")
        raise QueryExecutionException(
          message=f"查询执行失败: {str(e)}",
          sql=query,
          parameters=params
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
        parameters=params
      )

  def executeNonQuery(self, query: str, params: Optional[List[Any]] = None) -> bool:
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
          connectionInfo=self.getConnectionParams()
        )

      self.logger.debug(f"使用驱动: {driverType.value}")

      self.logger.debug("获取数据库连接参数")
      connectionParams = self.getConnectionParams()
      self.logger.debug("从连接池获取数据库连接")
      connCursor = self.connectionPool.getConnection(connectionParams)

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
          self.logger.debug(f"执行参数化非查询语句，参数: {params}")
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
              parameters=params
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
          parameters=params
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
        parameters=params
      )

  def executeScalar(self, query: str, params: Optional[List[Any]] = None) -> Any:
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
        parameters=params
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
