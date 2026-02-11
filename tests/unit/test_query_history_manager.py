#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查询历史管理器单元测试
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from src.business.services.query_history_manager import (
    QueryHistoryManager,
    reset_query_history_manager,
)


class TestQueryHistoryManager(unittest.TestCase):
    """
    查询历史管理器测试类
    """

    def setUp(self):
        """
        测试前准备
        """
        # 创建临时文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        
        # 重置单例
        reset_query_history_manager()
        
        # 创建管理器实例
        self.manager = QueryHistoryManager(history_file=self.temp_file.name, max_history=10)
    
    def tearDown(self):
        """
        测试后清理
        """
        # 删除临时文件
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
        reset_query_history_manager()
    
    def test_add_history(self):
        """
        测试添加历史记录
        """
        # 添加一条历史记录
        self.manager.add_history(
            sql="SELECT * FROM Users",
            execution_time_ms=100,
            row_count=50,
            success=True
        )
        
        # 验证历史记录数量
        self.assertEqual(self.manager.get_history_count(), 1)
        
        # 验证历史记录内容
        history = self.manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['sql'], "SELECT * FROM Users")
        self.assertEqual(history[0]['execution_time_ms'], 100)
        self.assertEqual(history[0]['row_count'], 50)
        self.assertTrue(history[0]['success'])
    
    def test_add_empty_sql(self):
        """
        测试添加空SQL
        """
        # 添加空SQL应该被忽略
        self.manager.add_history(sql="", execution_time_ms=100)
        self.assertEqual(self.manager.get_history_count(), 0)
        
        # 添加只有空格的SQL也应该被忽略
        self.manager.add_history(sql="   ", execution_time_ms=100)
        self.assertEqual(self.manager.get_history_count(), 0)
    
    def test_duplicate_sql(self):
        """
        测试重复SQL处理
        """
        # 添加相同的SQL两次
        self.manager.add_history(sql="SELECT * FROM Users", execution_time_ms=100)
        self.manager.add_history(sql="SELECT * FROM Users", execution_time_ms=200)
        
        # 应该只有一条记录（最新的）
        self.assertEqual(self.manager.get_history_count(), 1)
        self.assertEqual(self.manager.get_history()[0]['execution_time_ms'], 200)
    
    def test_max_history_limit(self):
        """
        测试历史记录数量限制
        """
        # 添加超过限制数量的历史记录
        for i in range(15):
            self.manager.add_history(sql=f"SELECT * FROM Table{i}", execution_time_ms=100)
        
        # 应该只保留最新的10条
        self.assertEqual(self.manager.get_history_count(), 10)
        
        # 验证是最新的10条
        history = self.manager.get_history()
        self.assertEqual(history[0]['sql'], "SELECT * FROM Table14")
        self.assertEqual(history[9]['sql'], "SELECT * FROM Table5")
    
    def test_search_history(self):
        """
        测试搜索历史记录
        """
        # 添加一些历史记录
        self.manager.add_history(sql="SELECT * FROM Users", execution_time_ms=100)
        self.manager.add_history(sql="SELECT * FROM Orders", execution_time_ms=200)
        self.manager.add_history(sql="INSERT INTO Users VALUES (1)", execution_time_ms=50)
        
        # 搜索包含"Users"的记录
        results = self.manager.search_history("Users")
        self.assertEqual(len(results), 2)
        
        # 搜索包含"SELECT"的记录
        results = self.manager.search_history("SELECT")
        self.assertEqual(len(results), 2)
        
        # 搜索不存在的记录
        results = self.manager.search_history("DELETE")
        self.assertEqual(len(results), 0)
    
    def test_search_case_sensitive(self):
        """
        测试区分大小写的搜索
        """
        self.manager.add_history(sql="SELECT * FROM Users", execution_time_ms=100)
        
        # 不区分大小写
        results = self.manager.search_history("select", case_sensitive=False)
        self.assertEqual(len(results), 1)
        
        # 区分大小写
        results = self.manager.search_history("select", case_sensitive=True)
        self.assertEqual(len(results), 0)
        
        results = self.manager.search_history("SELECT", case_sensitive=True)
        self.assertEqual(len(results), 1)
    
    def test_delete_history_entry(self):
        """
        测试删除历史记录
        """
        # 添加三条记录
        self.manager.add_history(sql="SQL1", execution_time_ms=100)
        self.manager.add_history(sql="SQL2", execution_time_ms=200)
        self.manager.add_history(sql="SQL3", execution_time_ms=300)
        
        # 删除第二条（索引1）
        result = self.manager.delete_history_entry(1)
        self.assertTrue(result)
        self.assertEqual(self.manager.get_history_count(), 2)
        
        # 验证删除的是正确的记录
        history = self.manager.get_history()
        self.assertEqual(history[0]['sql'], "SQL3")
        self.assertEqual(history[1]['sql'], "SQL1")
    
    def test_delete_invalid_index(self):
        """
        测试删除无效的索引
        """
        self.manager.add_history(sql="SQL1", execution_time_ms=100)
        
        # 删除负索引
        result = self.manager.delete_history_entry(-1)
        self.assertFalse(result)
        
        # 删除超出范围的索引
        result = self.manager.delete_history_entry(10)
        self.assertFalse(result)
    
    def test_clear_history(self):
        """
        测试清空历史记录
        """
        # 添加一些记录
        self.manager.add_history(sql="SQL1", execution_time_ms=100)
        self.manager.add_history(sql="SQL2", execution_time_ms=200)
        
        # 清空
        self.manager.clear_history()
        
        # 验证
        self.assertEqual(self.manager.get_history_count(), 0)
        self.assertEqual(len(self.manager.get_history()), 0)
    
    def test_persistence(self):
        """
        测试历史记录持久化
        """
        # 添加记录
        self.manager.add_history(sql="SELECT * FROM Users", execution_time_ms=100)
        
        # 创建新的管理器实例（模拟重启）
        new_manager = QueryHistoryManager(history_file=self.temp_file.name)
        
        # 验证记录仍然存在
        self.assertEqual(new_manager.get_history_count(), 1)
        self.assertEqual(new_manager.get_history()[0]['sql'], "SELECT * FROM Users")
    
    def test_get_formatted_history_text(self):
        """
        测试获取格式化的历史记录文本
        """
        entry = {
            'timestamp': '2024-01-01T10:00:00',
            'sql': 'SELECT * FROM Users WHERE Status = "Active"',
            'execution_time_ms': 150.5,
            'row_count': 100,
            'success': True
        }
        
        formatted = self.manager.get_formatted_history_text(entry)
        
        # 验证格式化文本包含关键信息
        self.assertIn('2024-01-01', formatted)
        self.assertIn('成功', formatted)
        self.assertIn('150', formatted)
        self.assertIn('100', formatted)
        self.assertIn('SELECT * FROM Users', formatted)
    
    def test_get_history_with_limit(self):
        """
        测试获取指定数量的历史记录
        """
        # 添加5条记录
        for i in range(5):
            self.manager.add_history(sql=f"SQL{i}", execution_time_ms=100)
        
        # 获取前3条
        history = self.manager.get_history(limit=3)
        self.assertEqual(len(history), 3)
        
        # 获取全部
        history = self.manager.get_history()
        self.assertEqual(len(history), 5)


class TestQueryHistoryManagerSingleton(unittest.TestCase):
    """
    查询历史管理器单例测试
    """
    
    def tearDown(self):
        """
        测试后清理
        """
        reset_query_history_manager()
    
    def test_singleton(self):
        """
        测试单例模式
        """
        from src.business.services.query_history_manager import get_query_history_manager
        
        manager1 = get_query_history_manager()
        manager2 = get_query_history_manager()
        
        # 应该是同一个实例
        self.assertIs(manager1, manager2)


if __name__ == '__main__':
    unittest.main()
