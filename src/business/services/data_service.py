#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据服务模块
用于处理数据相关的业务逻辑
提供安全的数据访问功能
"""

import logging
import re
import time
import traceback
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass

from src.data.repositories.database_repository import get_db_repository
from src.infrastructure.config.config_manager import get_config_manager

logger = logging.getLogger(__name__)

# 允许的 schema 名称模式 (白名单)
ALLOWED_SCHEMA_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


@dataclass
class ValidationResult:
  """
  验证结果

  Attributes:
      is_valid: 是否有效
      message: 验证消息
      sanitized_value: 净化后的值
  """
  is_valid: bool
  message: str
  sanitized_value: str = ""


class InputValidator:
  """
  输入验证器

  提供通用的输入验证和净化功能
  """

  @staticmethod
  def validate_schema_name(schema: Optional[str]) -> ValidationResult:
    """
    验证 schema 名称

    Args:
        schema: schema 名称

    Returns:
        ValidationResult: 验证结果
    """
    # None 检查
    if schema is None:
      return ValidationResult(
        is_valid=True,
        message="Using default schema",
        sanitized_value="public"
      )

    # 空字符串检查
    if not schema:
      return ValidationResult(
        is_valid=True,
        message="Empty schema, using default",
        sanitized_value="public"
      )

    # 长度检查
    if len(schema) > 63:
      return ValidationResult(
        is_valid=False,
        message="Schema name too long (max 63 characters)",
        sanitized_value=""
      )

    # 模式检查
    if not ALLOWED_SCHEMA_PATTERN.match(schema):
      return ValidationResult(
        is_valid=False,
        message="Invalid schema name format",
        sanitized_value=""
      )

    # SQL 注入风险字符检查
    dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "\\"]
    if any(char in schema for char in dangerous_chars):
      return ValidationResult(
        is_valid=False,
        message="Schema name contains dangerous characters",
        sanitized_value=""
      )

    return ValidationResult(
      is_valid=True,
      message="Valid schema name",
      sanitized_value=schema.lower()
    )

  @staticmethod
  def sanitize_identifier(identifier: str) -> str:
    """
    净化标识符 (表名、列名等)

    Args:
        identifier: 标识符

    Returns:
        str: 净化后的标识符
    """
    # 只允许字母、数字、下划线
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', identifier)
    return sanitized.lower()

  @staticmethod
  def validate_sql_query_params(params: tuple) -> bool:
    """
    验证 SQL 查询参数

    Args:
        params: 查询参数

    Returns:
        bool: 是否有效
    """
    if not params:
      return True

    # 检查参数类型
    allowed_types = (str, int, float, bool, type(None))

    for param in params:
      if not isinstance(param, allowed_types):
        logger.warning(f"Invalid parameter type: {type(param)}")
        return False

    # 检查危险内容
    dangerous_patterns = [
      r"'.*--",
      r"'.*/\*",
      r"'.*\*/",
      r"'\s+OR\s+'",
      r"';\s*DROP",
      r"';\s*DELETE",
      r"';\s*UPDATE",
    ]

    for param in params:
      if isinstance(param, str):
        for pattern in dangerous_patterns:
          if re.search(pattern, param, re.IGNORECASE):
            logger.warning(f"Dangerous pattern detected in parameter: {pattern}")
            return False

    return True

  @staticmethod
  def validate_query(
    query: str,
    params: Optional[tuple] = None,
    require_params: bool = True
  ) -> ValidationResult:
    """
    验证查询安全性（增强版）

    强制要求使用参数化查询，防止 SQL 注入。

    Args:
        query: SQL 查询语句
        params: 查询参数
        require_params: 是否强制要求参数化查询

    Returns:
        ValidationResult: 验证结果
    """
    if not query:
      return ValidationResult(
        is_valid=False,
        message="Query cannot be empty",
        sanitized_value=""
      )

    # 1. 强制参数化检查
    if require_params and params is None:
      return ValidationResult(
        is_valid=False,
        message="Dynamic queries must use parameterized queries",
        sanitized_value=""
      )

    query_upper = query.upper().strip()

    # 2. 检查危险的关键字
    dangerous_keywords = [
      ("DROP", "DROP"),
      ("DELETE FROM", "DELETE"),
      ("TRUNCATE", "TRUNCATE"),
      ("ALTER", "ALTER"),
      ("CREATE", "CREATE"),
      ("INSERT INTO", "INSERT"),
      ("UPDATE", "UPDATE"),
      ("EXEC", "EXEC"),
      ("EXECUTE", "EXECUTE"),
      ("xp_", "xp_"),
      ("sp_", "sp_"),
    ]

    for keyword, description in dangerous_keywords:
      if keyword in query_upper:
        return ValidationResult(
          is_valid=False,
          message=f"Query contains dangerous keyword: {description}",
          sanitized_value=""
        )

    # 3. 检查注释注入
    if "--" in query or "/*" in query:
      logger.warning("Query contains SQL comments")

    # 4. 验证参数安全性
    if params is not None:
      if not InputValidator.validate_sql_query_params(params):
        return ValidationResult(
          is_valid=False,
          message="Parameters contain dangerous content",
          sanitized_value=""
        )

    return ValidationResult(
      is_valid=True,
      message="Query passed safety check",
      sanitized_value=query
    )

  @staticmethod
  def validate_query_not_dangerous(query: str) -> ValidationResult:
    """
    验证查询是否包含危险操作（兼容旧接口）

    Args:
        query: SQL 查询语句

    Returns:
        ValidationResult: 验证结果
    """
    # 旧方法只做向后兼容，不强制参数化
    if not query:
      return ValidationResult(
        is_valid=False,
        message="Query cannot be empty",
        sanitized_value=""
      )

    query_upper = query.upper().strip()

    # 检查危险的关键字
    dangerous_keywords = [
      ("DROP", "DROP"),
      ("DELETE FROM", "DELETE"),
      ("TRUNCATE", "TRUNCATE"),
      ("ALTER", "ALTER"),
      ("CREATE", "CREATE"),
      ("INSERT INTO", "INSERT"),
      ("UPDATE", "UPDATE"),
      ("EXEC", "EXEC"),
      ("EXECUTE", "EXECUTE"),
      ("xp_", "xp_"),
      ("sp_", "sp_"),
    ]

    for keyword, description in dangerous_keywords:
      if keyword in query_upper:
        return ValidationResult(
          is_valid=False,
          message=f"Query contains dangerous keyword: {description}",
          sanitized_value=""
        )

    # 检查注释注入
    if "--" in query or "/*" in query:
      logger.warning("Query contains SQL comments")

    return ValidationResult(
      is_valid=True,
      message="Query passed safety check",
      sanitized_value=query
    )


class DataService:
  """
  数据服务类

  提供安全的数据访问功能，支持重试机制和超时控制
  """

  # 默认重试配置
  DEFAULT_MAX_RETRIES = 3
  DEFAULT_RETRY_DELAY = 1.0  # 秒
  DEFAULT_TIMEOUT = 30  # 秒

  def __init__(self):
    """
    初始化数据服务
    """
    self.db_repository = get_db_repository()
    self.config_manager = get_config_manager()
    self._connection_status = "disconnected"
    self._last_error = None
    self._retry_count = 0

  def get_connection_status(self) -> Dict[str, Any]:
    """
    获取连接状态信息

    Returns:
        Dict[str, Any]: 包含连接状态信息的字典
    """
    return {
        "status": self._connection_status,
        "last_error": self._last_error,
        "retry_count": self._retry_count
    }

  def _execute_with_retry(
    self,
    operation: callable,
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

    Raises:
        Exception: 所有重试失败后抛出异常
    """
    max_retries = max_retries or self.DEFAULT_MAX_RETRIES
    timeout = timeout or self.DEFAULT_TIMEOUT
    last_exception = None

    import time
    start_time = time.time()

    for attempt in range(max_retries + 1):
      try:
        # 检查超时
        if time.time() - start_time > timeout:
          raise TimeoutError(f"操作超时（{timeout}秒）")

        # 执行操作
        result = operation()

        # 成功，重置重试计数
        self._retry_count = 0
        self._last_error = None
        self._connection_status = "connected"

        return result

      except TimeoutError:
        self._last_error = f"第 {attempt + 1}/{max_retries + 1} 次尝试: 操作超时"
        self._connection_status = "timeout"

        if attempt < max_retries:
          delay = self.DEFAULT_RETRY_DELAY * (2 ** attempt)  # 指数退避
          logger.warning(f"操作超时，{delay:.1f}秒后重试...")
          time.sleep(delay)
        else:
          raise

      except Exception as e:
        last_exception = e
        self._last_error = f"第 {attempt + 1}/{max_retries + 1} 次尝试: {str(e)}"
        self._connection_status = "error"

        if attempt < max_retries:
          delay = self.DEFAULT_RETRY_DELAY * (2 ** attempt)  # 指数退避
          logger.warning(f"操作失败，{delay:.1f}秒后重试...")
          time.sleep(delay)

    # 所有重试都失败
    self._retry_count = max_retries + 1
    if last_exception:
      raise last_exception
    raise RuntimeError("操作失败，所有重试都已尝试")

  def get_data(
    self, query: str, params: Optional[List[Any]] = None
  ) -> Optional[List[Dict[str, Any]]]:
    """
    获取数据

    Args:
        query: SQL查询语句
        params: 查询参数（强制要求，用于防止SQL注入）

    Returns:
        Optional[List[Dict[str, Any]]]: 查询结果

    Raises:
        ValueError: 查询包含危险操作或未使用参数化查询
        TypeError: 参数类型错误
    """
    try:
      logger.debug("开始执行数据获取操作")

      # 验证查询安全性（强制参数化）
      query_validation = InputValidator.validate_query(query, tuple(params) if params else None)
      if not query_validation.is_valid:
        logger.error(f"查询验证失败: {query_validation.message}")
        raise ValueError(f"查询验证失败: {query_validation.message}")

      # 验证参数类型
      if params is not None:
        if not isinstance(params, (list, tuple)):
          raise TypeError("参数必须为列表或元组")

      logger.info(f"执行查询: {query}")
      if params:
        logger.debug(f"查询参数: [已脱敏，共{len(params)}个参数]")

      logger.debug("调用数据库仓库执行查询")
      result = self.db_repository.execute_query(query, params)
      logger.debug(f"数据获取操作完成，返回{len(result) if result else 0}条记录")
      return result

    except (ValueError, TypeError):
      raise
    except Exception as e:
      logger.error(f"获取数据失败: {str(e)}")
      logger.debug(f"异常详情: {traceback.format_exc()}")
      return None

  def save_data(self, query: str, params: Optional[List[Any]] = None) -> bool:
    """
    保存数据

    Args:
        query: SQL语句
        params: 查询参数（强制要求，用于防止SQL注入）

    Returns:
        bool: 执行是否成功

    Raises:
        ValueError: 查询包含危险操作或未使用参数化查询
        TypeError: 参数类型错误
    """
    try:
      logger.debug("开始执行数据保存操作")

      # 验证查询安全性（强制参数化）
      query_validation = InputValidator.validate_query(query, tuple(params) if params else None)
      if not query_validation.is_valid:
        logger.error(f"保存操作验证失败: {query_validation.message}")
        raise ValueError(f"保存操作验证失败: {query_validation.message}")

      # 验证参数类型
      if params is not None:
        if not isinstance(params, (list, tuple)):
          raise TypeError("参数必须为列表或元组")

      logger.info(f"执行保存操作: {query}")
      if params:
        logger.debug(f"保存参数: [已脱敏，共{len(params)}个参数]")

      logger.debug("调用数据库仓库执行非查询操作")
      result = self.db_repository.execute_non_query(query, params)
      logger.debug(f"数据保存操作完成，执行结果: {result}")
      return result

    except (ValueError, TypeError):
      raise
    except Exception as e:
      logger.error(f"保存数据失败: {str(e)}")
      logger.debug(f"异常详情: {traceback.format_exc()}")
      return False

  def test_connection(self) -> bool:
    """
    测试数据库连接

    Returns:
        bool: 连接是否正常
    """
    try:
      logger.debug("开始执行数据库连接测试")
      logger.info("执行数据库连接测试")
      # 执行简单查询测试连接
      logger.debug("执行测试查询: SELECT 1")
      # 测试查询使用特殊处理，不需要参数化
      result = self.db_repository.execute_query("SELECT 1", timeout=5)
      logger.debug(f"测试查询结果: {result}")
      if result and len(result) > 0:
        logger.info("数据库连接测试成功")
        logger.debug("连接测试完成，状态: 成功")
        return True
      else:
        logger.error("数据库连接测试失败: 查询未返回结果")
        logger.debug("连接测试完成，状态: 失败")
        return False
    except Exception as e:
      logger.error(f"连接测试失败: {str(e)}")
      logger.debug(f"异常详情: {traceback.format_exc()}")
      return False

  def get_table_names(self, schema: Optional[str] = None) -> List[str]:
    """
    获取数据库表名列表

    Args:
        schema: 数据库 schema 名称

    Returns:
        List[str]: 表名列表

    Raises:
        ValueError: schema 名称无效
    """
    # 验证 schema
    validation = InputValidator.validate_schema_name(schema)

    if not validation.is_valid:
      raise ValueError(f"Invalid schema: {validation.message}")

    schema_param = validation.sanitized_value

    try:
      query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
        ORDER BY table_name
      """
      # 使用参数化查询
      result = self.db_repository.execute_query(query, [schema_param])
      return [row.get("table_name", "") for row in result] if result else []

    except Exception as e:
      logger.error(f"获取表名列表失败: {str(e)}")
      raise


# 创建全局数据服务实例
data_service = DataService()


def get_data_service() -> DataService:
    """
    获取数据服务实例

    Returns:
        DataService: 数据服务实例
    """
    return data_service
