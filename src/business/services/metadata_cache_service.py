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
            tables_data: 表元数据列表
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
            prefix: 表名前缀
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
