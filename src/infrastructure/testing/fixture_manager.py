#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fixture 管理器模块

提供测试 fixture 的注册和管理功能。
用于 pytest fixtures 的集中管理。
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
import pytest


@dataclass
class FixtureDefinition:
  """Fixture 定义类"""
  name: str
  factory: Callable
  scope: str = "function"
  autouse: bool = False
  params: Optional[List[Any]] = None


class FixtureManager:
  """Fixture 管理器"""

  def __init__(self):
    """初始化 Fixture 管理器"""
    self._fixtures: Dict[str, FixtureDefinition] = {}
    self._registered = False

  def registerFixture(
    self,
    name: str,
    factory: Callable,
    scope: str = "function",
    autouse: bool = False,
    params: Optional[List[Any]] = None
  ) -> None:
    """
    注册一个 fixture

    Args:
      name: fixture 名称
      factory: fixture 工厂函数
      scope: fixture 作用域
      autouse: 是否自动使用
      params: 参数列表（用于 parametrize）
    """
    self._fixtures[name] = FixtureDefinition(
      name=name,
      factory=factory,
      scope=scope,
      autouse=autouse,
      params=params
    )

  def getFixture(self, name: str) -> FixtureDefinition:
    """
    获取 fixture 定义

    Args:
      name: fixture 名称

    Returns:
      FixtureDefinition: fixture 定义
    """
    if name not in self._fixtures:
      raise ValueError(f"Fixture '{name}' not found")
    return self._fixtures[name]

  def listFixtures(self) -> List[str]:
    """列出所有注册的 fixture 名称"""
    return list(self._fixtures.keys())

  def createPytestFixtures(self) -> None:
    """将注册的 fixture 转换为 pytest fixtures"""
    for fixtureDef in self._fixtures.values():
      self._createPytestFixture(fixtureDef)

  def _createPytestFixture(self, fixtureDef: FixtureDefinition) -> None:
    """
    创建 pytest fixture

    Args:
      fixtureDef: fixture 定义
    """
    # 使用 pytest.fixture 装饰器创建 fixture
    fixture = pytest.fixture(
      scope=fixtureDef.scope,
      autouse=fixtureDef.autouse,
      params=fixtureDef.params
    )(fixtureDef.factory)


# 单例实例
_fixtureManager = FixtureManager()


def getFixtureManager() -> FixtureManager:
  """获取 Fixture 管理器单例"""
  return _fixtureManager


def registerTestFixtures() -> None:
  """注册所有测试 fixtures"""
  manager = getFixtureManager()

  # 数据库连接 fixture
  def dbConnection():
    return {
      "server": "localhost",
      "port": 1972,
      "namespace": "USER",
      "connected": True
    }

  manager.registerFixture(
    name="dbConnection",
    factory=dbConnection,
    scope="session"
  )

  # 查询历史 fixture
  def queryHistory():
    return [
      {"id": 1, "query": "SELECT * FROM Table1", "timestamp": "2026-01-01"},
      {"id": 2, "query": "SELECT * FROM Table2", "timestamp": "2026-01-02"},
    ]

  manager.registerFixture(
    name="queryHistory",
    factory=queryHistory,
    scope="function"
  )

  # 测试配置 fixture
  def testConfig():
    return {
      "timeout": 30,
      "retries": 3,
      "cacheEnabled": True
    }

  manager.registerFixture(
    name="testConfig",
    factory=testConfig,
    scope="session"
  )

  # 用户认证 fixture
  def userAuth():
    return {
      "username": "testUser",
      "token": "testToken123",
      "permissions": ["read", "write"]
    }

  manager.registerFixture(
    name="userAuth",
    factory=userAuth,
    scope="function"
  )

  # 模拟数据 fixture
  def mockData():
    return {
      "items": [
        {"id": i, "name": f"Item{i}", "value": i * 10}
        for i in range(1, 6)
      ],
      "total": 5
    }

  manager.registerFixture(
    name="mockData",
    factory=mockData,
    scope="function"
  )


# 导出
__all__ = [
  'FixtureManager',
  'getFixtureManager',
  'registerTestFixtures',
]
