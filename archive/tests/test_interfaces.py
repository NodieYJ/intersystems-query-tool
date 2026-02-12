#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
接口和异常体系单元测试

测试接口定义和异常处理功能。
"""

import pytest
from unittest.mock import MagicMock, Mock
from src.infrastructure.interfaces import (
  IRepository,
  IQueryRepository,
  IService,
  IDataService,
  IDataAnalysisService,
)
from src.infrastructure.exceptions import (
  AppException,
  DatabaseException,
  ConnectionException,
  QueryExecutionException,
  TransactionException,
  BusinessException,
  ValidationException,
  NotFoundException,
  DuplicateException,
  ConfigurationException,
  DataException,
  DataParsingException,
  DataConversionException,
)


class TestInterfaces:
  """接口测试类"""

  def testIRepositoryIsAbstract(self):
    """测试 IRepository 是抽象类"""
    with pytest.raises(TypeError):
      IRepository()

  def testIQueryRepositoryIsAbstract(self):
    """测试 IQueryRepository 是抽象类"""
    with pytest.raises(TypeError):
      IQueryRepository()

  def testIServiceIsAbstract(self):
    """测试 IService 是抽象类"""
    with pytest.raises(TypeError):
      IService()

  def testIDataServiceIsAbstract(self):
    """测试 IDataService 是抽象类"""
    with pytest.raises(TypeError):
      IDataService()

  def testMockRepositoryImplementsInterface(self):
    """测试 Mock Repository 实现接口"""
    mockRepo = MagicMock(spec=IRepository)
    assert hasattr(mockRepo, 'getById')
    assert hasattr(mockRepo, 'getAll')
    assert hasattr(mockRepo, 'save')
    assert hasattr(mockRepo, 'delete')
    assert hasattr(mockRepo, 'count')
    assert hasattr(mockRepo, 'exists')

  def testMockQueryRepositoryImplementsInterface(self):
    """测试 Mock Query Repository 实现接口"""
    mockRepo = MagicMock(spec=IQueryRepository)
    assert hasattr(mockRepo, 'executeQuery')
    assert hasattr(mockRepo, 'executeNonQuery')
    assert hasattr(mockRepo, 'executeScalar')


class TestAppException:
  """应用异常测试类"""

  def testAppExceptionCreation(self):
    """测试创建应用异常"""
    exc = AppException("测试错误", errorCode="APP_001")
    assert exc.message == "测试错误"
    assert exc.errorCode == "APP_001"
    assert exc.details == {}
    assert exc.cause is None

  def testAppExceptionWithDetails(self):
    """测试创建带详情异常"""
    details = {"key": "value"}
    exc = AppException("错误", errorCode="APP_002", details=details)
    assert exc.details == details

  def testAppExceptionWithCause(self):
    """测试创建带原始异常的异常"""
    originalExc = ValueError("原始错误")
    exc = AppException("错误", errorCode="APP_003", cause=originalExc)
    assert exc.cause == originalExc

  def testAppExceptionStr(self):
    """测试异常字符串表示"""
    exc = AppException("测试消息", errorCode="TEST_001")
    assert str(exc) == "[TEST_001] 测试消息"

  def testAppExceptionToDict(self):
    """测试异常转换为字典"""
    exc = AppException("测试", errorCode="TEST_002")
    result = exc.toDict()
    assert result["errorCode"] == "TEST_002"
    assert result["message"] == "测试"
    assert "timestamp" in result
    assert "details" in result


class TestDatabaseException:
  """数据库异常测试类"""

  def testDatabaseExceptionCreation(self):
    """测试创建数据库异常"""
    exc = DatabaseException("数据库错误")
    assert exc.errorCode == "DB_000"

  def testConnectionException(self):
    """测试连接异常"""
    exc = ConnectionException("连接失败")
    assert exc.errorCode == "DB_001"
    assert "连接失败" in exc.message

  def testQueryExecutionException(self):
    """测试查询执行异常"""
    exc = QueryExecutionException(
      message="查询失败",
      sql="SELECT * FROM table",
      parameters=[1, 2]
    )
    assert exc.errorCode == "DB_002"
    assert exc.details["sql"] == "SELECT * FROM table"
    assert exc.details["parameters"] == [1, 2]

  def testTransactionException(self):
    """测试事务异常"""
    exc = TransactionException("事务失败", transactionId="tx_123")
    assert exc.errorCode == "DB_003"
    assert exc.details["transactionId"] == "tx_123"


class TestBusinessException:
  """业务异常测试类"""

  def testBusinessExceptionCreation(self):
    """测试创建业务异常"""
    exc = BusinessException("业务错误")
    assert exc.errorCode == "BZ_000"

  def testValidationException(self):
    """测试验证异常"""
    exc = ValidationException(
      message="验证失败",
      field="username",
      value="",
      rule="not_empty"
    )
    assert exc.errorCode == "BZ_001"
    assert exc.details["field"] == "username"
    assert exc.details["rule"] == "not_empty"

  def testNotFoundException(self):
    """测试资源不存在异常"""
    exc = NotFoundException(
      message="用户不存在",
      resourceType="User",
      resourceId=123
    )
    assert exc.errorCode == "BZ_002"
    assert exc.details["resourceType"] == "User"
    assert exc.details["resourceId"] == 123

  def testDuplicateException(self):
    """测试重复操作异常"""
    exc = DuplicateException(
      message="用户名已存在",
      resourceType="User",
      duplicateField="username"
    )
    assert exc.errorCode == "BZ_003"


class TestConfigurationException:
  """配置异常测试类"""

  def testConfigurationException(self):
    """测试配置异常"""
    exc = ConfigurationException(
      message="配置错误",
      configKey="database.server",
      expectedValue="localhost",
      actualValue="invalid"
    )
    assert exc.errorCode == "CFG_001"
    assert exc.details["configKey"] == "database.server"


class TestDataException:
  """数据异常测试类"""

  def testDataExceptionCreation(self):
    """测试创建数据异常"""
    exc = DataException("数据错误")
    assert exc.errorCode == "DATA_001"

  def testDataParsingException(self):
    """测试数据解析异常"""
    exc = DataParsingException(
      message="CSV解析失败",
      format="CSV",
      lineNumber=100
    )
    assert exc.errorCode == "DATA_002"
    assert exc.details["format"] == "CSV"
    assert exc.details["lineNumber"] == 100

  def testDataConversionException(self):
    """测试数据转换异常"""
    exc = DataConversionException(
      message="类型转换失败",
      sourceType="string",
      targetType="int",
      value="abc"
    )
    assert exc.errorCode == "DATA_003"
    assert exc.details["sourceType"] == "string"
    assert exc.details["targetType"] == "int"


class TestExceptionInheritance:
  """异常继承测试类"""

  def testDatabaseExceptionInheritance(self):
    """测试数据库异常继承"""
    exc = ConnectionException("错误")
    assert isinstance(exc, DatabaseException)
    assert isinstance(exc, AppException)

  def testBusinessExceptionInheritance(self):
    """测试业务异常继承"""
    exc = ValidationException("错误")
    assert isinstance(exc, BusinessException)
    assert isinstance(exc, AppException)

  def testDataExceptionInheritance(self):
    """测试数据异常继承"""
    exc = DataParsingException("错误")
    assert isinstance(exc, DataException)
    assert isinstance(exc, AppException)
