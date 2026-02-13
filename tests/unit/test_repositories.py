#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Repository模式单元测试

测试 BaseRepository、QueryHistoryRepository 和 TableMetadataRepository
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.repositories.base_repository import BaseRepository, QueryRepository
from src.data.repositories.query_history_repository import QueryHistoryRepository
from src.data.repositories.table_metadata_repository import TableMetadataRepository


class MockDBRepository:
    """模拟数据库仓库"""
    
    def __init__(self):
        self.query_results = []
        self.non_query_result = True
        self.scalar_result = None
    
    def execute_query(self, query, params=None):
        return self.query_results
    
    def execute_non_query(self, query, params=None):
        return self.non_query_result
    
    def execute_scalar(self, query, params=None):
        return self.scalar_result


class TestQueryRepository(unittest.TestCase):
    """QueryRepository 测试类"""
    
    def setUp(self):
        """测试准备"""
        self.mock_db = MockDBRepository()
        self.repo = QueryRepository(self.mock_db)
    
    def test_query_execution(self):
        """测试查询执行"""
        # 设置模拟结果
        self.mock_db.query_results = [
            {'id': 1, 'name': 'test'},
            {'id': 2, 'name': 'test2'}
        ]
        
        # 执行查询
        result = self.repo.query("SELECT * FROM test", [])
        
        # 验证结果
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'test')
    
    def test_update_execution(self):
        """测试更新执行"""
        self.mock_db.non_query_result = True
        
        result = self.repo.update("UPDATE test SET name = %s", ['new_name'])
        
        self.assertTrue(result)
    
    def test_unsupported_operations(self):
        """测试不支持的操作"""
        with self.assertRaises(NotImplementedError):
            self.repo.find_by_id(1)
        
        with self.assertRaises(NotImplementedError):
            self.repo.save({})
        
        with self.assertRaises(NotImplementedError):
            self.repo.delete(1)


class TestQueryHistoryRepository(unittest.TestCase):
    """QueryHistoryRepository 测试类"""
    
    def setUp(self):
        """测试准备"""
        self.mock_db = MockDBRepository()
        self.repo = QueryHistoryRepository(self.mock_db)
    
    def test_find_by_id_found(self):
        """测试根据ID查找 - 找到记录"""
        self.mock_db.query_results = [
            {'id': 1, 'query_text': 'SELECT * FROM users', 'status': 'success'}
        ]
        
        result = self.repo.find_by_id(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['query_text'], 'SELECT * FROM users')
    
    def test_find_by_id_not_found(self):
        """测试根据ID查找 - 未找到记录"""
        self.mock_db.query_results = []
        
        result = self.repo.find_by_id(999)
        
        self.assertIsNone(result)
    
    def test_find_all(self):
        """测试查找所有记录"""
        self.mock_db.query_results = [
            {'id': 1, 'query_text': 'SELECT 1'},
            {'id': 2, 'query_text': 'SELECT 2'}
        ]
        
        result = self.repo.find_all(limit=10, offset=0)
        
        self.assertEqual(len(result), 2)
    
    def test_find_by_status(self):
        """测试根据状态查找"""
        self.mock_db.query_results = [
            {'id': 1, 'status': 'success'},
            {'id': 2, 'status': 'success'}
        ]
        
        result = self.repo.find_by_status('success', limit=10)
        
        self.assertEqual(len(result), 2)
    
    def test_search(self):
        """测试搜索功能"""
        self.mock_db.query_results = [
            {'id': 1, 'query_text': 'SELECT * FROM users'},
            {'id': 2, 'query_text': 'SELECT * FROM orders'}
        ]
        
        result = self.repo.search('SELECT', limit=10)
        
        self.assertEqual(len(result), 2)
    
    def test_save_insert(self):
        """测试保存新记录"""
        self.mock_db.non_query_result = True
        
        entity = {
            'query_text': 'SELECT 1',
            'status': 'success',
            'execution_time': 0.5,
            'row_count': 1
        }
        
        result = self.repo.save(entity)
        
        self.assertTrue(result)
    
    def test_delete(self):
        """测试删除记录"""
        self.mock_db.non_query_result = True
        
        result = self.repo.delete(1)
        
        self.assertTrue(result)
    
    def test_count(self):
        """测试统计记录数"""
        self.mock_db.scalar_result = 100
        
        result = self.repo.count()
        
        self.assertEqual(result, 100)
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        self.mock_db.scalar_result = 100
        
        result = self.repo.get_statistics()
        
        self.assertIn('total', result)
        self.assertIn('success', result)
        self.assertIn('failed', result)
        self.assertIn('success_rate', result)


class TestTableMetadataRepository(unittest.TestCase):
    """TableMetadataRepository 测试类"""
    
    def setUp(self):
        """测试准备"""
        self.mock_db = MockDBRepository()
        self.repo = TableMetadataRepository(self.mock_db)
    
    def test_get_all_tables(self):
        """测试获取所有表名"""
        self.mock_db.query_results = [
            {'name': 'users'},
            {'name': 'orders'},
            {'name': 'products'}
        ]
        
        result = self.repo.get_all_tables()
        
        self.assertEqual(len(result), 3)
        self.assertIn('users', result)
    
    def test_get_table_columns(self):
        """测试获取表列信息"""
        self.mock_db.query_results = [
            {'COLUMN_NAME': 'id', 'DATA_TYPE': 'INT'},
            {'COLUMN_NAME': 'name', 'DATA_TYPE': 'VARCHAR'}
        ]
        
        result = self.repo.get_table_columns('users')
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['COLUMN_NAME'], 'id')
    
    def test_get_table_row_count(self):
        """测试获取表记录数"""
        self.mock_db.scalar_result = 1000
        
        result = self.repo.get_table_row_count('users')
        
        self.assertEqual(result, 1000)
    
    def test_table_exists_true(self):
        """测试表存在检查 - 存在"""
        self.mock_db.scalar_result = 1
        
        result = self.repo.table_exists('users')
        
        self.assertTrue(result)
    
    def test_table_exists_false(self):
        """测试表存在检查 - 不存在"""
        self.mock_db.scalar_result = 0
        
        result = self.repo.table_exists('nonexistent')
        
        self.assertFalse(result)
    
    def test_get_database_info(self):
        """测试获取数据库信息"""
        self.mock_db.query_results = [
            {'name': 'users'},
            {'name': 'orders'}
        ]
        self.mock_db.scalar_result = 100
        
        result = self.repo.get_database_info()
        
        self.assertIn('table_count', result)
        self.assertIn('tables', result)
        self.assertEqual(result['table_count'], 2)
    
    def test_readonly_operations(self):
        """测试只读限制"""
        with self.assertRaises(NotImplementedError):
            self.repo.save({'name': 'test'})
        
        with self.assertRaises(NotImplementedError):
            self.repo.delete(1)


class TestRepositoryIntegration(unittest.TestCase):
    """Repository集成测试类"""
    
    def test_repository_chain(self):
        """测试仓库链式调用"""
        mock_db = MockDBRepository()
        
        # 创建多个仓库实例
        query_repo = QueryHistoryRepository(mock_db)
        meta_repo = TableMetadataRepository(mock_db)
        
        # 验证它们共享同一个db_repository
        self.assertEqual(query_repo.db_repository, mock_db)
        self.assertEqual(meta_repo.db_repository, mock_db)


if __name__ == '__main__':
    unittest.main()
