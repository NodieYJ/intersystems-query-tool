#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试基础设施模块

提供测试相关的工具和设施：
- Mock 工厂
- Fixture 管理器
- 数据工厂
"""

from src.infrastructure.testing.mock_factory import MockFactory
from src.infrastructure.testing.fixture_manager import (
  FixtureManager,
  getFixtureManager,
  registerTestFixtures
)
from src.infrastructure.testing.data_factory import (
  DataFactory,
  UserData,
  QueryHistoryData,
  DataResultData
)


__all__ = [
  # Mock 工厂
  'MockFactory',

  # Fixture 管理器
  'FixtureManager',
  'getFixtureManager',
  'registerTestFixtures',

  # 数据工厂
  'DataFactory',
  'UserData',
  'QueryHistoryData',
  'DataResultData',
]
