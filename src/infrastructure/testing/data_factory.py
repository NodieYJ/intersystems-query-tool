#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据工厂模块

提供测试数据的生成工厂。
用于快速创建各种测试数据。
"""

import uuid
import random
import string
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class UserData:
  """用户数据类"""
  id: int
  username: str
  email: str
  createdAt: datetime
  isActive: bool = True
  permissions: List[str] = field(default_factory=list)


@dataclass
class QueryHistoryData:
  """查询历史数据类"""
  id: int
  query: str
  executionTime: float
  timestamp: datetime
  status: str = "success"
  rowCount: int = 0


@dataclass
class DataResultData:
  """数据结果数据类"""
  id: int
  columns: List[str]
  rows: List[Dict[str, Any]]
  totalRows: int
  executionTime: float
  timestamp: datetime


class DataFactory:
  """测试数据工厂"""

  _idCounter = 0

  @classmethod
  def resetIdCounter(cls) -> None:
    """重置 ID 计数器"""
    cls._idCounter = 0

  @classmethod
  def generateId(cls) -> int:
    """生成唯一 ID"""
    cls._idCounter += 1
    return cls._idCounter

  @classmethod
  def generateUuid(cls) -> str:
    """生成 UUID"""
    return str(uuid.uuid4())

  @classmethod
  def randomString(cls, length: int = 10) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters, k=length))

  @classmethod
  def randomNumber(cls, minValue: int = 1, maxValue: int = 1000) -> int:
    """生成随机整数"""
    return random.randint(minValue, maxValue)

  @classmethod
  def randomFloat(cls, minValue: float = 0.0, maxValue: float = 1000.0) -> float:
    """生成随机浮点数"""
    return round(random.uniform(minValue, maxValue), 2)

  @classmethod
  def randomBool(cls) -> bool:
    """生成随机布尔值"""
    return random.choice([True, False])

  @classmethod
  def randomDate(cls, daysBack: int = 30) -> datetime:
    """生成随机日期"""
    daysAgo = random.randint(0, daysBack)
    return datetime.now() - timedelta(days=daysAgo)

  # ==================== 用户数据工厂 ====================

  @classmethod
  def createUser(
    cls,
    id: int = None,
    username: str = None,
    email: str = None,
    isActive: bool = None,
    permissions: List[str] = None
  ) -> UserData:
    """
    创建用户数据

    Args:
      id: 用户 ID
      username: 用户名
      email: 邮箱
      isActive: 是否激活
      permissions: 权限列表

    Returns:
      UserData: 用户数据对象
    """
    return UserData(
      id=id or cls.generateId(),
      username=username or f"user_{cls.randomString(5)}",
      email=email or f"{cls.randomString(8)}@example.com",
      createdAt=cls.randomDate(),
      isActive=isActive if isActive is not None else cls.randomBool(),
      permissions=permissions or ["read"]
    )

  @classmethod
  def createUserList(cls, count: int = 5) -> List[UserData]:
    """
    创建用户数据列表

    Args:
      count: 用户数量

    Returns:
      List[UserData]: 用户数据列表
    """
    return [cls.createUser() for _ in range(count)]

  # ==================== 查询历史数据工厂 ====================

  @classmethod
  def createQueryHistory(
    cls,
    id: int = None,
    query: str = None,
    executionTime: float = None,
    status: str = None,
    rowCount: int = None
  ) -> QueryHistoryData:
    """
    创建查询历史数据

    Args:
      id: 记录 ID
      query: SQL 查询语句
      executionTime: 执行时间
      status: 状态
      rowCount: 返回行数

    Returns:
      QueryHistoryData: 查询历史数据对象
    """
    return QueryHistoryData(
      id=id or cls.generateId(),
      query=query or f"SELECT * FROM Table_{cls.randomString(3)}",
      executionTime=executionTime or cls.randomFloat(0.1, 10.0),
      timestamp=cls.randomDate(),
      status=status or cls.randomChoice(["success", "success", "failed"]),
      rowCount=rowCount or cls.randomNumber(0, 1000)
    )

  @classmethod
  def createQueryHistoryList(cls, count: int = 10) -> List[QueryHistoryData]:
    """
    创建查询历史数据列表

    Args:
      count: 记录数量

    Returns:
      List[QueryHistoryData]: 查询历史数据列表
    """
    return [cls.createQueryHistory() for _ in range(count)]

  # ==================== 数据结果数据工厂 ====================

  @classmethod
  def createDataResult(
    cls,
    id: int = None,
    columns: List[str] = None,
    rowCount: int = None,
    includeMetadata: bool = True
  ) -> DataResultData:
    """
    创建数据结果数据

    Args:
      id: 结果 ID
      columns: 列名列表
      rowCount: 行数
      includeMetadata: 是否包含元数据

    Returns:
      DataResultData: 数据结果数据对象
    """
    columns = columns or ["id", "name", "value", "created_at"]
    actualRowCount = rowCount or cls.randomNumber(1, 100)

    rows = []
    for i in range(actualRowCount):
      row = {}
      for col in columns:
        if "id" in col.lower():
          row[col] = i + 1
        elif "name" in col.lower():
          row[col] = f"Item_{i + 1}"
        elif "value" in col.lower():
          row[col] = cls.randomNumber(1, 1000)
        elif "created" in col.lower() or "date" in col.lower():
          row[col] = cls.randomDate().isoformat()
        else:
          row[col] = cls.randomString(10)
      rows.append(row)

    return DataResultData(
      id=id or cls.generateId(),
      columns=columns,
      rows=rows,
      totalRows=actualRowCount,
      executionTime=cls.randomFloat(0.1, 5.0),
      timestamp=datetime.now()
    )

  @classmethod
  def createDataResultList(cls, count: int = 5) -> List[DataResultData]:
    """
    创建数据结果数据列表

    Args:
      count: 结果数量

    Returns:
      List[DataResultData]: 数据结果数据列表
    """
    return [cls.createDataResult() for _ in range(count)]

  # ==================== 辅助方法 ====================

  @classmethod
  def randomChoice(cls, choices: List[Any]) -> Any:
    """从列表中随机选择一个元素"""
    return random.choice(choices)

  @classmethod
  def randomEmail(cls) -> str:
    """生成随机邮箱"""
    return f"{cls.randomString(8)}@{cls.randomString(5)}.com"

  @classmethod
  def randomPhone(cls) -> str:
    """生成随机电话号码"""
    return f"1{random.randint(3, 9)}{''.join(random.choices(string.digits, k=9))}"


# 创建默认工厂实例
dataFactory = DataFactory()


# 导出
__all__ = [
  'DataFactory',
  'UserData',
  'QueryHistoryData',
  'DataResultData',
]
