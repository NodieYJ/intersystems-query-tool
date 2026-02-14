#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
领域模型模块

定义核心业务领域对象，用于业务逻辑层。
所有模型使用 dataclass 定义，支持序列化和反序列化。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class DatabaseType(Enum):
  """
  数据库类型枚举

  支持的数据库类型：
  - POSTGRESQL: PostgreSQL 数据库
  - MYSQL: MySQL 数据库
  - SQLITE: SQLite 数据库
  - IRIS: Intersystems IRIS 数据库
  - CACHE: Intersystems Cache 数据库
  """
  POSTGRESQL = "postgresql"
  MYSQL = "mysql"
  SQLITE = "sqlite"
  IRIS = "iris"
  CACHE = "cache"


class QueryStatus(Enum):
  """
  查询状态枚举

  查询执行状态：
  - PENDING: 等待执行
  - RUNNING: 正在执行
  - SUCCESS: 执行成功
  - FAILED: 执行失败
  - CANCELLED: 已取消
  """
  PENDING = "pending"
  RUNNING = "running"
  SUCCESS = "success"
  FAILED = "failed"
  CANCELLED = "cancelled"


@dataclass
class DatabaseConnection:
  """
  数据库连接领域模型

  封装数据库连接的所有信息，用于业务逻辑层。

  Attributes:
    id: 连接唯一标识符
    name: 连接名称（用户自定义）
    host: 数据库主机地址
    port: 数据库端口
    database: 数据库名称
    username: 用户名
    database_type: 数据库类型
    schema: 数据库 schema（可选）
    is_active: 连接是否激活
    created_at: 创建时间
    updated_at: 更新时间（可选）
    last_connected_at: 上次连接时间（可选）

  Example:
    >>> connection = DatabaseConnection(
    ...     id="conn_001",
    ...     name="生产数据库",
    ...     host="localhost",
    ...     port=5432,
    ...     database="mydb",
    ...     username="admin",
    ...     database_type=DatabaseType.POSTGRESQL
    ... )
  """
  id: str
  name: str
  host: str
  port: int
  database: str
  username: str
  database_type: DatabaseType
  schema: Optional[str] = None
  is_active: bool = True
  created_at: datetime = field(default_factory=datetime.now)
  updated_at: Optional[datetime] = None
  last_connected_at: Optional[datetime] = None

  def to_dict(self) -> Dict[str, Any]:
    """
    转换为字典

    Returns:
      Dict[str, Any]: 包含所有字段的字典，枚举类型转为字符串
    """
    return {
      'id': self.id,
      'name': self.name,
      'host': self.host,
      'port': self.port,
      'database': self.database,
      'username': self.username,
      'database_type': self.database_type.value,
      'schema': self.schema,
      'is_active': self.is_active,
      'created_at': self.created_at.isoformat() if self.created_at else None,
      'updated_at': self.updated_at.isoformat() if self.updated_at else None,
      'last_connected_at': self.last_connected_at.isoformat() if self.last_connected_at else None
    }

  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseConnection':
    """
    从字典创建实例

    Args:
      data: 包含字段数据的字典

    Returns:
      DatabaseConnection: 创建的实例

    Raises:
      ValueError: 如果必要字段缺失或类型错误
    """
    return cls(
      id=data['id'],
      name=data['name'],
      host=data['host'],
      port=data['port'],
      database=data['database'],
      username=data['username'],
      database_type=DatabaseType(data['database_type']),
      schema=data.get('schema'),
      is_active=data.get('is_active', True),
      created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
      updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
      last_connected_at=datetime.fromisoformat(data['last_connected_at']) if data.get('last_connected_at') else None
    )


@dataclass
class QueryResult:
  """
  查询结果领域模型

  封装 SQL 查询的结果，包含执行元数据。

  Attributes:
    query_id: 查询唯一标识符
    sql: 执行的 SQL 语句
    rows: 查询结果行列表
    execution_time_ms: 执行时间（毫秒）
    row_count: 结果行数
    column_names: 列名列表
    executed_at: 执行时间
    connection_id: 连接标识符（可选）

  Example:
    >>> result = QueryResult(
    ...     query_id="query_001",
    ...     sql="SELECT * FROM users",
    ...     rows=[{"id": 1, "name": "张三"}],
    ...     execution_time_ms=15.5,
    ...     row_count=1,
    ...     column_names=["id", "name"]
    ... )
  """
  query_id: str
  sql: str
  rows: List[Dict[str, Any]]
  execution_time_ms: float
  row_count: int
  column_names: List[str]
  executed_at: datetime = field(default_factory=datetime.now)
  connection_id: Optional[str] = None

  def is_empty(self) -> bool:
    """
    检查结果是否为空

    Returns:
      bool: 如果没有数据行返回 True
    """
    return self.row_count == 0 or len(self.rows) == 0

  def to_dict(self) -> Dict[str, Any]:
    """
    转换为字典

    Returns:
      Dict[str, Any]: 包含所有字段的字典
    """
    return {
      'query_id': self.query_id,
      'sql': self.sql,
      'rows': self.rows,
      'execution_time_ms': self.execution_time_ms,
      'row_count': self.row_count,
      'column_names': self.column_names,
      'executed_at': self.executed_at.isoformat(),
      'connection_id': self.connection_id
    }

  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> 'QueryResult':
    """
    从字典创建实例

    Args:
      data: 包含字段数据的字典

    Returns:
      QueryResult: 创建的实例
    """
    return cls(
      query_id=data['query_id'],
      sql=data['sql'],
      rows=data.get('rows', []),
      execution_time_ms=data['execution_time_ms'],
      row_count=data['row_count'],
      column_names=data.get('column_names', []),
      executed_at=datetime.fromisoformat(data['executed_at']) if data.get('executed_at') else datetime.now(),
      connection_id=data.get('connection_id')
    )


@dataclass
class QueryHistory:
  """
  查询历史领域模型

  记录已执行的查询信息，用于历史查询功能。

  Attributes:
    id: 历史记录唯一标识符
    sql: 执行的 SQL 语句
    connection_id: 连接标识符
    executed_at: 执行时间
    execution_time_ms: 执行时间（毫秒）
    row_count: 结果行数
    status: 查询状态
    error_message: 错误信息（可选）
    created_at: 记录创建时间

  Example:
    >>> history = QueryHistory(
    ...     id="hist_001",
    ...     sql="SELECT * FROM users",
    ...     connection_id="conn_001",
    ...     execution_time_ms=15.5,
    ...     row_count=10,
    ...     status=QueryStatus.SUCCESS
    ... )
  """
  id: str
  sql: str
  connection_id: str
  executed_at: datetime
  execution_time_ms: float
  row_count: int
  status: QueryStatus
  error_message: Optional[str] = None
  created_at: datetime = field(default_factory=datetime.now)

  def to_dict(self) -> Dict[str, Any]:
    """
    转换为字典

    Returns:
      Dict[str, Any]: 包含所有字段的字典
    """
    return {
      'id': self.id,
      'sql': self.sql,
      'connection_id': self.connection_id,
      'executed_at': self.executed_at.isoformat(),
      'execution_time_ms': self.execution_time_ms,
      'row_count': self.row_count,
      'status': self.status.value,
      'error_message': self.error_message,
      'created_at': self.created_at.isoformat()
    }

  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> 'QueryHistory':
    """
    从字典创建实例

    Args:
      data: 包含字段数据的字典

    Returns:
      QueryHistory: 创建的实例
    """
    return cls(
      id=data['id'],
      sql=data['sql'],
      connection_id=data['connection_id'],
      executed_at=datetime.fromisoformat(data['executed_at']) if data.get('executed_at') else datetime.now(),
      execution_time_ms=data['execution_time_ms'],
      row_count=data['row_count'],
      status=QueryStatus(data['status']),
      error_message=data.get('error_message'),
      created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
    )


@dataclass
class ColumnMetadata:
  """
  列元数据领域模型

  描述数据库表中的列信息。

  Attributes:
    column_name: 列名
    data_type: 数据类型
    is_nullable: 是否可为空
    max_length: 最大长度（可选）
    precision: 精度（可选，用于数值类型）
    scale: 小数位数（可选，用于数值类型）
    is_primary_key: 是否为主键

  Example:
    >>> column = ColumnMetadata(
    ...     column_name="id",
    ...     data_type="INTEGER",
    ...     is_nullable=False,
    ...     is_primary_key=True
    ... )
  """
  column_name: str
  data_type: str
  is_nullable: bool = True
  max_length: Optional[int] = None
  precision: Optional[int] = None
  scale: Optional[int] = None
  is_primary_key: bool = False

  def to_dict(self) -> Dict[str, Any]:
    """
    转换为字典

    Returns:
      Dict[str, Any]: 包含所有字段的字典
    """
    return {
      'column_name': self.column_name,
      'data_type': self.data_type,
      'is_nullable': self.is_nullable,
      'max_length': self.max_length,
      'precision': self.precision,
      'scale': self.scale,
      'is_primary_key': self.is_primary_key
    }

  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> 'ColumnMetadata':
    """
    从字典创建实例

    Args:
      data: 包含字段数据的字典

    Returns:
      ColumnMetadata: 创建的实例
    """
    return cls(
      column_name=data['column_name'],
      data_type=data['data_type'],
      is_nullable=data.get('is_nullable', True),
      max_length=data.get('max_length'),
      precision=data.get('precision'),
      scale=data.get('scale'),
      is_primary_key=data.get('is_primary_key', False)
    )


@dataclass
class TableMetadata:
  """
  表元数据领域模型

  描述数据库表的元数据信息。

  Attributes:
    table_name: 表名
    schema: 所属 schema（可选）
    columns: 列元数据列表
    row_count: 表行数（可选）
    created_at: 表创建时间（可选）
    updated_at: 表更新时间（可选）

  Example:
    >>> column = ColumnMetadata(column_name="id", data_type="INTEGER", is_primary_key=True)
    >>> table = TableMetadata(
    ...     table_name="users",
    ...     schema="public",
    ...     columns=[column],
    ...     row_count=1000
    ... )
  """
  table_name: str
  columns: List[ColumnMetadata] = field(default_factory=list)
  schema: Optional[str] = None
  row_count: Optional[int] = None
  created_at: Optional[datetime] = None
  updated_at: Optional[datetime] = None

  def to_dict(self) -> Dict[str, Any]:
    """
    转换为字典

    Returns:
      Dict[str, Any]: 包含所有字段的字典
    """
    return {
      'table_name': self.table_name,
      'schema': self.schema,
      'columns': [col.to_dict() for col in self.columns],
      'row_count': self.row_count,
      'created_at': self.created_at.isoformat() if self.created_at else None,
      'updated_at': self.updated_at.isoformat() if self.updated_at else None
    }

  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> 'TableMetadata':
    """
    从字典创建实例

    Args:
      data: 包含字段数据的字典

    Returns:
      TableMetadata: 创建的实例
    """
    return cls(
      table_name=data['table_name'],
      schema=data.get('schema'),
      columns=[ColumnMetadata.from_dict(col) for col in data.get('columns', [])],
      row_count=data.get('row_count'),
      created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
      updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
    )


def generate_query_id() -> str:
  """
  生成唯一的查询标识符

  Returns:
    str: 格式为 "query_<uuid>" 的唯一标识符
  """
  return f"query_{uuid4().hex[:12]}"


def generate_connection_id() -> str:
  """
  生成唯一的连接标识符

  Returns:
    str: 格式为 "conn_<uuid>" 的唯一标识符
  """
  return f"conn_{uuid4().hex[:12]}"
