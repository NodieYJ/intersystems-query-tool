#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mock 工厂模块

提供创建各种 Mock 对象的工厂类。
用于单元测试中的依赖隔离。
"""

from unittest.mock import MagicMock, Mock, PropertyMock
from typing import Any, Dict, List, Optional
from src.infrastructure.interfaces import (
  IRepository,
  IQueryRepository,
  IService,
  IDataService
)


class MockFactory:
  """Mock 对象工厂类"""

  @staticmethod
  def createMockRepository(
    entityType: type = None,
    idField: str = "id"
  ) -> IRepository:
    """
    创建模拟的 Repository

    Args:
      entityType: 实体类型
      idField: ID 字段名

    Returns:
      IRepository: 模拟的 Repository
    """
    mockRepo = MagicMock(spec=IRepository)

    # 设置默认返回值
    mockRepo.getById.return_value = None
    mockRepo.getAll.return_value = []
    mockRepo.save.return_value = True
    mockRepo.delete.return_value = True
    mockRepo.count.return_value = 0
    mockRepo.exists.return_value = False

    return mockRepo

  @staticmethod
  def createMockQueryRepository(
    queryResult: List[Dict[str, Any]] = None,
    executeSuccess: bool = True
  ) -> IQueryRepository:
    """
    创建模拟的 Query Repository

    Args:
      queryResult: 查询结果
      executeSuccess: 执行是否成功

    Returns:
      IQueryRepository: 模拟的 Query Repository
    """
    mockRepo = MagicMock(spec=IQueryRepository)

    # 设置默认返回值
    mockRepo.executeQuery.return_value = queryResult or []
    mockRepo.executeNonQuery.return_value = executeSuccess
    mockRepo.executeScalar.return_value = 1 if executeSuccess else None

    return mockRepo

  @staticmethod
  def createMockDataService(
    getDataResult: List[Dict[str, Any]] = None,
    saveDataSuccess: bool = True,
    testConnectionSuccess: bool = True
  ) -> IDataService:
    """
    创建模拟的 Data Service

    Args:
      getDataResult: getData 方法返回值
      saveDataSuccess: saveData 方法是否成功
      testConnectionSuccess: testConnection 方法是否成功

    Returns:
      IDataService: 模拟的 Data Service
    """
    mockService = MagicMock(spec=IDataService)

    mockService.getData.return_value = getDataResult or []
    mockService.saveData.return_value = saveDataSuccess
    mockService.testConnection.return_value = testConnectionSuccess
    mockService.execute.return_value = True
    mockService.validate.return_value = True

    return mockService

  @staticmethod
  def createMockService(
    serviceType: type = None,
    returnValue: Any = None,
    sideEffect: callable = None
  ) -> IService:
    """
    创建模拟的 Service

    Args:
      serviceType: 服务类型（用于 spec）
      returnValue: 默认返回值
      sideEffect: 副作用函数

    Returns:
      IService: 模拟的 Service
    """
    mockService = MagicMock(spec=IService)

    mockService.execute.return_value = returnValue
    if sideEffect:
      mockService.execute.side_effect = sideEffect

    mockService.validate.return_value = True

    return mockService

  @staticmethod
  def createMockConfigProvider(
    configData: Dict[str, Any] = None
  ) -> MagicMock:
    """
    创建模拟的配置提供器

    Args:
      configData: 配置数据

    Returns:
      MagicMock: 模拟的配置提供器
    """
    mockProvider = MagicMock()

    mockProvider.get.side_effect = lambda key, default=None: configData.get(key, default) if configData else default
    mockProvider.set.return_value = True
    mockProvider.load.return_value = True
    mockProvider.save.return_value = True

    return mockProvider

  @staticmethod
  def createMockDatabaseConnection(
    connected: bool = True,
    serverInfo: Dict[str, Any] = None
  ) -> MagicMock:
    """
    创建模拟的数据库连接

    Args:
      connected: 是否已连接
      serverInfo: 服务器信息

    Returns:
      MagicMock: 模拟的数据库连接
    """
    mockConn = MagicMock()

    mockConn.isConnected.return_value = connected
    mockConn.getServerInfo.return_value = serverInfo or {"server": "localhost", "port": 1972}
    mockConn.close.return_value = None
    mockConn.ping.return_value = connected

    return mockConn

  @staticmethod
  def createMockCursor(
    queryResult: List[Dict[str, Any]] = None,
    rowCount: int = 0
  ) -> MagicMock:
    """
    创建模拟的数据库 Cursor

    Args:
      queryResult: 查询结果
      rowCount: 影响行数

    Returns:
      MagicMock: 模拟的 Cursor
    """
    mockCursor = MagicMock()

    # 设置 fetchall 返回值
    if queryResult:
      mockCursor.fetchall.return_value = [
        tuple(row.values()) for row in queryResult
      ]
      mockCursor.description.return_value = [
        (col,) for col in queryResult[0].keys()
      ]
    else:
      mockCursor.fetchall.return_value = []
      mockCursor.description.return_value = []

    mockCursor.rowcount = rowCount
    mockCursor.execute.return_value = None
    mockCursor.close.return_value = None

    return mockCursor

  @staticmethod
  def createMockLogger() -> MagicMock:
    """
    创建模拟的 Logger

    Returns:
      MagicMock: 模拟的 Logger
    """
    mockLogger = MagicMock()

    mockLogger.debug.return_value = None
    mockLogger.info.return_value = None
    mockLogger.warning.return_value = None
    mockLogger.error.return_value = None
    mockLogger.critical.return_value = None

    return mockLogger

  @staticmethod
  def createMockEventBus() -> MagicMock:
    """
    创建模拟的事件总线

    Returns:
      MagicMock: 模拟的事件总线
    """
    mockBus = MagicMock()

    mockBus.publish.return_value = None
    mockBus.subscribe.return_value = None
    mockBus.unsubscribe.return_value = None
    mockBus.emit.return_value = None

    return mockBus


# 导出 MockFactory
__all__ = ['MockFactory']
