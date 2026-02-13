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
