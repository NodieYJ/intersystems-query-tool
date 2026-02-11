#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
接口定义模块

提供所有核心业务接口的抽象基类定义。
用于实现依赖倒置原则，便于单元测试和代码扩展。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar


# 定义通用类型变量
T = TypeVar('T')
U = TypeVar('U')
IdType = TypeVar('IdType')


class IRepository(ABC, Generic[T, IdType]):
  """
  数据仓储接口

  定义基础的数据访问操作。
  所有数据仓储类都应该实现此接口。
  """

  @abstractmethod
  def getById(self, id: IdType) -> Optional[T]:
    """
    根据ID获取实体

    Args:
      id: 实体ID

    Returns:
      Optional[T]: 找到返回实体，否则返回None
    """
    pass

  @abstractmethod
  def getAll(self) -> List[T]:
    """
    获取所有实体

    Returns:
      List[T]: 所有实体列表
    """
    pass

  @abstractmethod
  def save(self, entity: T) -> bool:
    """
    保存实体（新增或更新）

    Args:
      entity: 要保存的实体

    Returns:
      bool: 是否保存成功
    """
    pass

  @abstractmethod
  def delete(self, id: IdType) -> bool:
    """
    根据ID删除实体

    Args:
      id: 要删除的实体ID

    Returns:
      bool: 是否删除成功
    """
    pass

  @abstractmethod
  def count(self) -> int:
    """
    获取实体总数

    Returns:
      int: 实体数量
    """
    pass

  @abstractmethod
  def exists(self, id: IdType) -> bool:
    """
    检查实体是否存在

    Args:
      id: 实体ID

    Returns:
      bool: 是否存在
    """
    pass


class IQueryRepository(ABC):
  """
  查询仓储接口

  定义数据库查询操作。
  专门用于处理复杂查询场景。
  """

  @abstractmethod
  def executeQuery(
    self,
    query: str,
    params: Optional[List[Any]] = None
  ) -> List[Dict[str, Any]]:
    """
    执行查询语句

    Args:
      query: SQL查询语句
      params: 查询参数

    Returns:
      List[Dict[str, Any]]: 查询结果列表
    """
    pass

  @abstractmethod
  def executeNonQuery(
    self,
    query: str,
    params: Optional[List[Any]] = None
  ) -> bool:
    """
    执行非查询语句（INSERT/UPDATE/DELETE）

    Args:
      query: SQL语句
      params: 语句参数

    Returns:
      bool: 是否执行成功
    """
    pass

  @abstractmethod
  def executeScalar(self, query: str, params: Optional[List[Any]] = None) -> Any:
    """
    执行标量查询（返回单个值）

    Args:
      query: SQL查询语句
      params: 查询参数

    Returns:
      Any: 查询结果（单个值）
    """
    pass


class IService(ABC, Generic[T]):
  """
  服务基类接口

  定义基础业务服务操作。
  所有业务服务类都应该实现此接口。
  """

  @abstractmethod
  def execute(self, *args, **kwargs) -> Any:
    """
    执行服务操作

    Args:
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      Any: 操作结果
    """
    pass

  @abstractmethod
  def validate(self, *args, **kwargs) -> bool:
    """
    验证输入参数

    Args:
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      bool: 验证是否通过
    """
    pass


class IDataService(IService):
  """
  数据服务接口

  专门用于数据访问的服务接口。
  """

  @abstractmethod
  def getData(
    self,
    query: str,
    params: Optional[List[Any]] = None
  ) -> Optional[List[Dict[str, Any]]]:
    """
    获取数据

    Args:
      query: SQL查询语句
      params: 查询参数

    Returns:
      Optional[List[Dict[str, Any]]]: 查询结果
    """
    pass

  @abstractmethod
  def saveData(
    self,
    query: str,
    params: Optional[List[Any]] = None
  ) -> bool:
    """
    保存数据

    Args:
      query: SQL语句
      params: 语句参数

    Returns:
      bool: 是否保存成功
    """
    pass

  @abstractmethod
  def testConnection(self) -> bool:
    """
    测试数据库连接

    Returns:
      bool: 连接是否正常
    """
    pass


class IDataAnalysisService(IService):
  """
  数据分析服务接口
  """

  @abstractmethod
  def loadFromDataframe(self, df) -> bool:
    """
    从DataFrame加载数据

    Args:
      df: pandas DataFrame对象

    Returns:
      bool: 是否加载成功
    """
    pass

  @abstractmethod
  def loadFromFile(self, filePath: str) -> bool:
    """
    从文件加载数据

    Args:
      filePath: 文件路径

    Returns:
      bool: 是否加载成功
    """
    pass

  @abstractmethod
  def getStatistics(self) -> Dict[str, Any]:
    """
    获取统计信息

    Returns:
      Dict[str, Any]: 统计信息字典
    """
    pass

  @abstractmethod
  def clearData(self) -> None:
    """
    清除数据
    """
    pass


class IAsyncExecutor(ABC):
  """
  异步执行器接口

  定义异步任务执行操作。
  用于在UI线程中安全执行耗时操作。
  """

  @abstractmethod
  def executeAsync(self, task, *args, **kwargs) -> Any:
    """
    异步执行任务

    Args:
      task: 要执行的任务函数
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      Any: 任务执行结果
    """
    pass

  @abstractmethod
  def submitTask(self, taskId: str, task, *args, **kwargs) -> bool:
    """
    提交异步任务

    Args:
      taskId: 任务唯一标识
      task: 要执行的任务函数
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      bool: 是否提交成功
    """
    pass

  @abstractmethod
  def cancelTask(self, taskId: str) -> bool:
    """
    取消异步任务

    Args:
      taskId: 任务唯一标识

    Returns:
      bool: 是否取消成功
    """
    pass

  @abstractmethod
  def getTaskStatus(self, taskId: str) -> Dict[str, Any]:
    """
    获取任务状态

    Args:
      taskId: 任务唯一标识

    Returns:
      Dict[str, Any]: 任务状态信息
    """
    pass


class IPlugin(ABC):
  """
  插件接口

  定义插件生命周期管理操作。
  所有插件类都应该实现此接口。
  """

  @abstractmethod
  def getName(self) -> str:
    """
    获取插件名称

    Returns:
      str: 插件名称
    """
    pass

  @abstractmethod
  def getVersion(self) -> str:
    """
    获取插件版本

    Returns:
      str: 插件版本号
    """
    pass

  @abstractmethod
  def getDescription(self) -> str:
    """
    获取插件描述

    Returns:
      str: 插件描述信息
    """
    pass

  @abstractmethod
  def initialize(self) -> bool:
    """
    初始化插件

    Returns:
      bool: 是否初始化成功
    """
    pass

  @abstractmethod
  def execute(self, *args, **kwargs) -> Any:
    """
    执行插件功能

    Args:
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      Any: 执行结果
    """
    pass

  @abstractmethod
  def shutdown(self) -> None:
    """
    关闭插件
    """
    pass


class IEventHandler(ABC):
  """
  事件处理器接口

  定义事件处理操作。
  """

  @abstractmethod
  def handleEvent(self, eventType: str, eventData: Dict[str, Any]) -> None:
    """
    处理事件

    Args:
      eventType: 事件类型
      eventData: 事件数据
    """
    pass


class IConfigProvider(ABC):
  """
  配置提供器接口

  定义配置读取操作。
  """

  @abstractmethod
  def get(self, key: str, default: Any = None) -> Any:
    """
    获取配置值

    Args:
      key: 配置键
      default: 默认值

    Returns:
      Any: 配置值
    """
    pass

  @abstractmethod
  def set(self, key: str, value: Any) -> bool:
    """
    设置配置值

    Args:
      key: 配置键
      value: 配置值

    Returns:
      bool: 是否设置成功
    """
    pass

  @abstractmethod
  def load(self) -> bool:
    """
    加载配置

    Returns:
      bool: 是否加载成功
    """
    pass

  @abstractmethod
  def save(self) -> bool:
    """
    保存配置

    Returns:
      bool: 是否保存成功
    """
    pass


# 导出所有接口
__all__ = [
  'IRepository',
  'IQueryRepository',
  'IService',
  'IDataService',
  'IDataAnalysisService',
  'IAsyncExecutor',
  'IPlugin',
  'IEventHandler',
  'IConfigProvider',
  'T',
  'U',
  'IdType',
]
