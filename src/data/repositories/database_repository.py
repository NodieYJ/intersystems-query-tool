#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库仓库模块
用于管理数据库连接和执行数据库操作
"""

import logging
import threading
import time
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from src.infrastructure.config.config_manager import get_config_manager
from src.infrastructure.config.constants import DatabaseDefaults, DatabaseTypes
from src.data.repositories.driver_factory import (
    DatabaseDriverFactory,
    DatabaseDriverType,
    get_driver_factory,
)

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    数据库连接池类

    支持连接健康检查、超时清理和自动释放
    """

    def __init__(self, max_connections: int = 10, timeout: int = 30):
        """
        初始化连接池

        Args:
            max_connections: 最大连接数
            timeout: 连接超时时间（秒）
        """
        self.max_connections = max_connections
        self.timeout = timeout
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


class DatabaseRepository:
    """
    数据库仓库类
    """

    def __init__(self):
        """
        初始化数据库仓库
        """
        self.config_manager = get_config_manager()
        self.connection_pool = ConnectionPool()
        self.logger = logging.getLogger(__name__)

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
            
            # 处理加密的密码
            # 注意：这里我们直接返回密码，因为数据库连接需要原始密码
            # 密码在配置文件中是加密存储的，但在内存中我们保持原始密码
            
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
        self, query: str, params: Optional[List[Any]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        执行SQL查询

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            Optional[List[Dict[str, Any]]]: 查询结果
        """
        try:
            self.logger.debug("开始执行SQL查询操作")

            # 使用驱动工厂检测可用驱动
            factory = get_driver_factory()
            driver_type = factory.detect_available_driver()

            if driver_type == DatabaseDriverType.UNKNOWN:
                self.logger.error("没有可用的数据库驱动")
                self.logger.debug("查询操作终止，无可用驱动")
                return None

            self.logger.debug(f"使用驱动: {driver_type.value}")

            self.logger.debug("获取数据库连接参数")
            connection_params = self.get_connection_params()
            self.logger.debug("从连接池获取数据库连接")
            conn_cursor = self.connection_pool.get_connection(connection_params)

            if not conn_cursor:
                self.logger.error("无法获取数据库连接")
                self.logger.debug("查询操作终止，无法获取连接")
                return None

            conn, cursor = conn_cursor
            self.logger.debug(f"成功获取数据库连接: {conn}")

            # 判断是否为IRIS驱动
            is_iris_driver = hasattr(conn, "iris") or hasattr(conn, "isIRIS")

            try:
                # 执行查询
                self.logger.debug("准备执行SQL查询")
                if params:
                    self.logger.debug(f"执行参数化查询，参数: {params}")
                    if is_iris_driver:
                        # IRIS驱动的参数化查询
                        self.logger.debug("使用IRIS驱动执行参数化查询")
                        cursor.execute(query, *params)
                    else:
                        # pyodbc的参数化查询
                        self.logger.debug("使用pyodbc执行参数化查询")
                        cursor.execute(query, params)
                else:
                    self.logger.debug("执行普通查询")
                    cursor.execute(query)

                # 获取查询结果
                self.logger.debug("开始获取查询结果")
                if is_iris_driver:
                    # IRIS驱动获取结果的方式
                    self.logger.debug("使用IRIS驱动获取结果")
                    try:
                        # 尝试获取结果集
                        result_set = cursor
                        results = []

                        # 检查是否有结果
                        if hasattr(result_set, "next"):
                            # 使用IRIS驱动的结果获取方式
                            self.logger.debug("使用IRIS驱动的next()方法获取结果")
                            while result_set.next():
                                # 获取列名和值
                                row_dict = {}
                                for i in range(result_set.getColumnCount()):
                                    column_name = result_set.getColumnName(i + 1)
                                    column_value = result_set.getString(i + 1)
                                    row_dict[column_name] = column_value
                                results.append(row_dict)
                        else:
                            # 尝试使用fetchall
                            self.logger.debug("尝试使用fetchall获取结果")
                            rows = cursor.fetchall()
                            if rows:
                                # 假设第一行是列名
                                if isinstance(rows[0], tuple) and len(rows) > 1:
                                    # 第一行是列名，其余是数据
                                    columns = rows[0]
                                    data_rows = rows[1:]
                                    for row in data_rows:
                                        results.append(dict(zip(columns, row)))
                                else:
                                    # 直接处理数据
                                    for row in rows:
                                        if isinstance(row, tuple):
                                            # 为每行创建默认列名
                                            row_dict = {}
                                            for i, value in enumerate(row):
                                                row_dict[f"COLUMN_{i+1}"] = value
                                            results.append(row_dict)
                        self.logger.debug(f"IRIS驱动获取结果完成，共{len(results)}条记录")
                    except Exception as e:
                        self.logger.error(f"使用IRIS驱动获取结果失败: {str(e)}")
                        self.logger.debug(f"异常详情: {traceback.format_exc()}")
                        return None
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
                        return None

                if not results:
                    self.logger.warning("查询执行成功，但未返回任何记录")
                self.logger.info(f"查询执行成功，返回{len(results)}条记录")
                self.logger.debug(f"查询结果: {results}")
                return results

            except Exception as e:
                self.logger.error(f"查询执行失败: {str(e)}")
                self.logger.debug(f"异常详情: {traceback.format_exc()}")
                return None
            finally:
                # 释放连接回连接池
                self.logger.debug("释放连接回连接池")
                self.connection_pool.release_connection(conn)
                self.logger.debug("连接释放完成")
        except Exception as e:
            self.logger.error(f"SQL查询操作失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            return None

    def execute_non_query(self, query: str, params: Optional[List[Any]] = None) -> bool:
        """
        执行非查询SQL语句

        Args:
            query: SQL语句
            params: 查询参数

        Returns:
            bool: 执行是否成功
        """
        try:
            self.logger.debug("开始执行非查询SQL操作")

            # 使用驱动工厂检测可用驱动
            factory = get_driver_factory()
            driver_type = factory.detect_available_driver()

            if driver_type == DatabaseDriverType.UNKNOWN:
                self.logger.error("没有可用的数据库驱动")
                self.logger.debug("非查询操作终止，无可用驱动")
                return False

            self.logger.debug(f"使用驱动: {driver_type.value}")

            self.logger.debug("获取数据库连接参数")
            connection_params = self.get_connection_params()
            self.logger.debug("从连接池获取数据库连接")
            conn_cursor = self.connection_pool.get_connection(connection_params)

            if not conn_cursor:
                self.logger.error("无法获取数据库连接")
                self.logger.debug("非查询操作终止，无法获取连接")
                return False

            conn, cursor = conn_cursor
            self.logger.debug(f"成功获取数据库连接: {conn}")

            # 判断是否为IRIS驱动
            is_iris_driver = hasattr(conn, "iris") or hasattr(conn, "isIRIS")

            try:
                # 执行非查询语句
                self.logger.debug("准备执行非查询SQL语句")
                if params:
                    self.logger.debug(f"执行参数化非查询语句，参数: {params}")
                    if is_iris_driver:
                        # IRIS驱动的参数化执行
                        self.logger.debug("使用IRIS驱动执行参数化非查询语句")
                        cursor.execute(query, *params)
                    else:
                        # pyodbc的参数化执行
                        self.logger.debug("使用pyodbc执行参数化非查询语句")
                        cursor.execute(query, params)
                else:
                    self.logger.debug("执行普通非查询语句")
                    cursor.execute(query)

                # 提交事务
                self.logger.debug("开始提交事务")
                if is_iris_driver:
                    # IRIS驱动的事务提交
                    self.logger.debug("使用IRIS驱动提交事务")
                    try:
                        if hasattr(conn, "commit"):
                            conn.commit()
                            self.logger.debug("IRIS驱动执行commit()")
                        self.logger.info("IRIS驱动事务提交成功")
                    except Exception as e:
                        self.logger.warning(f"IRIS驱动事务提交失败: {str(e)}")
                        self.logger.debug(f"异常详情: {traceback.format_exc()}")
                        # IRIS驱动可能不需要显式提交
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
                        return False

                self.logger.info("非查询语句执行成功")
                self.logger.debug("非查询操作完成")
                return True

            except Exception as e:
                self.logger.error(f"非查询语句执行失败: {str(e)}")
                self.logger.debug(f"异常详情: {traceback.format_exc()}")
                # 回滚事务
                if not is_iris_driver and hasattr(conn, "rollback"):
                    try:
                        self.logger.debug("执行事务回滚")
                        conn.rollback()
                        self.logger.debug("事务回滚完成")
                    except Exception as rollback_e:
                        self.logger.warning(f"事务回滚失败: {str(rollback_e)}")
                        self.logger.debug(f"回滚异常详情: {traceback.format_exc()}")
                return False
            finally:
                # 释放连接回连接池
                self.logger.debug("释放连接回连接池")
                self.connection_pool.release_connection(conn)
                self.logger.debug("连接释放完成")
        except Exception as e:
            self.logger.error(f"非查询SQL操作失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            return False

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
