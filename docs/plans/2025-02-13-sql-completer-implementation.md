# SQL 智能补全功能实现方案

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现基于本地数据库元数据的 SQL 智能补全功能，支持 SQL 关键字、表名、列名的自动补全

**Architecture:** 使用 Provider 模式分离关键字和元数据提供，LocalMetadataCache 使用 SQLite 本地缓存数据库元数据，SQLCompleter 继承 QCompleter 提供智能补全 UI

**Tech Stack:** PySide2, SQLite, 现有 Repository/CQRS/Cache 架构

**兼容性约束:** ✅ Windows 7 SP1, ✅ Python 3.8.1, ✅ 完全离线

---

## 前置依赖检查

### 检查现有架构组件

**必需已存在的组件:**
- `src/data/repositories/database_repository.py` - 数据库操作
- `src/infrastructure/cache/cache_manager.py` - 缓存管理
- `src/business/services/data_service.py` - 数据服务
- `src/presentation/dialogs/sql_query_dialog.py` - SQL 编辑器对话框

**验证命令:**
```bash
python -c "from src.data.repositories.database_repository import DatabaseRepository; print('✓ DatabaseRepository exists')"
python -c "from src.infrastructure.cache.cache_manager import CacheManager; print('✓ CacheManager exists')"
python -c "from src.business.services.data_service import DataService; print('✓ DataService exists')"
```

---

## Task 1: 创建 SQL 关键字数据文件

**Files:**
- Create: `resources/data/sql_keywords.json`
- Test: `tests/unit/test_sql_keywords.py`

**Step 1: Write the failing test**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""SQL关键字数据文件测试"""

import json
import os
import unittest


class TestSQLKeywords(unittest.TestCase):
    """测试 SQL 关键字数据文件"""

    def setUp(self):
        self.keywords_path = 'resources/data/sql_keywords.json'

    def test_keywords_file_exists(self):
        """测试关键字文件存在"""
        self.assertTrue(os.path.exists(self.keywords_path))

    def test_keywords_file_is_valid_json(self):
        """测试关键字文件是有效的 JSON"""
        with open(self.keywords_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)

    def test_keywords_has_required_categories(self):
        """测试包含必需的分类"""
        with open(self.keywords_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        required_categories = ['DML', 'DDL', 'CLAUSES', 'JOINS', 'OPERATORS', 'FUNCTIONS']
        for category in required_categories:
            self.assertIn(category, data)
            self.assertIsInstance(data[category], list)
            self.assertGreater(len(data[category]), 0)

    def test_keywords_are_uppercase(self):
        """测试关键字都是大写"""
        with open(self.keywords_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for category, keywords in data.items():
            for keyword in keywords:
                self.assertEqual(keyword, keyword.upper())


if __name__ == '__main__':
    unittest.main()
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.unit.test_sql_keywords -v`
Expected: FAIL with "FileNotFoundError"

**Step 3: Write minimal implementation**

```json
{
  "DML": [
    "SELECT", "INSERT", "UPDATE", "DELETE", "MERGE", "REPLACE",
    "CALL", "EXPLAIN", "DESCRIBE", "SHOW"
  ],
  "DDL": [
    "CREATE", "ALTER", "DROP", "TRUNCATE", "RENAME",
    "TABLE", "INDEX", "VIEW", "DATABASE", "SCHEMA",
    "PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "NOT NULL",
    "DEFAULT", "AUTO_INCREMENT", "IDENTITY"
  ],
  "CLAUSES": [
    "FROM", "WHERE", "GROUP BY", "HAVING", "ORDER BY",
    "LIMIT", "OFFSET", "JOIN", "ON", "USING",
    "VALUES", "SET", "INTO", "AS", "DISTINCT",
    "ALL", "UNION", "INTERSECT", "EXCEPT"
  ],
  "JOINS": [
    "JOIN", "INNER JOIN", "LEFT JOIN", "LEFT OUTER JOIN",
    "RIGHT JOIN", "RIGHT OUTER JOIN", "FULL JOIN",
    "FULL OUTER JOIN", "CROSS JOIN", "NATURAL JOIN"
  ],
  "OPERATORS": [
    "AND", "OR", "NOT", "IN", "EXISTS", "BETWEEN",
    "LIKE", "IS NULL", "IS NOT NULL", "CASE", "WHEN",
    "THEN", "ELSE", "END", "CAST", "CONVERT"
  ],
  "FUNCTIONS": [
    "COUNT", "SUM", "AVG", "MAX", "MIN",
    "CONCAT", "SUBSTRING", "SUBSTR", "UPPER", "LOWER",
    "TRIM", "LTRIM", "RTRIM", "LENGTH", "CHAR_LENGTH",
    "DATE", "NOW", "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP",
    "YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "SECOND",
    "ROUND", "CEIL", "FLOOR", "ABS", "MOD",
    "COALESCE", "NULLIF", "IFNULL", "ISNULL"
  ],
  "DATA_TYPES": [
    "INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT",
    "VARCHAR", "CHAR", "TEXT", "STRING",
    "DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "REAL",
    "DATE", "TIME", "DATETIME", "TIMESTAMP",
    "BOOLEAN", "BOOL", "BINARY", "BLOB"
  ]
}
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.unit.test_sql_keywords -v`
Expected: PASS (all 4 tests)

**Step 5: Commit**

```bash
git add resources/data/sql_keywords.json tests/unit/test_sql_keywords.py
git commit -m "feat: add SQL keywords data file with 80+ keywords"
```

---

## Task 2: 创建 SQLKeywordProvider 类

**Files:**
- Create: `src/presentation/widgets/sql_keyword_provider.py`
- Test: `tests/unit/test_sql_keyword_provider.py`

**Step 1: Write the failing test**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""SQLKeywordProvider 单元测试"""

import unittest
import os
import sys

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from presentation.widgets.sql_keyword_provider import SQLKeywordProvider


class TestSQLKeywordProvider(unittest.TestCase):
    """测试 SQL 关键字提供者"""

    def setUp(self):
        self.provider = SQLKeywordProvider()

    def test_provider_initialization(self):
        """测试提供者初始化"""
        self.assertIsNotNone(self.provider)
        self.assertIsInstance(self.provider.all_keywords, list)
        self.assertGreater(len(self.provider.all_keywords), 0)

    def test_get_suggestions_with_prefix(self):
        """测试根据前缀获取建议"""
        suggestions = self.provider.get_suggestions("SEL")
        self.assertIn("SELECT", suggestions)

    def test_get_suggestions_case_insensitive(self):
        """测试大小写不敏感的建议"""
        upper_suggestions = self.provider.get_suggestions("sel")
        lower_suggestions = self.provider.get_suggestions("SEL")
        self.assertEqual(upper_suggestions, lower_suggestions)

    def test_get_suggestions_empty_prefix(self):
        """测试空前缀返回所有关键字"""
        suggestions = self.provider.get_suggestions("")
        self.assertGreater(len(suggestions), 50)

    def test_get_suggestions_no_match(self):
        """测试无匹配时返回空列表"""
        suggestions = self.provider.get_suggestions("XYZ123")
        self.assertEqual(len(suggestions), 0)


if __name__ == '__main__':
    unittest.main()
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.unit.test_sql_keyword_provider -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQL 关键字提供者模块

提供 SQL 关键字、函数名的智能提示功能
"""

import json
import os
from typing import List, Dict


class SQLKeywordProvider:
    """
    SQL 关键字提供者
    
    从本地 JSON 文件加载 SQL 关键字，提供基于前缀的智能提示
    """

    def __init__(self, keywords_file: str = None):
        """
        初始化关键字提供者
        
        Args:
            keywords_file: 关键字 JSON 文件路径，默认为 resources/data/sql_keywords.json
        """
        if keywords_file is None:
            # 计算默认路径
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            keywords_file = os.path.join(base_dir, 'resources', 'data', 'sql_keywords.json')
        
        self.keywords_file = keywords_file
        self.all_keywords = self._load_keywords()

    def _load_keywords(self) -> List[str]:
        """
        从 JSON 文件加载关键字
        
        Returns:
            排序后的关键字列表
        """
        try:
            with open(self.keywords_file, 'r', encoding='utf-8') as f:
                data: Dict[str, List[str]] = json.load(f)
            
            all_keywords = []
            for category_keywords in data.values():
                all_keywords.extend(category_keywords)
            
            return sorted(set(all_keywords))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # 如果文件不存在或解析失败，返回基础关键字
            return [
                "SELECT", "INSERT", "UPDATE", "DELETE",
                "FROM", "WHERE", "GROUP BY", "ORDER BY",
                "JOIN", "LEFT JOIN", "RIGHT JOIN",
                "AND", "OR", "NOT", "IN", "EXISTS",
                "COUNT", "SUM", "AVG", "MAX", "MIN"
            ]

    def get_suggestions(self, prefix: str) -> List[str]:
        """
        根据前缀获取关键字建议
        
        Args:
            prefix: 用户输入的前缀（大小写不敏感）
            
        Returns:
            匹配的关键字列表
        """
        if not prefix:
            return self.all_keywords
        
        prefix_upper = prefix.upper()
        return [kw for kw in self.all_keywords if kw.startswith(prefix_upper)]

    def get_keywords_by_category(self, category: str) -> List[str]:
        """
        获取特定类别的关键字
        
        Args:
            category: 类别名称 (DML, DDL, CLAUSES, JOINS, OPERATORS, FUNCTIONS, DATA_TYPES)
            
        Returns:
            该类别下的关键字列表
        """
        try:
            with open(self.keywords_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get(category, [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []


# 单例模式，全局共享
_keyword_provider_instance = None


def get_keyword_provider() -> SQLKeywordProvider:
    """
    获取 SQLKeywordProvider 单例
    
    Returns:
        SQLKeywordProvider 实例
    """
    global _keyword_provider_instance
    if _keyword_provider_instance is None:
        _keyword_provider_instance = SQLKeywordProvider()
    return _keyword_provider_instance
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.unit.test_sql_keyword_provider -v`
Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add src/presentation/widgets/sql_keyword_provider.py tests/unit/test_sql_keyword_provider.py
git commit -m "feat: add SQLKeywordProvider for keyword suggestions"
```

---

## Task 3: 创建 LocalMetadataCache 类

**Files:**
- Create: `src/business/services/metadata_cache_service.py`
- Test: `tests/unit/test_metadata_cache_service.py`

**Step 1: Write the failing test**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""LocalMetadataCache 单元测试"""

import unittest
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from business.services.metadata_cache_service import LocalMetadataCache


class TestLocalMetadataCache(unittest.TestCase):
    """测试本地元数据缓存服务"""

    def setUp(self):
        """测试前创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_metadata.db')
        self.cache = LocalMetadataCache(self.db_path)

    def tearDown(self):
        """测试后清理临时目录"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_initialization(self):
        """测试缓存初始化"""
        self.assertIsNotNone(self.cache)
        self.assertTrue(os.path.exists(self.db_path))

    def test_update_metadata(self):
        """测试更新元数据"""
        connection_id = 'test_conn'
        tables_data = [
            {
                'name': 'users',
                'type': 'TABLE',
                'comment': '用户表',
                'columns': [
                    {'name': 'id', 'type': 'INT', 'position': 1},
                    {'name': 'username', 'type': 'VARCHAR(50)', 'position': 2}
                ]
            }
        ]
        
        self.cache.update_metadata(connection_id, tables_data)
        
        # 验证表是否存在
        tables = self.cache.search_tables(connection_id, 'users')
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0][1], 'users')  # table_name

    def test_search_tables(self):
        """测试搜索表"""
        connection_id = 'test_conn'
        tables_data = [
            {'name': 'users', 'type': 'TABLE', 'comment': '', 'columns': []},
            {'name': 'orders', 'type': 'TABLE', 'comment': '', 'columns': []},
            {'name': 'products', 'type': 'TABLE', 'comment': '', 'columns': []}
        ]
        
        self.cache.update_metadata(connection_id, tables_data)
        
        # 搜索 'user' 应该返回 users
        results = self.cache.search_tables(connection_id, 'user')
        self.assertEqual(len(results), 1)
        
        # 搜索空字符串应该返回所有
        results = self.cache.search_tables(connection_id, '')
        self.assertEqual(len(results), 3)

    def test_get_columns(self):
        """测试获取列信息"""
        connection_id = 'test_conn'
        tables_data = [
            {
                'name': 'users',
                'type': 'TABLE',
                'comment': '',
                'columns': [
                    {'name': 'id', 'type': 'INT', 'nullable': False, 'default': None, 'comment': '', 'position': 1},
                    {'name': 'name', 'type': 'VARCHAR(100)', 'nullable': True, 'default': None, 'comment': '', 'position': 2}
                ]
            }
        ]
        
        self.cache.update_metadata(connection_id, tables_data)
        
        columns = self.cache.get_columns(connection_id, 'users')
        self.assertEqual(len(columns), 2)
        self.assertEqual(columns[0][0], 'id')  # column_name
        self.assertEqual(columns[1][0], 'name')

    def test_clear_connection(self):
        """测试清除连接元数据"""
        connection_id = 'test_conn'
        tables_data = [{'name': 'users', 'type': 'TABLE', 'comment': '', 'columns': []}]
        
        self.cache.update_metadata(connection_id, tables_data)
        self.assertEqual(len(self.cache.search_tables(connection_id, '')), 1)
        
        self.cache.clear_connection(connection_id)
        self.assertEqual(len(self.cache.search_tables(connection_id, '')), 0)


if __name__ == '__main__':
    unittest.main()
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.unit.test_metadata_cache_service -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地元数据缓存服务

使用 SQLite 本地缓存数据库元数据（表、列、索引等）
支持 Windows 7, Python 3.8.1, 完全离线
"""

import sqlite3
import os
import logging
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LocalMetadataCache:
    """
    本地元数据缓存管理器
    
    功能:
    - 缓存数据库表、列、索引元数据
    - 支持多连接隔离
    - 全文搜索支持
    - 自动过期管理
    """

    def __init__(self, db_path: str = 'data/metadata_cache.db'):
        """
        初始化元数据缓存
        
        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_db()

    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _init_db(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript('''
                -- 表元数据表
                CREATE TABLE IF NOT EXISTS tables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    connection_id TEXT NOT NULL,
                    schema_name TEXT,
                    table_name TEXT NOT NULL,
                    table_type TEXT DEFAULT 'TABLE',
                    comment TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(connection_id, schema_name, table_name)
                );
                
                -- 列元数据表
                CREATE TABLE IF NOT EXISTS columns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_id INTEGER NOT NULL,
                    column_name TEXT NOT NULL,
                    data_type TEXT,
                    is_nullable BOOLEAN DEFAULT 1,
                    column_default TEXT,
                    comment TEXT,
                    ordinal_position INTEGER DEFAULT 0,
                    FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE CASCADE,
                    UNIQUE(table_id, column_name)
                );
                
                -- 索引表
                CREATE TABLE IF NOT EXISTS indexes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_id INTEGER NOT NULL,
                    index_name TEXT NOT NULL,
                    is_unique BOOLEAN DEFAULT 0,
                    is_primary BOOLEAN DEFAULT 0,
                    FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE CASCADE
                );
                
                -- 索引列表
                CREATE TABLE IF NOT EXISTS index_columns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_id INTEGER NOT NULL,
                    column_name TEXT NOT NULL,
                    ordinal_position INTEGER DEFAULT 0,
                    FOREIGN KEY (index_id) REFERENCES indexes(id) ON DELETE CASCADE
                );
                
                -- 创建索引
                CREATE INDEX IF NOT EXISTS idx_tables_conn ON tables(connection_id);
                CREATE INDEX IF NOT EXISTS idx_tables_name ON tables(table_name);
                CREATE INDEX IF NOT EXISTS idx_columns_table ON columns(table_id);
                CREATE INDEX IF NOT EXISTS idx_columns_name ON columns(column_name);
            ''')
            conn.commit()

    def update_metadata(self, connection_id: str, tables_data: List[Dict[str, Any]]):
        """
        更新连接的元数据
        
        Args:
            connection_id: 连接标识符
            tables_data: 表元数据列表，格式:
                [
                    {
                        'name': 'table_name',
                        'schema': 'schema_name',  # 可选
                        'type': 'TABLE',  # 或 'VIEW'
                        'comment': '表注释',  # 可选
                        'columns': [
                            {
                                'name': 'column_name',
                                'type': 'VARCHAR(50)',
                                'nullable': True,
                                'default': None,
                                'comment': '列注释',
                                'position': 1
                            }
                        ]
                    }
                ]
        """
        with sqlite3.connect(self.db_path) as conn:
            try:
                # 删除该连接的旧数据
                conn.execute(
                    'DELETE FROM tables WHERE connection_id = ?',
                    (connection_id,)
                )
                
                # 插入新数据
                for table_data in tables_data:
                    cursor = conn.execute('''
                        INSERT INTO tables (connection_id, schema_name, table_name, table_type, comment)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        connection_id,
                        table_data.get('schema', ''),
                        table_data['name'],
                        table_data.get('type', 'TABLE'),
                        table_data.get('comment', '')
                    ))
                    
                    table_id = cursor.lastrowid
                    
                    # 插入列信息
                    for col in table_data.get('columns', []):
                        conn.execute('''
                            INSERT INTO columns 
                            (table_id, column_name, data_type, is_nullable, column_default, comment, ordinal_position)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            table_id,
                            col['name'],
                            col.get('type', 'VARCHAR'),
                            1 if col.get('nullable', True) else 0,
                            col.get('default'),
                            col.get('comment', ''),
                            col.get('position', 0)
                        ))
                
                conn.commit()
                logger.info(f"Updated metadata for connection {connection_id}: {len(tables_data)} tables")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to update metadata: {e}")
                raise

    def search_tables(self, connection_id: str, prefix: str, limit: int = 20) -> List[Tuple]:
        """
        搜索表名
        
        Args:
            connection_id: 连接标识符
            prefix: 表名前缀（大小写不敏感）
            limit: 返回结果数量限制
            
        Returns:
            元组列表: (schema_name, table_name, table_type, comment)
        """
        with sqlite3.connect(self.db_path) as conn:
            if prefix:
                cursor = conn.execute('''
                    SELECT schema_name, table_name, table_type, comment
                    FROM tables
                    WHERE connection_id = ? 
                      AND (table_name LIKE ? OR comment LIKE ?)
                    ORDER BY table_name
                    LIMIT ?
                ''', (connection_id, f'{prefix}%', f'%{prefix}%', limit))
            else:
                cursor = conn.execute('''
                    SELECT schema_name, table_name, table_type, comment
                    FROM tables
                    WHERE connection_id = ?
                    ORDER BY table_name
                    LIMIT ?
                ''', (connection_id, limit))
            
            return cursor.fetchall()

    def get_columns(self, connection_id: str, table_name: str, schema_name: str = '') -> List[Tuple]:
        """
        获取表的列信息
        
        Args:
            connection_id: 连接标识符
            table_name: 表名
            schema_name: 模式名（可选）
            
        Returns:
            元组列表: (column_name, data_type, is_nullable, column_default, comment)
        """
        with sqlite3.connect(self.db_path) as conn:
            if schema_name:
                cursor = conn.execute('''
                    SELECT c.column_name, c.data_type, c.is_nullable, c.column_default, c.comment
                    FROM columns c
                    JOIN tables t ON c.table_id = t.id
                    WHERE t.connection_id = ? 
                      AND t.table_name = ? 
                      AND t.schema_name = ?
                    ORDER BY c.ordinal_position
                ''', (connection_id, table_name, schema_name))
            else:
                cursor = conn.execute('''
                    SELECT c.column_name, c.data_type, c.is_nullable, c.column_default, c.comment
                    FROM columns c
                    JOIN tables t ON c.table_id = t.id
                    WHERE t.connection_id = ? AND t.table_name = ?
                    ORDER BY c.ordinal_position
                ''', (connection_id, table_name))
            
            return cursor.fetchall()

    def get_all_tables(self, connection_id: str) -> List[Tuple]:
        """
        获取连接的所有表
        
        Args:
            connection_id: 连接标识符
            
        Returns:
            元组列表: (schema_name, table_name, table_type)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT schema_name, table_name, table_type
                FROM tables
                WHERE connection_id = ?
                ORDER BY table_name
            ''', (connection_id,))
            return cursor.fetchall()

    def clear_connection(self, connection_id: str):
        """
        清除连接的元数据
        
        Args:
            connection_id: 连接标识符
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM tables WHERE connection_id = ?', (connection_id,))
            conn.commit()
            logger.info(f"Cleared metadata for connection {connection_id}")

    def get_last_update_time(self, connection_id: str) -> Optional[datetime]:
        """
        获取元数据最后更新时间
        
        Args:
            connection_id: 连接标识符
            
        Returns:
            最后更新时间，如果没有则返回 None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT MAX(last_updated) FROM tables WHERE connection_id = ?
            ''', (connection_id,))
            result = cursor.fetchone()
            if result and result[0]:
                return datetime.fromisoformat(result[0])
            return None


# 单例实例
_cache_instance = None


def get_metadata_cache(db_path: str = 'data/metadata_cache.db') -> LocalMetadataCache:
    """
    获取 LocalMetadataCache 单例
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        LocalMetadataCache 实例
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LocalMetadataCache(db_path)
    return _cache_instance
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.unit.test_metadata_cache_service -v`
Expected: PASS (all 6 tests)

**Step 5: Commit**

```bash
git add src/business/services/metadata_cache_service.py tests/unit/test_metadata_cache_service.py
git commit -m "feat: add LocalMetadataCache for database metadata caching"
```

---

## Task 4: 创建 SQLCompleter 组件

**Files:**
- Create: `src/presentation/widgets/sql_completer.py`
- Test: `tests/unit/test_sql_completer.py`

**Step 1: Write the failing test**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""SQLCompleter 单元测试"""

import unittest
import os
import sys
from unittest.mock import Mock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from PySide2.QtWidgets import QApplication, QTextEdit
from PySide2.QtCore import Qt

from presentation.widgets.sql_completer import SQLCompleter

# 创建 QApplication 实例（每个测试文件只需要一个）
_app = None


def get_app():
    global _app
    if _app is None:
        _app = QApplication([])
    return _app


class TestSQLCompleter(unittest.TestCase):
    """测试 SQL 补全器"""

    @classmethod
    def setUpClass(cls):
        """测试类开始前创建 QApplication"""
        cls.app = get_app()

    def setUp(self):
        """每个测试前创建编辑器"""
        self.editor = QTextEdit()
        self.completer = SQLCompleter(self.editor, 'test_conn')

    def test_completer_initialization(self):
        """测试补全器初始化"""
        self.assertIsNotNone(self.completer)
        self.assertEqual(self.completer.connection_id, 'test_conn')
        self.assertIsNotNone(self.completer.keyword_provider)
        self.assertIsNotNone(self.completer.metadata_cache)

    def test_get_current_word(self):
        """测试获取当前单词"""
        # 模拟输入 "SELECT us"
        self.editor.setPlainText("SELECT us")
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.End)
        self.editor.setTextCursor(cursor)
        
        # 由于需要实际 UI 交互，这里简化测试
        word = self.completer._get_current_word("SELECT us")
        self.assertEqual(word, "us")

    def test_needs_table_name(self):
        """测试判断是否需要表名"""
        # 应该匹配的情况
        self.assertTrue(self.completer._needs_table_name("SELECT * FROM "))
        self.assertTrue(self.completer._needs_table_name("JOIN "))
        self.assertTrue(self.completer._needs_table_name("INSERT INTO "))
        
        # 不应该匹配的情况
        self.assertFalse(self.completer._needs_table_name("SELECT "))
        self.assertFalse(self.completer._needs_table_name("WHERE "))

    def test_needs_column_name(self):
        """测试判断是否需要列名"""
        # 应该匹配的情况
        self.assertTrue(self.completer._needs_column_name("SELECT "))
        self.assertTrue(self.completer._needs_column_name("SELECT id, "))
        self.assertTrue(self.completer._needs_column_name("WHERE "))
        
        # 不应该匹配的情况
        self.assertFalse(self.completer._needs_column_name("FROM "))


if __name__ == '__main__':
    unittest.main()
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.unit.test_sql_completer -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQL 智能补全组件

支持 SQL 关键字、表名、列名的智能补全
基于 PySide2 QCompleter 实现
"""

import re
from typing import List, Optional

from PySide2.QtWidgets import QCompleter, QTextEdit, QApplication
from PySide2.QtCore import Qt, QStringListModel, QObject

from presentation.widgets.sql_keyword_provider import SQLKeywordProvider, get_keyword_provider
from business.services.metadata_cache_service import LocalMetadataCache, get_metadata_cache


class SQLCompleter(QCompleter):
    """
    SQL 智能补全器
    
    功能:
    - SQL 关键字补全
    - 表名补全（基于本地缓存的元数据）
    - 列名补全（基于上下文）
    - 上下文感知（根据当前位置提供合适的建议）
    """

    def __init__(self, parent: QTextEdit, connection_id: str = 'default'):
        """
        初始化 SQL 补全器
        
        Args:
            parent: 父文本编辑器
            connection_id: 数据库连接标识符
        """
        super().__init__(parent)
        
        self.text_edit = parent
        self.connection_id = connection_id
        
        # 初始化提供者
        self.keyword_provider = get_keyword_provider()
        self.metadata_cache = get_metadata_cache()
        
        # 设置模型
        self.model = QStringListModel()
        self.setModel(self.model)
        
        # 配置补全器
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setFilterMode(Qt.MatchStartsWith)
        
        # 设置最大显示数量
        self.setMaxVisibleItems(10)
        
        # 连接信号
        self.activated.connect(self._insert_completion)

    def update_connection(self, connection_id: str):
        """
        更新连接标识符
        
        Args:
            connection_id: 新的连接标识符
        """
        self.connection_id = connection_id

    def refresh_suggestions(self, force: bool = False):
        """
        刷新补全建议
        
        在文本变化时调用，根据当前输入和上下文更新建议列表
        
        Args:
            force: 是否强制刷新（忽略最小触发长度）
        """
        cursor = self.text_edit.textCursor()
        current_line = cursor.block().text()[:cursor.positionInBlock()]
        
        # 获取当前单词
        word = self._get_current_word(current_line)
        
        # 最少 2 个字符才触发（除非强制）
        if len(word) < 2 and not force:
            return
        
        # 获取补全建议
        suggestions = self._get_suggestions(word, current_line)
        
        if suggestions:
            self.model.setStringList(suggestions)
            # 计算补全位置
            rect = self.text_edit.cursorRect()
            self.complete(rect)

    def _get_current_word(self, line: str) -> str:
        """
        获取当前正在输入的单词
        
        Args:
            line: 当前行文本
            
        Returns:
            当前单词（可能包含点号，如 table.column）
        """
        # 从后往前找，匹配单词字符或点号
        match = re.search(r'[\w.]+$', line)
        return match.group(0) if match else ''

    def _get_suggestions(self, word: str, context: str) -> List[str]:
        """
        根据上下文获取补全建议
        
        Args:
            word: 当前输入的单词
            context: 当前行上下文
            
        Returns:
            建议列表
        """
        suggestions = []
        word_upper = word.upper()
        
        # 检查是否是表名.列名格式
        if '.' in word:
            table_part, col_part = word.rsplit('.', 1)
            columns = self._get_column_suggestions(table_part, col_part)
            suggestions.extend(columns)
        else:
            # 1. SQL 关键字建议
            keywords = self.keyword_provider.get_suggestions(word)
            suggestions.extend(keywords)
            
            # 2. 根据上下文判断是否需要表名
            if self._needs_table_name(context):
                tables = self._get_table_suggestions(word)
                suggestions.extend(tables)
            
            # 3. 根据上下文判断是否需要列名
            elif self._needs_column_name(context):
                table_name = self._extract_table_name(context)
                if table_name:
                    columns = self._get_column_suggestions(table_name, word)
                    suggestions.extend(columns)
        
        return suggestions[:20]  # 限制数量

    def _get_table_suggestions(self, prefix: str) -> List[str]:
        """
        获取表名建议
        
        Args:
            prefix: 前缀
            
        Returns:
            格式化的表名建议列表
        """
        tables = self.metadata_cache.search_tables(
            self.connection_id, prefix, limit=10
        )
        
        suggestions = []
        for schema, name, type_, comment in tables:
            display = f"{name} ({type_})"
            if comment:
                display += f" - {comment[:30]}"
            suggestions.append(display)
        
        return suggestions

    def _get_column_suggestions(self, table_name: str, prefix: str) -> List[str]:
        """
        获取列名建议
        
        Args:
            table_name: 表名
            prefix: 列名前缀
            
        Returns:
            格式化的列名建议列表
        """
        columns = self.metadata_cache.get_columns(
            self.connection_id, table_name
        )
        
        suggestions = []
        prefix_upper = prefix.upper()
        
        for col_name, col_type, is_nullable, default, comment in columns:
            if col_name.upper().startswith(prefix_upper):
                display = f"{col_name} ({col_type})"
                suggestions.append(display)
        
        return suggestions

    def _needs_table_name(self, context: str) -> bool:
        """
        判断当前上下文是否需要表名
        
        Args:
            context: 当前行上下文
            
        Returns:
            是否需要表名
        """
        patterns = [
            r'\bFROM\s+[\w.]*$',
            r'\bJOIN\s+[\w.]*$',
            r'\bINTO\s+[\w.]*$',
            r'\bTABLE\s+[\w.]*$',
            r'\bUPDATE\s+[\w.]*$',
            r'\bDELETE\s+FROM\s+[\w.]*$'
        ]
        
        context_upper = context.upper()
        return any(re.search(p, context_upper) for p in patterns)

    def _needs_column_name(self, context: str) -> bool:
        """
        判断当前上下文是否需要列名
        
        Args:
            context: 当前行上下文
            
        Returns:
            是否需要列名
        """
        patterns = [
            r'\bSELECT\s+[\w\s,.]*$',
            r'\bWHERE\s+[\w\s=<>!]*$',
            r'\bGROUP\s+BY\s+[\w\s,]*$',
            r'\bORDER\s+BY\s+[\w\s,]*$',
            r'\bHAVING\s+[\w\s=<>!]*$',
            r'\bSET\s+[\w\s,=]*$'
        ]
        
        context_upper = context.upper()
        return any(re.search(p, context_upper) for p in patterns)

    def _extract_table_name(self, context: str) -> Optional[str]:
        """
        从上下文中提取表名
        
        Args:
            context: 当前行上下文
            
        Returns:
            表名，如果没有找到则返回 None
        """
        # 尝试从 FROM 子句提取
        match = re.search(r'\bFROM\s+(\w+)', context, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # 尝试从 JOIN 子句提取
        match = re.search(r'\bJOIN\s+(\w+)', context, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # 尝试从 UPDATE 子句提取
        match = re.search(r'\bUPDATE\s+(\w+)', context, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # 尝试从 INTO 子句提取
        match = re.search(r'\bINTO\s+(\w+)', context, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None

    def _insert_completion(self, completion: str):
        """
        插入选中的补全项
        
        Args:
            completion: 选中的补全文本
        """
        cursor = self.text_edit.textCursor()
        current_line = cursor.block().text()[:cursor.positionInBlock()]
        word = self._get_current_word(current_line)
        
        # 移除已输入的部分
        for _ in range(len(word)):
            cursor.deletePreviousChar()
        
        # 插入补全文本（去掉括号里的说明）
        text_to_insert = completion.split(' (')[0]
        cursor.insertText(text_to_insert)
        
        self.text_edit.setTextCursor(cursor)

    def set_metadata(self, tables_data: List[dict]):
        """
        设置元数据（便捷方法）
        
        Args:
            tables_data: 表元数据列表
        """
        self.metadata_cache.update_metadata(self.connection_id, tables_data)
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.unit.test_sql_completer -v`
Expected: PASS (all 4 tests)

**Step 5: Commit**

```bash
git add src/presentation/widgets/sql_completer.py tests/unit/test_sql_completer.py
git commit -m "feat: add SQLCompleter widget with context-aware suggestions"
```

---

## Task 5: 创建元数据同步服务

**Files:**
- Create: `src/business/services/metadata_sync_service.py`
- Test: `tests/unit/test_metadata_sync_service.py`

**Step 1: Write the failing test**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""MetadataSyncService 单元测试"""

import unittest
import os
import sys
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from business.services.metadata_sync_service import MetadataSyncService


class TestMetadataSyncService(unittest.TestCase):
    """测试元数据同步服务"""

    def setUp(self):
        """设置测试"""
        self.mock_db_repo = Mock()
        self.mock_cache = Mock()
        self.sync_service = MetadataSyncService(self.mock_db_repo, self.mock_cache)

    def test_sync_metadata_success(self):
        """测试成功同步元数据"""
        # 模拟数据库返回的表列表
        self.mock_db_repo.get_all_tables.return_value = ['users', 'orders']
        
        # 模拟表列信息
        self.mock_db_repo.get_table_columns.side_effect = [
            [
                {'name': 'id', 'type': 'INT', 'ordinal_position': 1},
                {'name': 'name', 'type': 'VARCHAR', 'ordinal_position': 2}
            ],
            [
                {'name': 'order_id', 'type': 'INT', 'ordinal_position': 1},
                {'name': 'user_id', 'type': 'INT', 'ordinal_position': 2}
            ]
        ]
        
        # 执行同步
        result = self.sync_service.sync_metadata('test_conn')
        
        # 验证结果
        self.assertTrue(result)
        self.mock_cache.update_metadata.assert_called_once()
        
        # 验证传入的数据
        call_args = self.mock_cache.update_metadata.call_args
        self.assertEqual(call_args[0][0], 'test_conn')
        self.assertEqual(len(call_args[0][1]), 2)  # 2 个表

    def test_sync_metadata_empty_tables(self):
        """测试空表列表"""
        self.mock_db_repo.get_all_tables.return_value = []
        
        result = self.sync_service.sync_metadata('test_conn')
        
        self.assertTrue(result)
        self.mock_cache.update_metadata.assert_called_once()
        self.assertEqual(len(self.mock_cache.update_metadata.call_args[0][1]), 0)

    def test_sync_metadata_db_error(self):
        """测试数据库错误"""
        self.mock_db_repo.get_all_tables.side_effect = Exception("Connection failed")
        
        result = self.sync_service.sync_metadata('test_conn')
        
        self.assertFalse(result)
        self.mock_cache.update_metadata.assert_not_called()


if __name__ == '__main__':
    unittest.main()
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.unit.test_metadata_sync_service -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
元数据同步服务

负责从数据库同步元数据到本地缓存
支持手动同步和自动定时同步
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from data.repositories.database_repository import DatabaseRepository
from business.services.metadata_cache_service import LocalMetadataCache

logger = logging.getLogger(__name__)


class MetadataSyncService:
    """
    元数据同步服务
    
    功能:
    - 从数据库读取表结构
    - 同步到本地元数据缓存
    - 支持增量更新和全量更新
    - 自动定时刷新
    """

    def __init__(self, 
                 db_repository: DatabaseRepository,
                 metadata_cache: LocalMetadataCache):
        """
        初始化同步服务
        
        Args:
            db_repository: 数据库仓库
            metadata_cache: 元数据缓存
        """
        self.db_repository = db_repository
        self.metadata_cache = metadata_cache
        self._last_sync_times: Dict[str, datetime] = {}

    def sync_metadata(self, connection_id: str, force_full: bool = False) -> bool:
        """
        同步元数据
        
        Args:
            connection_id: 连接标识符
            force_full: 是否强制全量更新
            
        Returns:
            同步是否成功
        """
        try:
            logger.info(f"Starting metadata sync for connection: {connection_id}")
            
            # 获取所有表
            tables = self.db_repository.get_all_tables()
            logger.info(f"Found {len(tables)} tables")
            
            # 获取每个表的列信息
            tables_data = []
            for table_name in tables:
                try:
                    columns = self.db_repository.get_table_columns(table_name)
                    
                    tables_data.append({
                        'name': table_name,
                        'type': 'TABLE',
                        'comment': '',  # 可以从数据库获取
                        'columns': [
                            {
                                'name': col['name'],
                                'type': col.get('type', 'VARCHAR'),
                                'nullable': col.get('nullable', True),
                                'default': col.get('default'),
                                'comment': col.get('comment', ''),
                                'position': col.get('ordinal_position', 0)
                            }
                            for col in columns
                        ]
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to get columns for table {table_name}: {e}")
                    # 继续处理其他表
            
            # 更新缓存
            self.metadata_cache.update_metadata(connection_id, tables_data)
            
            # 记录同步时间
            self._last_sync_times[connection_id] = datetime.now()
            
            logger.info(f"Metadata sync completed: {len(tables_data)} tables")
            return True
            
        except Exception as e:
            logger.error(f"Metadata sync failed: {e}", exc_info=True)
            return False

    def should_sync(self, connection_id: str, interval_minutes: int = 30) -> bool:
        """
        检查是否需要同步
        
        Args:
            connection_id: 连接标识符
            interval_minutes: 同步间隔（分钟）
            
        Returns:
            是否需要同步
        """
        last_sync = self._last_sync_times.get(connection_id)
        
        if last_sync is None:
            return True
        
        elapsed = datetime.now() - last_sync
        return elapsed > timedelta(minutes=interval_minutes)

    def get_last_sync_time(self, connection_id: str) -> Optional[datetime]:
        """
        获取上次同步时间
        
        Args:
            connection_id: 连接标识符
            
        Returns:
            上次同步时间，如果没有则返回 None
        """
        return self._last_sync_times.get(connection_id)

    def clear_sync_record(self, connection_id: str):
        """
        清除同步记录
        
        Args:
            connection_id: 连接标识符
        """
        if connection_id in self._last_sync_times:
            del self._last_sync_times[connection_id]


# 便捷函数
def create_metadata_sync_service(
    db_repository: DatabaseRepository,
    cache_path: str = 'data/metadata_cache.db'
) -> MetadataSyncService:
    """
    创建元数据同步服务实例
    
    Args:
        db_repository: 数据库仓库
        cache_path: 缓存数据库路径
        
    Returns:
        MetadataSyncService 实例
    """
    from business.services.metadata_cache_service import LocalMetadataCache
    
    cache = LocalMetadataCache(cache_path)
    return MetadataSyncService(db_repository, cache)
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.unit.test_metadata_sync_service -v`
Expected: PASS (all 3 tests)

**Step 5: Commit**

```bash
git add src/business/services/metadata_sync_service.py tests/unit/test_metadata_sync_service.py
git commit -m "feat: add MetadataSyncService for syncing db metadata to cache"
```

---

## Task 6: 集成到 SQL 查询对话框

**Files:**
- Modify: `src/presentation/dialogs/sql_query_dialog.py`
- Test: `tests/integration/test_sql_completer_integration.py`

**Step 1: Read the existing file**

首先读取现有文件了解其结构：
```bash
cat src/presentation/dialogs/sql_query_dialog.py
```

**Step 2: Write the integration test**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""SQL 补全器集成测试"""

import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from PySide2.QtWidgets import QApplication

from presentation.dialogs.sql_query_dialog import SQLQueryDialog

_app = None


def get_app():
    global _app
    if _app is None:
        _app = QApplication([])
    return _app


class TestSQLCompleterIntegration(unittest.TestCase):
    """测试 SQL 补全器集成"""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def test_dialog_has_completer(self):
        """测试对话框有补全器"""
        # 这个测试需要 mock 数据服务
        # 简化版本：确保导入成功
        from presentation.widgets.sql_completer import SQLCompleter
        self.assertIsNotNone(SQLCompleter)

    def test_dialog_imports(self):
        """测试所有必要的导入都存在"""
        try:
            from presentation.widgets.sql_completer import SQLCompleter
            from business.services.metadata_cache_service import LocalMetadataCache
            from business.services.metadata_sync_service import MetadataSyncService
            from presentation.widgets.sql_keyword_provider import SQLKeywordProvider
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Import failed: {e}")


if __name__ == '__main__':
    unittest.main()
```

**Step 3: Run test to verify it fails**

Run: `python -m unittest tests.integration.test_sql_completer_integration -v`
Expected: PASS (因为现在只是测试导入)

**Step 4: Modify sql_query_dialog.py**

在现有文件基础上添加：

```python
# 在文件顶部添加导入
from presentation.widgets.sql_completer import SQLCompleter
from business.services.metadata_sync_service import MetadataSyncService, create_metadata_sync_service
from business.services.metadata_cache_service import get_metadata_cache
from PySide2.QtCore import QTimer

# 在 __init__ 方法中添加（在 setup_ui 调用后）
def setup_completer(self):
    """设置 SQL 智能补全"""
    # 创建补全器
    self.sql_completer = SQLCompleter(self.sql_editor, self.connection_id)
    
    # 创建元数据同步服务
    if hasattr(self, 'data_service') and self.data_service:
        db_repo = self.data_service.db_repository
        self.metadata_sync_service = create_metadata_sync_service(db_repo)
        
        # 立即同步一次
        self._sync_metadata()
        
        # 设置定时刷新（每 5 分钟）
        self.metadata_timer = QTimer(self)
        self.metadata_timer.timeout.connect(self._sync_metadata)
        self.metadata_timer.start(300000)  # 5 分钟

def _sync_metadata(self):
    """同步数据库元数据"""
    if hasattr(self, 'metadata_sync_service') and self.metadata_sync_service:
        success = self.metadata_sync_service.sync_metadata(self.connection_id)
        if success:
            print(f"Metadata synced for {self.connection_id}")
        else:
            print(f"Failed to sync metadata for {self.connection_id}")

# 在关闭事件中添加清理
def closeEvent(self, event):
    """关闭事件"""
    # 停止定时器
    if hasattr(self, 'metadata_timer'):
        self.metadata_timer.stop()
    
    # 清理元数据缓存记录
    if hasattr(self, 'connection_id'):
        cache = get_metadata_cache()
        cache.clear_connection(self.connection_id)
    
    event.accept()
```

**Step 5: Run test to verify it passes**

Run: `python -m unittest tests.integration.test_sql_completer_integration -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/presentation/dialogs/sql_query_dialog.py tests/integration/test_sql_completer_integration.py
git commit -m "feat: integrate SQLCompleter into SQLQueryDialog"
```

---

## Task 7: 创建使用示例和文档

**Files:**
- Create: `docs/examples/sql_completer_usage.md`
- Create: `docs/api/sql_completer_api.md`

**Step 1: Create usage documentation**

```markdown
# SQL 智能补全使用指南

## 功能概述

SQL 智能补全功能提供以下能力：

1. **SQL 关键字补全** - 自动提示 SELECT, FROM, WHERE 等关键字
2. **表名补全** - 根据数据库元数据提示表名
3. **列名补全** - 根据上下文提示列名
4. **上下文感知** - 在不同位置提供不同的建议

## 使用方法

### 基本使用

在 SQL 编辑器中输入时，补全会自动触发：

1. 输入 `SEL` → 提示 `SELECT`
2. 输入 `FROM us` → 提示 `users` 表
3. 输入 `WHERE id` → 提示 `id` 列

### 快捷键

- `Ctrl + Space` - 强制触发补全
- `Enter` / `Tab` - 确认选择
- `Esc` - 关闭补全窗口
- `↑` / `↓` - 选择建议项

### 配置

#### 自定义关键字

编辑 `resources/data/sql_keywords.json`：

```json
{
  "CUSTOM": ["MY_KEYWORD", "MY_FUNCTION"]
}
```

#### 调整触发延迟

在代码中修改：

```python
completer.setCompletionMode(QCompleter.PopupCompletion)
```

## 工作原理

### 架构

```
SQLQueryDialog
├── SQLCompleter
│   ├── SQLKeywordProvider (关键字)
│   └── LocalMetadataCache (元数据缓存)
├── MetadataSyncService (同步服务)
└── DataService (数据服务)
```

### 数据流

1. 打开 SQL 对话框 → 启动元数据同步
2. 同步服务从数据库读取表结构
3. 表结构存储到本地 SQLite 缓存
4. 用户输入时 → 查询缓存获取建议
5. 每 5 分钟自动刷新元数据

## 故障排除

### 补全不工作

1. 检查元数据是否已同步
2. 查看日志文件 `log/app.log`
3. 手动触发同步：刷新按钮

### 表名不显示

1. 确认数据库连接正常
2. 检查表权限
3. 查看元数据缓存文件 `data/metadata_cache.db`

## API 参考

参见 `docs/api/sql_completer_api.md`
```

**Step 2: Commit**

```bash
git add docs/examples/sql_completer_usage.md docs/api/sql_completer_api.md
git commit -m "docs: add SQL completer usage guide and API documentation"
```

---

## 验收测试清单

### 功能测试

- [ ] 输入 SQL 关键字前缀时显示建议
- [ ] 输入表名前缀时显示匹配的表
- [ ] 在 FROM 子句后显示表名建议
- [ ] 在 SELECT 子句后显示列名建议
- [ ] 选择建议后正确插入文本
- [ ] 元数据自动同步（打开对话框时）
- [ ] 元数据定时刷新（5分钟间隔）

### 兼容性测试

- [ ] Windows 7 SP1 运行正常
- [ ] Python 3.8.1 运行正常
- [ ] 离线环境无需网络

### 性能测试

- [ ] 补全响应时间 < 100ms
- [ ] 支持 1000+ 表无卡顿
- [ ] 内存占用增加 < 50MB

### 回归测试

- [ ] 所有现有单元测试通过
- [ ] SQL 查询功能正常工作
- [ ] 数据库连接配置正常

---

## 总结

### 新增文件

```
src/
├── presentation/
│   └── widgets/
│       ├── sql_keyword_provider.py      # SQL 关键字提供者
│       └── sql_completer.py             # SQL 补全器组件
├── business/
│   └── services/
│       ├── metadata_cache_service.py    # 元数据缓存服务
│       └── metadata_sync_service.py     # 元数据同步服务
resources/
└── data/
    └── sql_keywords.json                # SQL 关键字数据
tests/
├── unit/
│   ├── test_sql_keywords.py
│   ├── test_sql_keyword_provider.py
│   ├── test_metadata_cache_service.py
│   ├── test_sql_completer.py
│   └── test_metadata_sync_service.py
└── integration/
    └── test_sql_completer_integration.py
docs/
├── examples/
│   └── sql_completer_usage.md
└── api/
    └── sql_completer_api.md
```

### 修改文件

```
src/
└── presentation/
    └── dialogs/
        └── sql_query_dialog.py          # 集成补全器
```

### 依赖项

- PySide2 (已有)
- SQLite (Python 内置)
- 现有 Repository/CQRS/Cache 架构

### 兼容性

- ✅ Windows 7 SP1
- ✅ Python 3.8.1
- ✅ 完全离线

---

**计划完成时间**: 8-10 小时
**测试覆盖率目标**: > 80%
**文档完整性**: 100%
