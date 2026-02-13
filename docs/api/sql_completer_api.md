# SQL 智能补全 API 文档

## SQLKeywordProvider

### 类定义

```python
class SQLKeywordProvider:
    """SQL 关键字提供者"""
```

### 方法

#### `__init__(keywords_file: str = None)`
初始化关键字提供者

**参数:**
- `keywords_file`: 关键字 JSON 文件路径，默认为 `resources/data/sql_keywords.json`

#### `get_suggestions(prefix: str) -> List[str]`
根据前缀获取关键字建议

**参数:**
- `prefix`: 用户输入的前缀（大小写不敏感）

**返回:**
- 匹配的关键字列表

**示例:**
```python
provider = SQLKeywordProvider()
suggestions = provider.get_suggestions("SEL")
# 返回: ["SELECT"]
```

#### `get_keywords_by_category(category: str) -> List[str]`
获取特定类别的关键字

**参数:**
- `category`: 类别名称 (DML, DDL, CLAUSES, JOINS, OPERATORS, FUNCTIONS, DATA_TYPES)

**返回:**
- 该类别下的关键字列表

---

## LocalMetadataCache

### 类定义

```python
class LocalMetadataCache:
    """本地元数据缓存管理器"""
```

### 方法

#### `__init__(db_path: str = 'data/metadata_cache.db')`
初始化元数据缓存

**参数:**
- `db_path`: SQLite 数据库文件路径

#### `update_metadata(connection_id: str, tables_data: List[Dict])`
更新连接的元数据

**参数:**
- `connection_id`: 连接标识符
- `tables_data`: 表元数据列表

#### `search_tables(connection_id: str, prefix: str, limit: int = 20) -> List[Tuple]`
搜索表名

**参数:**
- `connection_id`: 连接标识符
- `prefix`: 表名前缀
- `limit`: 返回结果数量限制

**返回:**
- 元组列表: (schema_name, table_name, table_type, comment)

#### `get_columns(connection_id: str, table_name: str, schema_name: str = '') -> List[Tuple]`
获取表的列信息

**参数:**
- `connection_id`: 连接标识符
- `table_name`: 表名
- `schema_name`: 模式名（可选）

**返回:**
- 元组列表: (column_name, data_type, is_nullable, column_default, comment)

---

## SQLCompleter

### 类定义

```python
class SQLCompleter(QCompleter):
    """SQL 智能补全器"""
```

### 方法

#### `__init__(parent: QTextEdit, connection_id: str = 'default')`
初始化 SQL 补全器

**参数:**
- `parent`: 父文本编辑器
- `connection_id`: 数据库连接标识符

#### `refresh_suggestions(force: bool = False)`
刷新补全建议

**参数:**
- `force`: 是否强制刷新（忽略最小触发长度）

#### `update_connection(connection_id: str)`
更新连接标识符

**参数:**
- `connection_id`: 新的连接标识符

---

## MetadataSyncService

### 类定义

```python
class MetadataSyncService:
    """元数据同步服务"""
```

### 方法

#### `__init__(db_repository: DatabaseRepository, metadata_cache: LocalMetadataCache)`
初始化同步服务

**参数:**
- `db_repository`: 数据库仓库
- `metadata_cache`: 元数据缓存

#### `sync_metadata(connection_id: str, force_full: bool = False) -> bool`
同步元数据

**参数:**
- `connection_id`: 连接标识符
- `force_full`: 是否强制全量更新

**返回:**
- 同步是否成功

#### `should_sync(connection_id: str, interval_minutes: int = 30) -> bool`
检查是否需要同步

**参数:**
- `connection_id`: 连接标识符
- `interval_minutes`: 同步间隔（分钟）

**返回:**
- 是否需要同步
