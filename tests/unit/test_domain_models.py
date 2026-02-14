#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
领域模型单元测试

测试所有领域模型的创建、序列化和反序列化。
"""

import sys
import os
import unittest
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.business.models import (
    DatabaseType,
    QueryStatus,
    DatabaseConnection,
    QueryResult,
    QueryHistory,
    ColumnMetadata,
    TableMetadata,
    generate_query_id,
    generate_connection_id,
)


class TestDatabaseType(unittest.TestCase):
  """测试数据库类型枚举"""

  def test_database_type_values(self):
    """测试数据库类型枚举值"""
    assert DatabaseType.POSTGRESQL.value == "postgresql"
    assert DatabaseType.MYSQL.value == "mysql"
    assert DatabaseType.SQLITE.value == "sqlite"
    assert DatabaseType.IRIS.value == "iris"
    assert DatabaseType.CACHE.value == "cache"

  def test_database_type_from_string(self):
    """测试从字符串创建枚举"""
    assert DatabaseType("postgresql") == DatabaseType.POSTGRESQL
    assert DatabaseType("mysql") == DatabaseType.MYSQL
    assert DatabaseType("iris") == DatabaseType.IRIS


class TestQueryStatus:
  """测试查询状态枚举"""

  def test_query_status_values(self):
    """测试查询状态枚举值"""
    assert QueryStatus.PENDING.value == "pending"
    assert QueryStatus.RUNNING.value == "running"
    assert QueryStatus.SUCCESS.value == "success"
    assert QueryStatus.FAILED.value == "failed"
    assert QueryStatus.CANCELLED.value == "cancelled"


class TestDatabaseConnection:
  """测试数据库连接模型"""

  def test_create_connection(self):
    """测试创建连接实例"""
    connection = DatabaseConnection(
      id="conn_001",
      name="测试连接",
      host="localhost",
      port=5432,
      database="testdb",
      username="admin",
      database_type=DatabaseType.POSTGRESQL
    )

    assert connection.id == "conn_001"
    assert connection.name == "测试连接"
    assert connection.host == "localhost"
    assert connection.port == 5432
    assert connection.database == "testdb"
    assert connection.username == "admin"
    assert connection.database_type == DatabaseType.POSTGRESQL
    assert connection.is_active is True
    assert connection.schema is None

  def test_connection_with_optional_fields(self):
    """测试带可选字段的连接"""
    now = datetime.now()
    connection = DatabaseConnection(
      id="conn_002",
      name="生产数据库",
      host="192.168.1.1",
      port=3306,
      database="proddb",
      username="root",
      database_type=DatabaseType.MYSQL,
      schema="public",
      is_active=True,
      last_connected_at=now
    )

    assert connection.schema == "public"
    assert connection.last_connected_at == now

  def test_connection_to_dict(self):
    """测试连接序列化为字典"""
    connection = DatabaseConnection(
      id="conn_003",
      name="测试",
      host="localhost",
      port=5432,
      database="db",
      username="user",
      database_type=DatabaseType.SQLITE
    )

    data = connection.to_dict()

    assert data['id'] == "conn_003"
    assert data['name'] == "测试"
    assert data['database_type'] == "sqlite"
    assert 'created_at' in data

  def test_connection_from_dict(self):
    """测试从字典反序列化连接"""
    data = {
      'id': 'conn_004',
      'name': '从字典创建',
      'host': '127.0.0.1',
      'port': 5432,
      'database': 'mydb',
      'username': 'postgres',
      'database_type': 'postgresql',
      'is_active': True,
      'created_at': datetime.now().isoformat()
    }

    connection = DatabaseConnection.from_dict(data)

    assert connection.id == "conn_004"
    assert connection.name == "从字典创建"
    assert connection.database_type == DatabaseType.POSTGRESQL

  def test_connection_roundtrip(self):
    """测试序列化和反序列化的往返"""
    original = DatabaseConnection(
      id="conn_005",
      name="往返测试",
      host="localhost",
      port=5432,
      database="test",
      username="user",
      database_type=DatabaseType.IRIS,
      schema="test_schema"
    )

    data = original.to_dict()
    restored = DatabaseConnection.from_dict(data)

    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.database_type == original.database_type
    assert restored.schema == original.schema


class TestQueryResult:
  """测试查询结果模型"""

  def test_create_result(self):
    """测试创建结果实例"""
    result = QueryResult(
      query_id="query_001",
      sql="SELECT * FROM users",
      rows=[{"id": 1, "name": "张三"}],
      execution_time_ms=15.5,
      row_count=1,
      column_names=["id", "name"]
    )

    assert result.query_id == "query_001"
    assert result.sql == "SELECT * FROM users"
    assert result.row_count == 1
    assert result.execution_time_ms == 15.5

  def test_result_is_empty(self):
    """测试空结果检查"""
    empty_result = QueryResult(
      query_id="query_002",
      sql="SELECT * FROM empty_table",
      rows=[],
      execution_time_ms=5.0,
      row_count=0,
      column_names=[]
    )

    assert empty_result.is_empty() is True

    non_empty_result = QueryResult(
      query_id="query_003",
      sql="SELECT * FROM users",
      rows=[{"id": 1}],
      execution_time_ms=10.0,
      row_count=1,
      column_names=["id"]
    )

    assert non_empty_result.is_empty() is False

  def test_result_to_dict(self):
    """测试结果序列化"""
    result = QueryResult(
      query_id="query_004",
      sql="SELECT 1",
      rows=[{"1": 1}],
      execution_time_ms=1.0,
      row_count=1,
      column_names=["1"],
      connection_id="conn_001"
    )

    data = result.to_dict()

    assert data['query_id'] == "query_004"
    assert data['connection_id'] == "conn_001"
    assert data['row_count'] == 1


class TestQueryHistory:
  """测试查询历史模型"""

  def test_create_history(self):
    """测试创建历史记录"""
    history = QueryHistory(
      id="hist_001",
      sql="SELECT * FROM users",
      connection_id="conn_001",
      executed_at=datetime.now(),
      execution_time_ms=20.0,
      row_count=100,
      status=QueryStatus.SUCCESS
    )

    assert history.id == "hist_001"
    assert history.status == QueryStatus.SUCCESS
    assert history.row_count == 100

  def test_history_with_error(self):
    """测试带错误信息的历史记录"""
    history = QueryHistory(
      id="hist_002",
      sql="SELECT * FROM invalid_table",
      connection_id="conn_001",
      executed_at=datetime.now(),
      execution_time_ms=0.0,
      row_count=0,
      status=QueryStatus.FAILED,
      error_message="Table does not exist"
    )

    assert history.status == QueryStatus.FAILED
    assert history.error_message == "Table does not exist"

  def test_history_to_dict(self):
    """测试历史记录序列化"""
    now = datetime.now()
    history = QueryHistory(
      id="hist_003",
      sql="SELECT 1",
      connection_id="conn_002",
      executed_at=now,
      execution_time_ms=5.0,
      row_count=1,
      status=QueryStatus.SUCCESS
    )

    data = history.to_dict()

    assert data['id'] == "hist_003"
    assert data['status'] == "success"
    assert 'executed_at' in data


class TestColumnMetadata:
  """测试列元数据模型"""

  def test_create_column(self):
    """测试创建列元数据"""
    column = ColumnMetadata(
      column_name="id",
      data_type="INTEGER",
      is_nullable=False,
      is_primary_key=True
    )

    assert column.column_name == "id"
    assert column.data_type == "INTEGER"
    assert column.is_nullable is False
    assert column.is_primary_key is True

  def test_column_with_precision(self):
    """测试带精度的列"""
    column = ColumnMetadata(
      column_name="price",
      data_type="DECIMAL",
      precision=10,
      scale=2,
      is_nullable=True
    )

    assert column.precision == 10
    assert column.scale == 2

  def test_column_to_dict(self):
    """测试列元数据序列化"""
    column = ColumnMetadata(
      column_name="name",
      data_type="VARCHAR",
      max_length=255
    )

    data = column.to_dict()

    assert data['column_name'] == "name"
    assert data['max_length'] == 255


class TestTableMetadata:
  """测试表元数据模型"""

  def test_create_table(self):
    """测试创建表元数据"""
    columns = [
      ColumnMetadata(column_name="id", data_type="INTEGER", is_primary_key=True),
      ColumnMetadata(column_name="name", data_type="VARCHAR", max_length=100)
    ]

    table = TableMetadata(
      table_name="users",
      schema="public",
      columns=columns,
      row_count=1000
    )

    assert table.table_name == "users"
    assert table.schema == "public"
    assert len(table.columns) == 2
    assert table.row_count == 1000

  def test_table_to_dict(self):
    """测试表元数据序列化"""
    columns = [
      ColumnMetadata(column_name="id", data_type="INTEGER")
    ]

    table = TableMetadata(
      table_name="test_table",
      columns=columns
    )

    data = table.to_dict()

    assert data['table_name'] == "test_table"
    assert len(data['columns']) == 1

  def test_table_from_dict(self):
    """测试从字典反序列化表"""
    data = {
      'table_name': 'products',
      'schema': 'public',
      'columns': [
        {'column_name': 'id', 'data_type': 'INTEGER', 'is_primary_key': True}
      ],
      'row_count': 500
    }

    table = TableMetadata.from_dict(data)

    assert table.table_name == "products"
    assert len(table.columns) == 1
    assert table.columns[0].is_primary_key is True


class TestIdGenerators:
  """测试 ID 生成器"""

  def test_generate_query_id(self):
    """测试查询 ID 生成"""
    query_id = generate_query_id()

    assert query_id.startswith("query_")
    assert len(query_id) == 18  # "query_" + 12 个字符

  def test_generate_connection_id(self):
    """测试连接 ID 生成"""
    conn_id = generate_connection_id()

    assert conn_id.startswith("conn_")
    assert len(conn_id) == 17  # "conn_" + 12 个字符

  def test_id_uniqueness(self):
    """测试 ID 唯一性"""
    ids = [generate_query_id() for _ in range(100)]

    assert len(set(ids)) == 100  # 所有 ID 应该唯一


if __name__ == '__main__':
  import unittest

  # 创建测试套件
  loader = unittest.TestLoader()
  suite = unittest.TestSuite()

  # 添加所有测试类
  suite.addTests(loader.loadTestsFromTestCase(TestDatabaseType))
  suite.addTests(loader.loadTestsFromTestCase(TestQueryStatus))
  suite.addTests(loader.loadTestsFromTestCase(TestDatabaseConnection))
  suite.addTests(loader.loadTestsFromTestCase(TestQueryResult))
  suite.addTests(loader.loadTestsFromTestCase(TestQueryHistory))
  suite.addTests(loader.loadTestsFromTestCase(TestColumnMetadata))
  suite.addTests(loader.loadTestsFromTestCase(TestTableMetadata))
  suite.addTests(loader.loadTestsFromTestCase(TestIdGenerators))

  # 运行测试
  runner = unittest.TextTestRunner(verbosity=2)
  result = runner.run(suite)

  # 退出码
  sys.exit(0 if result.wasSuccessful() else 1)
