#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pytest 配置文件

提供全局 fixtures 和测试配置。
"""

import pytest
import sys
import os
from pathlib import Path

# 添加 src 目录到 Python 路径
srcPath = Path(__file__).parent.parent / "src"
if str(srcPath) not in sys.path:
  sys.path.insert(0, str(srcPath))


@pytest.fixture(scope="session")
def srcDirectory():
  """src 目录路径 fixture"""
  return Path(__file__).parent.parent / "src"


@pytest.fixture(scope="session")
def configDirectory():
  """配置目录路径 fixture"""
  return Path(__file__).parent.parent / "config"


@pytest.fixture
def tempConfigFile(tmp_path):
  """临时配置文件 fixture"""
  configContent = '''
{
  "database": {
    "server": "localhost",
    "port": 1972,
    "namespace": "USER",
    "username": "test",
    "password": "test123"
  },
  "ui": {
    "theme": "dark",
    "language": "zh-CN"
  },
  "logging": {
    "level": "DEBUG",
    "file": "app.log"
  }
}
'''
  configFile = tmp_path / "config.json"
  configFile.write_text(configContent)
  return str(configFile)


@pytest.fixture
def mockDatabaseConnection():
  """模拟数据库连接 fixture"""
  class MockConnection:
    def __init__(self):
      self.connected = True
      self.serverInfo = {"server": "localhost", "port": 1972}

    def close(self):
      self.connected = False

    def isConnected(self):
      return self.connected

  return MockConnection()


@pytest.fixture
def mockQueryResult():
  """模拟查询结果 fixture"""
  return [
    {"id": 1, "name": "测试1", "value": 100},
    {"id": 2, "name": "测试2", "value": 200},
    {"id": 3, "name": "测试3", "value": 300},
  ]


@pytest.fixture
def sampleQueryData():
  """示例查询数据 fixture"""
  return {
    "query": "SELECT * FROM Sample.Table WHERE ID > ?",
    "params": [0],
    "expectedRows": 3,
    "columns": ["ID", "Name", "Value"]
  }


@pytest.fixture
def emptyQueryResult():
  """空查询结果 fixture"""
  return []


@pytest.fixture
def errorQueryScenario():
  """错误查询场景 fixture"""
  return {
    "query": "INVALID SQL SYNTAX",
    "errorMessage": "SQL syntax error",
    "errorCode": "DB_002"
  }
