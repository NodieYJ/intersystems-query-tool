#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
异常处理模块

提供统一的异常类定义和异常处理工具。
支持错误码体系、异常链、日志记录和用户友好提示。
"""

from abc import ABC
from typing import Any, Dict, Optional
import traceback
import logging


logger = logging.getLogger(__name__)


class AppException(Exception):
  """
  应用基础异常类

  所有自定义异常的基类。
  提供统一的异常信息格式和错误追踪能力。
  """

  def __init__(
    self,
    message: str,
    errorCode: str = "APP_000",
    details: Dict[str, Any] = None,
    cause: Exception = None
  ):
    """
    初始化应用异常

    Args:
      message: 异常消息（人类可读）
      errorCode: 错误码（格式：模块_序号，如 DB_001）
      details: 额外详细信息字典
      cause: 原始异常（用于异常链）
    """
    super().__init__(message)
    self.message = message
    self.errorCode = errorCode
    self.details = details or {}
    self.cause = cause
    self.timestamp = self._getTimestamp()
    self.tracebackStr = self._getTraceback()

  def _getTimestamp(self) -> str:
    """获取异常发生时间"""
    from datetime import datetime
    return datetime.now().isoformat()

  def _getTraceback(self) -> str:
    """获取堆栈跟踪"""
    return traceback.format_exc()

  def toDict(self) -> Dict[str, Any]:
    """转换为字典格式"""
    return {
      "errorCode": self.errorCode,
      "message": self.message,
      "timestamp": self.timestamp,
      "details": self.details,
      "traceback": self.tracebackStr
    }

  def __str__(self) -> str:
    """字符串表示"""
    return f"[{self.errorCode}] {self.message}"

  def log(self, loggerInstance=None):
    """记录异常日志"""
    logInstance = loggerInstance or logger
    logInstance.error(
      f"异常发生: {self.__str__()}",
      extra={
        "errorCode": self.errorCode,
        "details": self.details,
        "traceback": self.tracebackStr
      },
      exc_info=True
    )


# ==================== 数据库异常 ====================


class DatabaseException(AppException):
  """
  数据库操作异常基类

  所有数据库相关异常的父类。
  """

  def __init__(
    self,
    message: str,
    errorCode: str = "DB_000",
    sql: str = None,
    **kwargs
  ):
    """
    初始化数据库异常

    Args:
      message: 异常消息
      errorCode: 错误码
      sql: 相关的SQL语句
      **kwargs: 其他参数
    """
    details = kwargs.get('details', {})
    if sql:
      details['sql'] = sql
    super().__init__(message, errorCode, details, kwargs.get('cause'))


class ConnectionException(DatabaseException):
  """数据库连接异常"""

  def __init__(
    self,
    message: str = "数据库连接失败",
    connectionInfo: Dict = None,
    errorCode: str = "DB_001",
    **kwargs
  ):
    details = {'connectionInfo': connectionInfo}
    super().__init__(
      message,
      errorCode=errorCode,
      details=details,
      **kwargs
    )


class QueryExecutionException(DatabaseException):
  """查询执行异常"""

  def __init__(
    self,
    message: str = "查询执行失败",
    sql: str = None,
    parameters: list = None,
    executionTime: float = None,
    errorCode: str = "DB_002",
    **kwargs
  ):
    details = {}
    if sql:
      details['sql'] = sql
    if parameters:
      details['parameters'] = parameters
    if executionTime:
      details['executionTime'] = executionTime

    super().__init__(
      message,
      errorCode=errorCode,
      details=details,
      **kwargs
    )


class TransactionException(DatabaseException):
  """事务执行异常"""

  def __init__(
    self,
    message: str = "事务执行失败",
    transactionId: str = None,
    errorCode: str = "DB_003",
    **kwargs
  ):
    details = {'transactionId': transactionId}
    super().__init__(
      message,
      errorCode=errorCode,
      details=details,
      **kwargs
    )


# ==================== 业务异常 ====================


class BusinessException(AppException):
  """
  业务逻辑异常基类

  所有业务规则相关异常的父类。
  """

  def __init__(
    self,
    message: str,
    errorCode: str = "BZ_000",
    entity: str = None,
    field: str = None,
    **kwargs
  ):
    details = kwargs.get('details', {})
    if entity:
      details['entity'] = entity
    if field:
      details['field'] = field
    super().__init__(message, errorCode, details, kwargs.get('cause'))


class ValidationException(BusinessException):
  """数据验证异常"""

  def __init__(
    self,
    message: str = "数据验证失败",
    field: str = None,
    value: Any = None,
    rule: str = None,
    errorCode: str = "BZ_001",
    **kwargs
  ):
    details = {'field': field, 'value': value, 'rule': rule}
    super().__init__(
      message,
      errorCode=errorCode,
      details=details,
      **kwargs
    )


class NotFoundException(BusinessException):
  """资源不存在异常"""

  def __init__(
    self,
    message: str = "请求的资源不存在",
    resourceType: str = None,
    resourceId: Any = None,
    errorCode: str = "BZ_002",
    **kwargs
  ):
    details = {'resourceType': resourceType, 'resourceId': resourceId}
    super().__init__(
      message,
      errorCode=errorCode,
      details=details,
      **kwargs
    )


class DuplicateException(BusinessException):
  """重复操作异常"""

  def __init__(
    self,
    message: str = "资源已存在",
    resourceType: str = None,
    duplicateField: str = None,
    errorCode: str = "BZ_003",
    **kwargs
  ):
    details = {'resourceType': resourceType, 'duplicateField': duplicateField}
    super().__init__(
      message,
      errorCode=errorCode,
      details=details,
      **kwargs
    )


# ==================== 配置异常 ====================


class ConfigurationException(AppException):
  """配置异常"""

  def __init__(
    self,
    message: str = "配置错误",
    configKey: str = None,
    expectedValue: Any = None,
    actualValue: Any = None,
    errorCode: str = "CFG_001",
    **kwargs
  ):
    details = {'configKey': configKey}
    if expectedValue:
      details['expectedValue'] = expectedValue
    if actualValue:
      details['actualValue'] = actualValue
    super().__init__(
      message,
      errorCode=errorCode,
      details=details,
      **kwargs
    )


# ==================== 数据异常 ====================


class DataException(AppException):
  """数据处理异常"""

  def __init__(
    self,
    message: str = "数据处理错误",
    dataOperation: str = None,
    dataSource: str = None,
    errorCode: str = "DATA_001",
    details: Dict[str, Any] = None,
    **kwargs
  ):
    # 清理kwargs中的冲突参数（来自子类的参数）
    kwargs.pop('errorCode', None)
    kwargs.pop('dataOperation', None)
    kwargs.pop('dataSource', None)
    kwargs.pop('format', None)
    kwargs.pop('lineNumber', None)
    kwargs.pop('sourceType', None)
    kwargs.pop('targetType', None)
    kwargs.pop('value', None)
    
    # 合并details
    mergedDetails = {'dataOperation': dataOperation, 'dataSource': dataSource}
    if details:
      mergedDetails.update(details)
    
    super().__init__(
      message,
      errorCode=errorCode,
      details=mergedDetails,
      **kwargs
    )


class DataParsingException(DataException):
  """数据解析异常"""

  def __init__(
    self,
    message: str = "数据解析失败",
    format: str = None,
    lineNumber: int = None,
    errorCode: str = "DATA_002",
    **kwargs
  ):
    # 清理kwargs中的参数，避免传递给父类时冲突
    kwargs.pop('details', None)
    kwargs.pop('errorCode', None)
    kwargs.pop('dataOperation', None)
    kwargs.pop('dataSource', None)
    kwargs.pop('format', None)
    kwargs.pop('lineNumber', None)
    details = {'format': format, 'lineNumber': lineNumber}
    super().__init__(
      message,
      errorCode=errorCode,
      details=details,
      **kwargs
    )


class DataConversionException(DataException):
  """数据转换异常"""

  def __init__(
    self,
    message: str = "数据转换失败",
    sourceType: str = None,
    targetType: str = None,
    value: Any = None,
    errorCode: str = "DATA_003",
    **kwargs
  ):
    # 清理kwargs中的参数，避免传递给父类时冲突
    kwargs.pop('details', None)
    kwargs.pop('errorCode', None)
    kwargs.pop('dataOperation', None)
    kwargs.pop('dataSource', None)
    kwargs.pop('sourceType', None)
    kwargs.pop('targetType', None)
    kwargs.pop('value', None)
    details = {
      'sourceType': sourceType,
      'targetType': targetType,
      'value': str(value)
    }
    super().__init__(
      message,
      errorCode=errorCode,
      details=details,
      **kwargs
    )


# 导出所有异常类
__all__ = [
  'AppException',
  'DatabaseException',
  'ConnectionException',
  'QueryExecutionException',
  'TransactionException',
  'BusinessException',
  'ValidationException',
  'NotFoundException',
  'DuplicateException',
  'ConfigurationException',
  'DataException',
  'DataParsingException',
  'DataConversionException',
]
